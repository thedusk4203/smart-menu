# File: backend/app/modules/ai/use_cases.py
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
    ChatResponse,
    ConversationChatResponse,
    ConversationDetail,
    ConversationSummary,
    ConversationTurn,
    ExplainPlanRequest,
    ParsedMenuRequest,
    ParseMenuRequest,
    SwapSuggestionRequest,
    SwapSuggestion,
)
from app.modules.ai.conversation_store import ConversationStore
from app.modules.meal_planning import constraint_checker
from app.modules.meal_planning.domain import ComposedMeal
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

    def execute(self, data: ExplainPlanRequest) -> ChatResponse:
        payload = {
            "plan_data": data.plan_data,
            "total_cost": data.total_cost,
            "total_calories": data.total_calories,
            "budget_limit": data.budget_limit,
        }
        reply = self._client.complete_text(
            [
                {"role": "system", "content": EXPLAIN_PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": _compact_json(payload, limit=12000)},
            ],
        )
        return ChatResponse(reply=reply)


class SuggestSwapUseCase:
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
        candidate_payload = [
            {"dish_id": item.dish_id, "name": item.name, "tags": list(item.tags),
             "calories": round(item.calories, 1), "cost": round(item.estimated_cost, 0)}
            for item in pool[:30]
        ]
        if not candidate_payload:
            return []
        raw = self._client.complete_json(
            [{"role": "system", "content": SWAP_SYSTEM_PROMPT},
             {"role": "user", "content": _compact_json({"note": data.note, "candidates": candidate_payload})}],
            schema_name="smart_menu_swap_rank", json_schema={
                "type": "object", "properties": {"suggestions": {"type": "array", "maxItems": 10,
                    "items": {"type": "object", "properties": {
                        "dish_id": {"type": "integer"}, "reason": {"type": "string"}},
                        "required": ["dish_id", "reason"], "additionalProperties": False}}},
                "required": ["suggestions"], "additionalProperties": False,
            },
        )
        allowed = {item.dish_id: item for item in pool[:30]}
        results: list[SwapSuggestion] = []
        seen: set[int] = set()
        for ranked in raw.get("suggestions", []):
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
