from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from pydantic import ValidationError

from app.core.exceptions import AppException
from app.modules.ai.exceptions import AIResponseValidationError, AIUnavailableError
from app.modules.ai.ports import AIClientPort
from app.modules.ai.request_parser import DeterministicMenuFields, extract_menu_fields
from app.modules.ai.prompts import (
    CHAT_SYSTEM_PROMPT,
    EXPLAIN_PLAN_SYSTEM_PROMPT,
    PARSE_MENU_SYSTEM_PROMPT,
    SWAP_SYSTEM_PROMPT,
)
from app.modules.ai.schemas import (
    ChatRequest,
    ConversationChatResponse,
    ConversationDetail,
    ConversationSummary,
    ConversationTurn,
    ExplainPlanResponse,
    ExplainPlanRequest,
    PlanExplanationContent,
    ParsedMenuRequest,
    ParseMenuRequest,
    SwapSuggestionRequest,
    SwapSuggestion,
)
from app.modules.ai.conversation_store import ConversationStore
from app.modules.meal_planning import constraint_checker
from app.modules.meal_planning.domain import ComposedMeal, DishCandidate
from app.modules.meal_planning.planner import DishPlanner
from app.modules.meal_planning.ports import DishCandidateProviderPort
from app.modules.meal_planning.use_cases import BuildPlanRequestUseCase
from app.shared.enums import MealType


class ChatUseCase:
    def __init__(self, client: AIClientPort, conversations: ConversationStore) -> None:
        self._client = client
        self._conversations = conversations

    def open_chat_stream(self, data: ChatRequest, *, user_id: int) -> "ChatStream":
        conversation_id, turn = self._conversations.start_turn(
            user_id=user_id,
            message=data.message,
            conversation_id=data.conversation_id,
        )
        history = self._conversations.completed_turns_before(
            conversation_id=conversation_id,
            turn_number=int(turn["turn_number"]),
        )
        user_content = data.message
        if data.context is not None:
            user_content += "\n\nNgữ cảnh ứng dụng:\n" + _compact_json(data.context)

        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        messages.extend(_recent_chat_history(history))
        messages.append({"role": "user", "content": user_content})
        return ChatStream(
            client=self._client,
            conversations=self._conversations,
            conversation_id=conversation_id,
            turn=turn,
            messages=messages,
        )

    def open_retry_stream(
        self, *, conversation_id: int, turn_id: int, user_id: int
    ) -> "ChatStream":
        turn = self._conversations.prepare_retry(
            conversation_id=conversation_id,
            turn_id=turn_id,
            user_id=user_id,
        )
        history = self._conversations.completed_turns_before(
            conversation_id=conversation_id,
            turn_number=int(turn["turn_number"]),
        )
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        messages.extend(_recent_chat_history(history))
        messages.append({"role": "user", "content": str(turn["user_content"])})
        return ChatStream(
            client=self._client,
            conversations=self._conversations,
            conversation_id=conversation_id,
            turn=turn,
            messages=messages,
        )


@dataclass
class ChatStream:
    """Một turn đã được ghi pending, sẵn sàng phát SSE và hoàn tất sau stream."""

    client: AIClientPort
    conversations: ConversationStore
    conversation_id: int
    turn: dict[str, Any]
    messages: list[dict[str, str]]

    def events(self) -> Iterator[dict[str, Any]]:
        settled = False

        def fail() -> None:
            nonlocal settled
            if settled:
                return
            self.conversations.fail_turn(
                conversation_id=self.conversation_id,
                turn_id=int(self.turn["id"]),
            )
            settled = True

        try:
            yield {
                "event": "start",
                "data": {
                    "conversation_id": self.conversation_id,
                    "turn": ConversationTurn.model_validate(self.turn).model_dump(mode="json"),
                },
            }
            chunks: list[str] = []
            for chunk in self.client.stream_text(self.messages):
                chunks.append(chunk)
                yield {"event": "delta", "data": {"content": chunk}}

            reply = "".join(chunks).strip()
            if not reply:
                raise AIResponseValidationError("AI provider không trả về nội dung trả lời.")
            completed = self.conversations.complete_turn(
                conversation_id=self.conversation_id,
                turn_id=int(self.turn["id"]),
                assistant_content=reply,
            )
            settled = True
            response = ConversationChatResponse(
                reply=reply,
                conversation_id=self.conversation_id,
                turn=ConversationTurn.model_validate(completed),
            )
            yield {"event": "done", "data": response.model_dump(mode="json")}
        except GeneratorExit:
            fail()
            raise
        except Exception as exc:
            fail()
            detail = exc.detail if isinstance(exc, AppException) else "Menuto chưa thể hoàn tất câu trả lời."
            yield {
                "event": "error",
                "data": {
                    "detail": detail,
                    "conversation_id": self.conversation_id,
                    "turn_id": int(self.turn["id"]),
                    "retryable": True,
                },
            }
        finally:
            fail()


class ConversationHistoryUseCase:
    def __init__(self, conversations: ConversationStore) -> None:
        self._conversations = conversations

    def list(self, *, user_id: int) -> list[ConversationSummary]:
        return [
            ConversationSummary.model_validate(item)
            for item in self._conversations.list_for_user(user_id)
        ]

    def get(self, *, conversation_id: int, user_id: int) -> ConversationDetail:
        return ConversationDetail.model_validate(
            self._conversations.get_for_user(conversation_id, user_id)
        )

    def delete(self, *, conversation_id: int, user_id: int) -> None:
        self._conversations.delete_for_user(conversation_id, user_id)


class ParseMenuRequestUseCase:
    def __init__(self, client: AIClientPort) -> None:
        self._client = client

    def execute(self, data: ParseMenuRequest) -> ParsedMenuRequest:
        deterministic = extract_menu_fields(data.message)
        try:
            raw = self._client.complete_json(
                [
                    {"role": "system", "content": PARSE_MENU_SYSTEM_PROMPT},
                    {"role": "user", "content": data.message},
                ],
                schema_name="smart_menu_plan_request",
                json_schema=ParsedMenuRequest.model_json_schema(),
            )
        except (AIUnavailableError, AIResponseValidationError):
            if deterministic.has_value:
                return self._merge(deterministic, None)
            raise
        try:
            llm_result = ParsedMenuRequest.model_validate(raw)
        except ValidationError as exc:
            if deterministic.has_value:
                return self._merge(deterministic, None)
            raise AIResponseValidationError("AI parse request không khớp schema.") from exc
        return self._merge(deterministic, llm_result)

    @staticmethod
    def _merge(
        deterministic: DeterministicMenuFields,
        llm_result: ParsedMenuRequest | None,
    ) -> ParsedMenuRequest:
        llm = llm_result or ParsedMenuRequest()
        tags = [tag for tag in llm.preferred_tags if tag.strip()]
        days = deterministic.days if deterministic.days is not None else llm.days
        meals_per_day = (
            deterministic.meals_per_day
            if deterministic.meals_per_day is not None
            else llm.meals_per_day
        )
        budget_limit = (
            deterministic.budget_limit
            if deterministic.budget_limit is not None
            else llm.budget_limit
        )
        actionable = any(value is not None for value in (days, meals_per_day, budget_limit)) or bool(tags)
        return ParsedMenuRequest(
            days=days,
            meals_per_day=meals_per_day,
            budget_limit=budget_limit,
            preferred_tags=tags,
            needs_clarification=not actionable,
            clarification_question=(
                None
                if actionable
                else llm.clarification_question or "Bạn muốn tạo thực đơn trong bao nhiêu ngày?"
            ),
        )


class ExplainPlanUseCase:
    def __init__(self, client: AIClientPort) -> None:
        self._client = client

    def execute(self, data: ExplainPlanRequest) -> ExplainPlanResponse:
        payload = _plan_explanation_payload(data)
        raw = self._client.complete_json(
            [
                {"role": "system", "content": EXPLAIN_PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(
                    payload, ensure_ascii=False, default=str, separators=(",", ":")
                )},
            ],
            schema_name="smart_menu_plan_explanation",
            json_schema=PlanExplanationContent.model_json_schema(),
        )
        try:
            content = PlanExplanationContent.model_validate(raw)
        except ValidationError as exc:
            raise AIResponseValidationError(
                "AI chưa tạo được bản phân tích thực đơn đúng định dạng. Hãy thử lại."
            ) from exc
        content = _ground_plan_explanation(content, payload["analysis_facts"])
        return ExplainPlanResponse(
            **content.model_dump(),
            reply=_format_plan_explanation(content),
        )


class SuggestSwapUseCase:
    _DEFAULT_NOTE = "món tương tự, phù hợp ngân sách"

    def __init__(self, client: AIClientPort, candidates: DishCandidateProviderPort,
                 build_request: BuildPlanRequestUseCase) -> None:
        self._client = client
        self._candidates = candidates
        self._build_request = build_request
        self._planner = DishPlanner()

    def execute(self, data: SwapSuggestionRequest, *, user_id: int) -> list[SwapSuggestion]:
        plan_data = data.plan.get("plan_data")
        if not isinstance(plan_data, dict) or not isinstance(plan_data.get("days"), list):
            raise AIResponseValidationError("Plan đổi món không đúng định dạng.")
        snapshot = plan_data.get("request_snapshot") or {}
        request = self._build_request.execute(
            user_id,
            days=int(snapshot.get("days") or len(plan_data["days"])),
            meals_per_day=int(snapshot.get("meals_per_day") or plan_data.get("meals_per_day") or 3),
            budget_limit=snapshot.get("budget_limit", data.plan.get("budget_limit")),
            preferred_tags=list(snapshot.get("preferred_tags") or []),
        )

        ids = [
            int(dish["dish_id"])
            for day in plan_data["days"] for meal in day.get("meals", [])
            for dish in meal.get("dishes", []) if dish.get("dish_id")
        ]
        by_id = self._candidates.load_by_ids(ids)
        if data.target_dish_id not in by_id:
            raise AIResponseValidationError("Món cần đổi không còn planner-ready.")
        target = by_id[data.target_dish_id]
        composed = self._compose(plan_data, by_id)
        target_day = composed[data.day - 1]
        target_index = next(
            (index for index, meal in enumerate(target_day) if meal.slot.value == data.meal_type), None
        )
        if target_index is None or data.target_dish_id not in [d.dish_id for d in target_day[target_index].dishes]:
            raise AIResponseValidationError("Không tìm thấy món cần đổi trong ngày/bữa đã chọn.")

        occupied = {dish.dish_id for dish in target_day[target_index].dishes}
        pool = [candidate for candidate in self._candidates.load_candidates(request.excluded_ingredient_ids)
                if candidate.dish_type == target.dish_type and candidate.dish_id not in occupied]
        terms = {term.casefold() for term in (data.note or "").replace(",", " ").split()}
        pool.sort(key=lambda item: (
            -sum(1 for tag in item.tags if any(term in tag.casefold() for term in terms)),
            abs(item.estimated_cost - target.estimated_cost),
            abs(item.calories - target.calories), item.dish_id,
        ))
        # The deterministic order is also the safe fallback. Keep the LLM
        # shortlist small: local reasoning models otherwise tend to calculate
        # scores for every dish and can exhaust the provider timeout.
        shortlist = pool[:12]
        candidate_payload = [
            {"dish_id": item.dish_id, "name": item.name, "tags": list(item.tags),
             "calories": round(item.calories, 1), "cost": round(item.estimated_cost, 0)}
            for item in shortlist
        ]
        if not candidate_payload:
            return []
        ranked_rows: list[dict[str, Any]] = []
        if self._needs_llm_ranking(data.note):
            budget_limit = request.budget_limit
            current_total = float(data.plan.get("total_cost") or 0)
            try:
                raw = self._client.complete_json(
                    [{"role": "system", "content": SWAP_SYSTEM_PROMPT},
                     {"role": "user", "content": _compact_json({
                         "note": data.note,
                         "target": {
                             "dish_id": target.dish_id,
                             "name": target.name,
                             "tags": list(target.tags),
                             "calories": round(target.calories, 1),
                             "cost": round(target.estimated_cost, 0),
                         },
                         "budget_context": {
                             "plan_total": round(current_total, 0),
                             "budget_limit": round(budget_limit, 0) if budget_limit else None,
                             "remaining": round(budget_limit - current_total, 0)
                             if budget_limit else None,
                         },
                         "candidates": candidate_payload,
                     })}],
                    schema_name="smart_menu_swap_rank", json_schema={
                        "type": "object", "properties": {"suggestions": {
                            "type": "array", "maxItems": 5,
                            "items": {"type": "object", "properties": {
                                "dish_id": {"type": "integer"},
                                "reason": {"type": "string"}},
                                "required": ["dish_id", "reason"],
                                "additionalProperties": False}}},
                        "required": ["suggestions"], "additionalProperties": False,
                    },
                )
                suggestions = raw.get("suggestions")
                if isinstance(suggestions, list):
                    ranked_rows = [row for row in suggestions if isinstance(row, dict)]
            except (AIUnavailableError, AIResponseValidationError):
                # Swapping is still safe without the LLM: candidates were
                # deterministically ranked and every resulting plan is checked
                # by Constraint Checker below.
                ranked_rows = []

        allowed = {item.dish_id: item for item in pool}
        # Invalid/duplicate LLM rows are ignored. Append every deterministic
        # candidate so an incomplete model response cannot yield an empty UI.
        ranked_rows.extend(
            {"dish_id": item.dish_id, "reason": self._fallback_reason(item, target)}
            for item in pool
        )
        results: list[SwapSuggestion] = []
        seen: set[int] = set()
        for ranked in ranked_rows:
            replacement = allowed.get(ranked.get("dish_id"))
            if replacement is None or replacement.dish_id in seen:
                continue
            seen.add(replacement.dish_id)
            next_days = [list(day) for day in composed]
            old_meal = next_days[data.day - 1][target_index]
            next_days[data.day - 1][target_index] = ComposedMeal(
                slot=old_meal.slot,
                dishes=tuple(replacement if dish.dish_id == data.target_dish_id else dish for dish in old_meal.dishes),
            )
            validation = constraint_checker.validate_plan(next_days, request)
            if not validation.is_feasible:
                continue
            entity = self._planner.build_entity(
                next_days, request, None, [],
                SimpleNamespace(solver_time_ms=0, nutrition_score=0, solver_status="ai_validated_swap"),
            )
            results.append(SwapSuggestion(
                dish_id=replacement.dish_id, name=replacement.name,
                reason=str(ranked.get("reason") or "Phù hợp với yêu cầu của bạn."),
                plan={"user_id": entity.user_id, "name": entity.name,
                      "start_date": None, "end_date": None, "budget_limit": entity.budget_limit,
                      "total_cost": entity.total_cost, "total_calories": entity.total_calories,
                      "plan_data": entity.plan_data},
            ))
            if len(results) == 3:
                break
        return results

    @classmethod
    def _needs_llm_ranking(cls, note: str | None) -> bool:
        normalized = " ".join((note or "").casefold().strip().rstrip(".").split())
        return bool(normalized and normalized != cls._DEFAULT_NOTE)

    @staticmethod
    def _fallback_reason(replacement: DishCandidate, target: DishCandidate) -> str:
        shared_tags = [tag for tag in replacement.tags if tag in target.tags]
        price_delta = replacement.estimated_cost - target.estimated_cost
        if price_delta < -0.5:
            return f"Cùng nhóm món và tiết kiệm khoảng {abs(price_delta):,.0f}đ so với món hiện tại."
        if price_delta > 0.5:
            return f"Cùng nhóm món, chi phí chênh khoảng {price_delta:,.0f}đ so với món hiện tại."
        if shared_tags:
            return f"Tương tự món hiện tại theo tiêu chí {shared_tags[0]}."
        return "Tương tự món hiện tại và phù hợp với cấu trúc bữa ăn."

    @staticmethod
    def _compose(plan_data: dict[str, Any], by_id: dict) -> list[list[ComposedMeal]]:
        days: list[list[ComposedMeal]] = []
        for day in plan_data["days"]:
            meals: list[ComposedMeal] = []
            for meal in day.get("meals", []):
                dish_ids = [int(item["dish_id"]) for item in meal.get("dishes", [])]
                if any(dish_id not in by_id for dish_id in dish_ids):
                    raise AIResponseValidationError("Plan chứa món không còn planner-ready.")
                meals.append(ComposedMeal(slot=MealType(meal["meal_type"]),
                                          dishes=tuple(by_id[dish_id] for dish_id in dish_ids)))
            days.append(meals)
        return days


def _compact_json(data: Any, *, limit: int = 5000) -> str:
    text = json.dumps(data, ensure_ascii=False, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "... [truncated]"


def _plan_explanation_payload(data: ExplainPlanRequest) -> dict[str, Any]:
    plan_data = data.plan_data
    raw_days = plan_data.get("days") if isinstance(plan_data.get("days"), list) else []
    day_count = len(raw_days)
    total_cost = float(data.total_cost) if data.total_cost is not None else None
    total_calories = float(data.total_calories) if data.total_calories is not None else None
    budget_limit = float(data.budget_limit) if data.budget_limit is not None else None

    compact_days: list[dict[str, Any]] = []
    for day in raw_days:
        if not isinstance(day, dict):
            continue
        meals: list[dict[str, Any]] = []
        for meal in day.get("meals") or []:
            if not isinstance(meal, dict):
                continue
            meals.append({
                "meal_type": meal.get("meal_type"),
                "name": meal.get("name"),
                "calories": meal.get("calories"),
                "protein_g": meal.get("protein_g"),
                "fat_g": meal.get("fat_g"),
                "carb_g": meal.get("carb_g"),
                "cost": meal.get("cost"),
                "dishes": [
                    {"name": dish.get("name"), "tags": dish.get("tags") or []}
                    for dish in meal.get("dishes") or []
                    if isinstance(dish, dict)
                ],
            })
        compact_days.append({
            "day": day.get("day"),
            "date": day.get("date"),
            "day_calories": day.get("day_calories"),
            "day_cost": day.get("day_cost"),
            "meals": meals,
        })

    remaining_budget = (
        round(budget_limit - total_cost, 0)
        if budget_limit is not None and total_cost is not None
        else None
    )
    budget_usage_pct = (
        round(total_cost / budget_limit * 100, 1)
        if budget_limit and total_cost is not None
        else None
    )
    average_calories = (
        round(total_calories / day_count, 1)
        if total_calories is not None and day_count
        else None
    )
    nutrition_target = plan_data.get("nutrition_target") or {}
    macro_comparison = _macro_comparison(raw_days, nutrition_target, day_count)
    calorie_comparison = _metric_comparison(
        average_calories,
        nutrition_target.get("calories"),
    )
    return {
        "task": "Phân tích ngay thực đơn này theo đúng schema; không hỏi lại người dùng.",
        "analysis_facts": {
            "days": day_count,
            "meals_per_day": plan_data.get("meals_per_day"),
            "total_cost": total_cost,
            "budget_limit": budget_limit,
            "remaining_budget": remaining_budget,
            "budget_usage_pct": budget_usage_pct,
            "total_calories": total_calories,
            "average_calories_per_day": average_calories,
            "nutrition_target": nutrition_target,
            "calorie_comparison": calorie_comparison,
            "macro_comparison": macro_comparison,
            "metrics": plan_data.get("metrics") or {},
            "warnings": plan_data.get("warnings") or [],
        },
        "plan_days": compact_days,
    }


def _macro_comparison(
    days: list[Any], nutrition_target: dict[str, Any], day_count: int
) -> dict[str, dict[str, float | str | None]]:
    result: dict[str, dict[str, float | str | None]] = {}
    for field in ("protein_g", "fat_g", "carb_g"):
        total = 0.0
        has_value = False
        for day in days:
            if not isinstance(day, dict):
                continue
            for meal in day.get("meals") or []:
                if not isinstance(meal, dict) or meal.get(field) is None:
                    continue
                total += float(meal[field])
                has_value = True
        raw_target = nutrition_target.get(field)
        target = float(raw_target) if raw_target is not None else None
        average = round(total / day_count, 1) if has_value and day_count else None
        if average is None or not target:
            result[field] = {
                "average_per_day": average,
                "target_per_day": target,
                "deviation_pct": None,
                "direction": None,
            }
            continue
        delta = average - target
        result[field] = {
            "average_per_day": average,
            "target_per_day": target,
            "deviation_pct": round(abs(delta) / target * 100, 1),
            "direction": "above" if delta > 0 else "below" if delta < 0 else "on_target",
        }
    return result


def _metric_comparison(
    average: float | None, raw_target: Any
) -> dict[str, float | str | None]:
    target = float(raw_target) if raw_target is not None else None
    if average is None or not target:
        return {
            "average_per_day": average,
            "target_per_day": target,
            "deviation_pct": None,
            "direction": None,
        }
    delta = average - target
    return {
        "average_per_day": average,
        "target_per_day": target,
        "deviation_pct": round(abs(delta) / target * 100, 1),
        "direction": "above" if delta > 0 else "below" if delta < 0 else "on_target",
    }


def _ground_plan_explanation(
    content: PlanExplanationContent, facts: dict[str, Any]
) -> PlanExplanationContent:
    """Keep prose useful while making every quantitative judgment deterministic."""
    days = int(facts.get("days") or 0)
    meals_per_day = int(facts.get("meals_per_day") or 0)
    total_cost = _optional_float(facts.get("total_cost"))
    average_calories = _optional_float(facts.get("average_calories_per_day"))

    summary_parts = [f"Thực đơn {days} ngày"]
    if meals_per_day:
        summary_parts.append(f"gồm {meals_per_day} bữa/ngày")
    if total_cost is not None:
        summary_parts.append(f"tổng chi phí {_format_vi_number(total_cost)}đ")
    if average_calories is not None:
        summary_parts.append(
            f"cung cấp trung bình {_format_vi_number(average_calories)} kcal/ngày"
        )
    summary = _join_summary_parts(summary_parts)

    budget_assessment = _budget_assessment(facts)
    nutrition_assessment = _nutrition_assessment(facts)
    highlights = _grounded_highlights(facts)
    cautions = _grounded_cautions(facts)
    recommendations = _grounded_recommendations(content.recommendations, facts)

    return content.model_copy(update={
        "summary": summary,
        "budget_assessment": budget_assessment,
        "nutrition_assessment": nutrition_assessment,
        "highlights": highlights,
        "cautions": cautions,
        "recommendations": recommendations,
    })


def _budget_assessment(facts: dict[str, Any]) -> str:
    total_cost = _optional_float(facts.get("total_cost"))
    budget_limit = _optional_float(facts.get("budget_limit"))
    remaining = _optional_float(facts.get("remaining_budget"))
    usage = _optional_float(facts.get("budget_usage_pct"))
    if total_cost is None:
        return "Thực đơn chưa có đủ dữ liệu chi phí để so sánh ngân sách."
    if budget_limit is None:
        return (
            f"Tổng chi phí là {_format_vi_number(total_cost)}đ; "
            "chưa có giới hạn ngân sách để đối chiếu."
        )
    if remaining is not None and remaining >= 0:
        usage_text = (
            f", tương đương {_format_vi_number(usage)}%" if usage is not None else ""
        )
        return (
            f"Tổng chi phí {_format_vi_number(total_cost)}đ{usage_text} của ngân sách "
            f"{_format_vi_number(budget_limit)}đ; còn {_format_vi_number(remaining)}đ dự phòng."
        )
    overspend = abs(remaining or (budget_limit - total_cost))
    return (
        f"Tổng chi phí {_format_vi_number(total_cost)}đ vượt "
        f"{_format_vi_number(overspend)}đ so với ngân sách "
        f"{_format_vi_number(budget_limit)}đ."
    )


def _nutrition_assessment(facts: dict[str, Any]) -> str:
    statements: list[str] = []
    calorie = facts.get("calorie_comparison")
    if isinstance(calorie, dict) and calorie.get("average_per_day") is not None:
        average = _format_vi_number(calorie["average_per_day"])
        target = calorie.get("target_per_day")
        deviation = calorie.get("deviation_pct")
        direction = calorie.get("direction")
        if target and deviation is not None:
            relation = {
                "above": "cao hơn",
                "below": "thấp hơn",
                "on_target": "đúng bằng",
            }.get(str(direction), "lệch")
            statements.append(
                f"Calo trung bình {average} kcal/ngày, {relation} "
                f"{_format_vi_number(deviation)}% so với mục tiêu "
                f"{_format_vi_number(target)} kcal/ngày"
            )
        else:
            statements.append(f"Calo trung bình {average} kcal/ngày")

    macro_labels = {
        "protein_g": "Đạm",
        "fat_g": "Chất béo",
        "carb_g": "Tinh bột",
    }
    comparison = facts.get("macro_comparison")
    if isinstance(comparison, dict):
        for field, label in macro_labels.items():
            item = comparison.get(field)
            if not isinstance(item, dict) or item.get("average_per_day") is None:
                continue
            statement = f"{label} {_format_vi_number(item['average_per_day'])}g/ngày"
            if item.get("target_per_day") and item.get("deviation_pct") is not None:
                direction = "cao hơn" if item.get("direction") == "above" else "thấp hơn"
                if item.get("direction") == "on_target":
                    direction = "đúng bằng"
                statement += (
                    f", {direction} {_format_vi_number(item['deviation_pct'])}% so với mục tiêu"
                )
            statements.append(statement)
    return "; ".join(statements) + "." if statements else (
        "Thực đơn chưa có đủ dữ liệu dinh dưỡng để so sánh với mục tiêu."
    )


def _grounded_highlights(facts: dict[str, Any]) -> list[str]:
    highlights: list[str] = []
    remaining = _optional_float(facts.get("remaining_budget"))
    if remaining is not None and remaining >= 0:
        highlights.append(
            f"Tổng chi phí nằm trong ngân sách, còn {_format_vi_number(remaining)}đ dự phòng."
        )

    calorie = facts.get("calorie_comparison")
    if isinstance(calorie, dict):
        deviation = _optional_float(calorie.get("deviation_pct"))
        if deviation is not None and deviation < 10:
            highlights.append(
                f"Calo trung bình bám sát mục tiêu, chỉ lệch {_format_vi_number(deviation)}%."
            )

    macro_labels = {"protein_g": "Đạm", "fat_g": "Chất béo", "carb_g": "Tinh bột"}
    comparison = facts.get("macro_comparison")
    if isinstance(comparison, dict):
        for field, label in macro_labels.items():
            item = comparison.get(field)
            deviation = _optional_float(item.get("deviation_pct")) if isinstance(item, dict) else None
            if deviation is not None and deviation < 5 and len(highlights) < 3:
                highlights.append(
                    f"{label} trung bình gần mục tiêu, lệch {_format_vi_number(deviation)}%."
                )
    if not highlights:
        highlights.append(
            f"Thực đơn đã có dữ liệu chi tiết cho {int(facts.get('days') or 0)} ngày."
        )
    return highlights[:3]


def _grounded_cautions(facts: dict[str, Any]) -> list[str]:
    cautions: list[str] = []
    warnings = facts.get("warnings") if isinstance(facts.get("warnings"), list) else []
    for warning in warnings:
        message = warning.get("message") if isinstance(warning, dict) else str(warning)
        message = " ".join(str(message or "").split())
        if "solver hết thời gian" in message.casefold():
            message = "Thực đơn hợp lệ, nhưng có thể chưa phải phương án tối ưu nhất."
        if message and message not in cautions and len(cautions) < 3:
            cautions.append(message)

    metrics = facts.get("metrics") if isinstance(facts.get("metrics"), dict) else {}
    protein_shortage = float(metrics.get("protein_shortage_pct") or 0)
    if protein_shortage >= 5:
        message = (
            "Lượng đạm trung bình đang thấp hơn mục tiêu khoảng "
            f"{_format_vi_number(protein_shortage)}%."
        )
        if len(cautions) >= 3:
            cautions[-1] = message
        else:
            cautions.append(message)

    average_calorie_deviation = float(metrics.get("average_calorie_deviation_pct") or 0)
    if average_calorie_deviation >= 10 and len(cautions) < 3:
        cautions.append(
            "Mức calo theo ngày lệch mục tiêu trung bình khoảng "
            f"{_format_vi_number(average_calorie_deviation)}%."
        )

    macro_labels = {"fat_g": "chất béo", "carb_g": "tinh bột"}
    comparison = facts.get("macro_comparison")
    if isinstance(comparison, dict):
        for field, label in macro_labels.items():
            item = comparison.get(field)
            if not isinstance(item, dict):
                continue
            deviation = float(item.get("deviation_pct") or 0)
            if deviation < 15 or len(cautions) >= 3:
                continue
            direction = "cao hơn" if item.get("direction") == "above" else "thấp hơn"
            cautions.append(
                f"Lượng {label} trung bình đang {direction} mục tiêu khoảng "
                f"{_format_vi_number(deviation)}%."
            )
    return cautions[:3]


def _grounded_recommendations(
    model_recommendations: list[str], facts: dict[str, Any]
) -> list[str]:
    recommendations: list[str] = []
    covered: set[str] = set()
    metrics = facts.get("metrics") if isinstance(facts.get("metrics"), dict) else {}
    protein_shortage = float(metrics.get("protein_shortage_pct") or 0)
    if protein_shortage >= 5:
        recommendations.append(
            "Khi đổi món, ưu tiên món chính giàu đạm hơn và kiểm tra lại tổng calo của ngày."
        )
        covered.add("protein")

    comparison = facts.get("macro_comparison")
    if isinstance(comparison, dict):
        for field, label in (("fat_g", "chất béo"), ("carb_g", "tinh bột")):
            item = comparison.get(field)
            deviation = _optional_float(item.get("deviation_pct")) if isinstance(item, dict) else None
            if deviation is None or deviation < 15 or len(recommendations) >= 3:
                continue
            if item.get("direction") == "above":
                recommendations.append(
                    f"Giảm khẩu phần hoặc đổi sang món ít {label} hơn ở bữa có mức cao nhất."
                )
            else:
                recommendations.append(
                    f"Bổ sung món có {label} phù hợp khi đổi món để tiến gần mục tiêu hơn."
                )
            covered.add(field)

    blocked_terms = ("solver", "mô hình", "hệ thống", "chạy lại")
    for recommendation in model_recommendations:
        normalized = " ".join(recommendation.split())
        lowered = normalized.casefold()
        if not normalized or "?" in normalized or any(term in lowered for term in blocked_terms):
            continue
        if "protein" in covered and ("protein" in lowered or "đạm" in lowered):
            continue
        if "carb_g" in covered and ("carb" in lowered or "tinh bột" in lowered):
            continue
        if "fat_g" in covered and ("fat" in lowered or "chất béo" in lowered):
            continue
        if normalized not in recommendations:
            recommendations.append(normalized)
        if len(recommendations) == 3:
            break

    if not recommendations:
        recommendations.append(
            "Có thể giữ thực đơn này và kiểm tra lại chi phí, calo cùng macro sau mỗi lần đổi món."
        )
    return recommendations[:3]


def _optional_float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _format_vi_number(value: Any) -> str:
    number = float(value)
    decimals = 0 if number.is_integer() else 1
    formatted = f"{number:,.{decimals}f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def _join_summary_parts(parts: list[str]) -> str:
    if len(parts) == 1:
        return parts[0] + "."
    return ", ".join(parts[:-1]) + " và " + parts[-1] + "."


def _format_plan_explanation(content: PlanExplanationContent) -> str:
    lines = [
        content.summary,
        "",
        "Ngân sách",
        content.budget_assessment,
        "",
        "Dinh dưỡng",
        content.nutrition_assessment,
        "",
        "Điểm phù hợp",
        *(f"• {item}" for item in content.highlights),
    ]
    if content.cautions:
        lines.extend(["", "Điểm cần lưu ý", *(f"• {item}" for item in content.cautions)])
    lines.extend(["", "Gợi ý tiếp theo", *(f"• {item}" for item in content.recommendations)])
    return "\n".join(lines)


def _recent_chat_history(turns: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Chọn các cặp user/assistant mới nhất trong giới hạn provider-safe."""
    selected: list[dict[str, Any]] = []
    total_chars = 0
    for turn in reversed(turns):
        user_content = str(turn.get("user_content") or "")
        assistant_content = str(turn.get("assistant_content") or "")
        if not user_content or not assistant_content:
            continue
        pair_chars = len(user_content) + len(assistant_content)
        if len(selected) >= 5 or total_chars + pair_chars > 12_000:
            break
        selected.append(turn)
        total_chars += pair_chars

    messages: list[dict[str, str]] = []
    for turn in reversed(selected):
        messages.append({"role": "user", "content": str(turn["user_content"])})
        messages.append(
            {"role": "assistant", "content": str(turn["assistant_content"])}
        )
    return messages
