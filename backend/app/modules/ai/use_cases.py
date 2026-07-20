from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.core.exceptions import AppException
from app.modules.ai.exceptions import AIResponseValidationError, AIUnavailableError
from app.modules.ai.message_formatting import (
    compact_json as _compact_json,
    recent_chat_history as _recent_chat_history,
)
from app.modules.ai.plan_explanation import (
    _format_plan_explanation,
    _ground_plan_explanation,
    _plan_explanation_payload,
)
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
from app.modules.meal_planning.optimizer_v3 import ProcurementCpSatOptimizer
from app.modules.meal_planning.planner import DishPlanner
from app.modules.meal_planning.ports import DishCandidateProviderPort
from app.modules.meal_planning.use_cases import BuildPlanRequestUseCase
from app.shared.enums import MealType


class ChatUseCase:
    def __init__(self, client: AIClientPort, conversations: ConversationStore,
                 system_prompt: str = CHAT_SYSTEM_PROMPT) -> None:
        self._client = client
        self._conversations = conversations
        self._system_prompt = system_prompt

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

        messages = [{"role": "system", "content": self._system_prompt}]
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
        messages = [{"role": "system", "content": self._system_prompt}]
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
            if isinstance(exc, AppException):
                detail = exc.detail
                error = {
                    "code": exc.code,
                    "message": exc.user_message,
                    "details": exc.details,
                }
            else:
                detail = "Menuto chưa thể hoàn tất câu trả lời."
                error = {
                    "code": "AI_STREAM_FAILED",
                    "message": "Menuto chưa thể hoàn tất câu trả lời. Hãy thử lại.",
                    "details": {},
                }
            yield {
                "event": "error",
                "data": {
                    "detail": detail,
                    "error": error,
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
    def __init__(self, client: AIClientPort,
                 system_prompt: str = PARSE_MENU_SYSTEM_PROMPT) -> None:
        self._client = client
        self._system_prompt = system_prompt

    def execute(self, data: ParseMenuRequest) -> ParsedMenuRequest:
        deterministic = extract_menu_fields(data.message)
        try:
            raw = self._client.complete_json(
                [
                    {"role": "system", "content": self._system_prompt},
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
    def __init__(self, client: AIClientPort,
                 system_prompt: str = EXPLAIN_PLAN_SYSTEM_PROMPT) -> None:
        self._client = client
        self._system_prompt = system_prompt

    def execute(self, data: ExplainPlanRequest) -> ExplainPlanResponse:
        payload = _plan_explanation_payload(data)
        raw = self._client.complete_json(
            [
                {"role": "system", "content": self._system_prompt},
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
                 build_request: BuildPlanRequestUseCase,
                 system_prompt: str = SWAP_SYSTEM_PROMPT,
                 optimizer: ProcurementCpSatOptimizer | None = None,
                 planner: DishPlanner | None = None) -> None:
        self._client = client
        self._candidates = candidates
        self._build_request = build_request
        self._system_prompt = system_prompt
        self._optimizer = optimizer or ProcurementCpSatOptimizer()
        self._planner = planner or DishPlanner()

    def execute(self, data: SwapSuggestionRequest, *, user_id: int) -> list[SwapSuggestion]:
        plan_data = data.plan.get("plan_data")
        if not isinstance(plan_data, dict) or not isinstance(plan_data.get("days"), list):
            raise AIResponseValidationError("Plan đổi món không đúng định dạng.")
        if int(plan_data.get("schema_version") or 0) != 3:
            raise AIResponseValidationError("Chỉ hỗ trợ đổi món cho meal plan schema V3.")
        snapshot = plan_data.get("request_snapshot") or {}
        raw_start_date = data.plan.get("start_date") or snapshot.get("start_date")
        plan_start_date: date | None = None
        if raw_start_date:
            try:
                plan_start_date = date.fromisoformat(str(raw_start_date))
            except ValueError as error:
                raise AIResponseValidationError(
                    "Ngày bắt đầu của thực đơn đổi món không hợp lệ."
                ) from error
        request = self._build_request.execute(
            user_id,
            days=int(snapshot.get("days") or len(plan_data["days"])),
            meals_per_day=int(snapshot.get("meals_per_day") or plan_data.get("meals_per_day") or 3),
            budget_limit=snapshot.get("budget_limit", data.plan.get("budget_limit")),
            preferred_tags=list(snapshot.get("preferred_tags") or []),
            start_date=plan_start_date,
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
                    [{"role": "system", "content": self._system_prompt},
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
            preview: dict[str, Any]
            solved = None
            if request.meals_per_day in (2, 3):
                fixed_candidates = list({
                    dish.dish_id: dish
                    for day in next_days for meal in day for dish in meal.dishes
                }.values())
                solved = self._optimizer.solve(
                    request, fixed_candidates, fixed_days=next_days
                )
            if solved is None:
                continue
            entity = self._planner.build_entity(
                next_days, request, plan_start_date, solved.warnings, solved
            )
            preview = {
                "user_id": entity.user_id, "name": entity.name,
                "start_date": entity.start_date, "end_date": entity.end_date,
                "budget_limit": entity.budget_limit, "total_cost": entity.total_cost,
                "total_calories": entity.total_calories, "plan_data": entity.plan_data,
            }
            results.append(SwapSuggestion(
                dish_id=replacement.dish_id, name=replacement.name,
                reason=str(ranked.get("reason") or "Phù hợp với yêu cầu của bạn."),
                plan=preview,
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
