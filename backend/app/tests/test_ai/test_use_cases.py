from __future__ import annotations

import json
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.modules.ai.exceptions import AIResponseValidationError, AIUnavailableError
from app.modules.ai.ports import AIClientPort, AIMessage
from app.modules.ai.schemas import ChatRequest, ParseMenuRequest, SwapSuggestionRequest
from app.modules.ai.personalization import AuthenticatedAIRequestScope
from app.modules.ai.use_cases import ChatUseCase, ParseMenuRequestUseCase, SuggestSwapUseCase
from app.modules.inventory.repository import SqlInventoryRepository
from app.modules.meal_planning.domain import DishCandidate, MealPlanEntity, PlanRequest
from app.shared.enums import DishType


class _FakeAIClient(AIClientPort):
    def __init__(self, *, text: str = "ok", json_data=None) -> None:
        self.text = text
        self.json_data = json_data if json_data is not None else {}
        self.messages: list[AIMessage] | None = None

    def complete_text(
        self,
        messages: list[AIMessage],
    ) -> str:
        self.messages = messages
        return self.text

    def stream_text(self, messages: list[AIMessage]):
        self.messages = messages
        yield self.text

    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict,
    ) -> dict:
        self.messages = messages
        return self.json_data


class _UnavailableAIClient(_FakeAIClient):
    def complete_json(self, messages, *, schema_name, json_schema):
        raise AIUnavailableError("provider unavailable")


class _FakeConversationStore:
    def __init__(self) -> None:
        self.failed = False

    def start_turn(self, *, user_id, message, conversation_id, mode="general"):
        now = datetime.now(timezone.utc)
        return 9, {
            "id": 11,
            "turn_number": 1,
            "user_content": message,
            "assistant_content": None,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }

    def completed_turns_before(self, *, conversation_id, turn_number):
        return []

    def complete_turn(self, *, conversation_id, turn_id, assistant_content, **metadata):
        now = datetime.now(timezone.utc)
        return {
            "id": turn_id,
            "turn_number": 1,
            "user_content": "Xin chào",
            "assistant_content": assistant_content,
            "status": "completed",
            "created_at": now,
            "updated_at": now,
        }

    def fail_turn(self, **kwargs):
        self.failed = True


def test_chat_stream_returns_deltas_then_completes_turn():
    client = _FakeAIClient(text="Chào bạn")
    events = list(ChatUseCase(client, _FakeConversationStore(), "Prompt chat tùy chỉnh").open_chat_stream(
        ChatRequest(message="Xin chào"), scope=AuthenticatedAIRequestScope(1)
    ).events())

    assert [event["event"] for event in events] == ["start", "delta", "done"]
    assert events[-1]["data"]["reply"] == "Chào bạn"
    assert events[-1]["data"]["conversation_id"] == 9
    assert events[-1]["data"]["turn"]["status"] == "completed"
    assert client.messages is not None
    assert client.messages[0]["role"] == "system"
    assert client.messages[0]["content"] == "Prompt chat tùy chỉnh"


def test_health_chat_uses_personal_context_and_labels_model_fallback():
    class _Preferences:
        def require_enabled(self, scope):
            assert scope.user_id == 7

    class _Context:
        def build(self, scope, *, mode):
            assert scope.user_id == 7
            assert mode == "health_reference"
            return {"age": 30, "goal": "maintain"}

    client = _FakeAIClient(text="Nội dung tham khảo")
    events = list(ChatUseCase(
        client,
        _FakeConversationStore(),
        context_reader=_Context(),
        preferences=_Preferences(),
    ).open_chat_stream(
        ChatRequest(message="Tôi nên ăn thế nào?", mode="health_reference"),
        scope=AuthenticatedAIRequestScope(7),
    ).events())

    done = events[-1]["data"]
    assert done["personalization_used"] is True
    assert done["grounding_mode"] == "model_fallback"
    assert done["citations"] == []
    assert done["reply"].startswith("Thông tin tham khảo từ kiến thức của mô hình")
    assert client.messages is not None
    assert any("[PERSONAL_CONTEXT]" in message["content"] for message in client.messages)


def test_parse_menu_request_validates_structured_output():
    client = _FakeAIClient(
        json_data={
            "days": 7,
            "meals_per_day": 3,
            "budget_limit": 500000,
            "preferred_tags": ["healthy", "ít dầu mỡ"],
            "needs_clarification": False,
            "clarification_question": None,
        }
    )

    result = ParseMenuRequestUseCase(client, "Prompt parse tùy chỉnh").execute(
        ParseMenuRequest(message="7 ngày 3 bữa ngân sách 500k")
    )

    assert result.days == 7
    assert result.meals_per_day == 3
    assert result.budget_limit == 500000
    assert result.preferred_tags == ["healthy", "ít dầu mỡ"]
    assert client.messages is not None
    assert client.messages[0]["content"] == "Prompt parse tùy chỉnh"


def test_parse_menu_uses_active_server_tags_and_reports_unknown_values():
    class _Tags:
        def list_names(self):
            return ["giàu đạm", "lành mạnh"]

    client = _FakeAIClient(json_data={
        "preferred_tags": ["Giàu Đạm", "không tồn tại", "lành mạnh"],
    })
    result = ParseMenuRequestUseCase(client, tags=_Tags()).execute(
        ParseMenuRequest(message="Ưu tiên giàu đạm và lành mạnh")
    )

    assert result.preferred_tags == ["giàu đạm", "lành mạnh"]
    assert result.unresolved_tags == ["không tồn tại"]
    assert client.messages is not None
    assert "giàu đạm" in client.messages[0]["content"]


def test_parse_menu_request_rejects_invalid_ai_shape():
    client = _FakeAIClient(json_data={"days": 99})

    with pytest.raises(AIResponseValidationError):
        ParseMenuRequestUseCase(client).execute(ParseMenuRequest(message="99 ngày"))


def test_parse_menu_request_uses_deterministic_fields_when_llm_only_clarifies():
    client = _FakeAIClient(json_data={
        "needs_clarification": True,
        "clarification_question": "Bạn có thích ăn chay không?",
    })

    result = ParseMenuRequestUseCase(client).execute(
        ParseMenuRequest(message="thực đơn 4 ngày, ngân sách 600k. 2 bữa một ngày")
    )

    assert result.days == 4
    assert result.meals_per_day == 2
    assert result.budget_limit == 600_000
    assert result.needs_clarification is False
    assert result.clarification_question is None


def test_parse_menu_request_deterministic_values_override_llm_values():
    client = _FakeAIClient(json_data={
        "days": 7,
        "meals_per_day": 3,
        "budget_limit": 100_000,
        "preferred_tags": ["giàu đạm"],
    })

    result = ParseMenuRequestUseCase(client).execute(
        ParseMenuRequest(message="4 ngày, 2 bữa, ngân sách 600 nghìn, ưu tiên giàu đạm")
    )

    assert (result.days, result.meals_per_day, result.budget_limit) == (4, 2, 600_000)
    assert result.preferred_tags == ["giàu đạm"]
    assert result.needs_clarification is False


def test_parse_menu_request_falls_back_when_llm_is_unavailable():
    result = ParseMenuRequestUseCase(_UnavailableAIClient()).execute(
        ParseMenuRequest(message="3 ngày, ngân sách 450k, mỗi ngày 2 bữa")
    )

    assert (result.days, result.meals_per_day, result.budget_limit) == (3, 2, 450_000)
    assert result.preferred_tags == []
    assert result.needs_clarification is False


def test_parse_menu_request_falls_back_when_llm_shape_is_invalid_but_numbers_are_valid():
    result = ParseMenuRequestUseCase(_FakeAIClient(json_data={"days": 99})).execute(
        ParseMenuRequest(message="5 ngày, 3 bữa, ngân sách 1 triệu")
    )

    assert (result.days, result.meals_per_day, result.budget_limit) == (5, 3, 1_000_000)
    assert result.needs_clarification is False


def test_parse_menu_request_only_clarifies_when_nothing_is_actionable():
    result = ParseMenuRequestUseCase(_FakeAIClient(json_data={})).execute(
        ParseMenuRequest(message="tạo giúp tôi một thực đơn")
    )

    assert result.needs_clarification is True
    assert result.clarification_question


class _FakeCandidateProvider:
    def __init__(self, target: DishCandidate, replacements: list[DishCandidate]) -> None:
        self.target = target
        self.replacements = replacements

    def load_by_ids(self, dish_ids):
        return {self.target.dish_id: self.target}

    def load_candidates(self, excluded_ingredient_ids):
        return [self.target, *self.replacements]


class _FakeBuildPlanRequest:
    def __init__(self, *, meals_per_day: int = 2) -> None:
        self.meals_per_day = meals_per_day
        self.last_kwargs = None

    def execute(self, user_id, **kwargs):
        self.last_kwargs = kwargs
        return PlanRequest(
            user_id=user_id,
            days=1,
            meals_per_day=self.meals_per_day,
            budget_limit=100_000,
            target_calories=500,
            target_protein_g=20,
            target_fat_g=15,
            target_carb_g=60,
        )


def _dish(dish_id: int, name: str, *, cost: float, calories: float) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        name=name,
        dish_type=DishType.SAVORY,
        cooking_method=None,
        calories=calories,
        protein_g=25,
        fat_g=10,
        carb_g=20,
        estimated_cost=cost,
        tags=("giàu đạm", "Việt Nam"),
    )


def _swap_request(note: str) -> SwapSuggestionRequest:
    return SwapSuggestionRequest(
        day=1,
        meal_type="lunch",
        target_dish_id=1,
        note=note,
        plan={
            "total_cost": 20_000,
            "plan_data": {
                "schema_version": 3,
                "days": [{
                    "day": 1,
                    "meals": [{"meal_type": "lunch", "dishes": [{"dish_id": 1}]}],
                }],
            },
        },
    )


def _swap_use_case(client, system_prompt="Prompt đổi món mặc định trong test"):
    target = _dish(1, "Gà kho", cost=20_000, calories=300)
    replacements = [
        _dish(2, "Gà hấp", cost=18_000, calories=280),
        _dish(3, "Cá kho", cost=19_000, calories=260),
    ]
    return SuggestSwapUseCase(
        client,
        _FakeCandidateProvider(target, replacements),
        _FakeBuildPlanRequest(),
        system_prompt,
        optimizer=SimpleNamespace(solve=lambda *_args, **_kwargs: SimpleNamespace(warnings=[])),
        planner=SimpleNamespace(build_entity=lambda _days, request, start_date, *_args: MealPlanEntity(
            id=None,
            user_id=request.user_id,
            start_date=start_date,
            total_cost=20_000,
            plan_data={"schema_version": 3, "solver_status": "ai_validated_swap"},
        )),
    )


def test_default_swap_note_uses_fast_deterministic_ranking(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.use_cases.constraint_checker.validate_plan",
        lambda *_args, **_kwargs: SimpleNamespace(is_feasible=True),
    )
    client = _FakeAIClient(json_data={"suggestions": [{"dish_id": 999, "reason": "Sai"}]})

    result = _swap_use_case(client).execute(
        _swap_request("Món tương tự, phù hợp ngân sách"), user_id=7
    )

    assert [item.dish_id for item in result] == [3, 2]
    assert client.messages is None
    assert all(item.plan["plan_data"]["solver_status"] == "ai_validated_swap" for item in result)


def test_custom_swap_note_falls_back_when_llm_fails(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.use_cases.constraint_checker.validate_plan",
        lambda *_args, **_kwargs: SimpleNamespace(is_feasible=True),
    )

    result = _swap_use_case(_UnavailableAIClient()).execute(
        _swap_request("Ưu tiên món ít calo"), user_id=7
    )

    assert [item.dish_id for item in result] == [3, 2]
    assert all(item.reason for item in result)


def test_custom_swap_note_sends_target_and_budget_context_to_llm(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.use_cases.constraint_checker.validate_plan",
        lambda *_args, **_kwargs: SimpleNamespace(is_feasible=True),
    )
    client = _FakeAIClient(json_data={
        "suggestions": [{"dish_id": 2, "reason": "Ít calo hơn món hiện tại."}],
    })

    result = _swap_use_case(client).execute(
        _swap_request("Ưu tiên món ít calo"), user_id=7
    )

    assert [item.dish_id for item in result] == [2, 3]
    assert client.messages is not None
    assert client.messages[0]["content"] == "Prompt đổi món mặc định trong test"
    payload = json.loads(client.messages[1]["content"])
    assert payload["target"]["dish_id"] == 1
    assert payload["budget_context"] == {
        "plan_total": 20_000,
        "budget_limit": 100_000,
        "remaining": 80_000,
    }
    assert len(payload["candidates"]) == 2


def test_swap_uses_original_plan_start_date_when_rebuilding_inventory(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.use_cases.constraint_checker.validate_plan",
        lambda *_args, **_kwargs: SimpleNamespace(is_feasible=True),
    )
    builder = _FakeBuildPlanRequest()
    target = _dish(1, "Gà kho", cost=20_000, calories=300)
    use_case = SuggestSwapUseCase(
        _FakeAIClient(),
        _FakeCandidateProvider(target, [_dish(2, "Gà hấp", cost=18_000, calories=280)]),
        builder,
    )
    request = _swap_request("Món tương tự, phù hợp ngân sách")
    request.plan["start_date"] = "2026-07-20"

    use_case.execute(request, user_id=7)

    assert builder.last_kwargs["start_date"] == date(2026, 7, 20)


def test_v3_swap_omits_unpersistable_preview_when_procurement_cannot_rebuild(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.use_cases.constraint_checker.validate_plan",
        lambda *_args, **_kwargs: SimpleNamespace(is_feasible=True),
    )
    monkeypatch.setattr(
        "app.modules.ai.use_cases.ProcurementCpSatOptimizer.solve",
        lambda *_args, **_kwargs: None,
    )
    target = _dish(1, "Gà kho", cost=20_000, calories=300)
    use_case = SuggestSwapUseCase(
        _FakeAIClient(),
        _FakeCandidateProvider(target, [_dish(2, "Gà hấp", cost=18_000, calories=280)]),
        _FakeBuildPlanRequest(meals_per_day=2),
    )
    request = _swap_request("Món tương tự, phù hợp ngân sách")
    request.plan["start_date"] = "2026-07-20"
    request.plan["plan_data"]["schema_version"] = 3

    result = use_case.execute(request, user_id=7)

    assert result == []


def test_swap_rejects_non_v3_plan() -> None:
    request = _swap_request("Món tương tự, phù hợp ngân sách")
    request.plan["plan_data"].pop("schema_version")

    with pytest.raises(AIResponseValidationError, match="schema V3"):
        _swap_use_case(_FakeAIClient()).execute(request, user_id=7)


def test_swap_dependency_builds_request_with_inventory_repository(monkeypatch):
    import app.dependencies as dependencies

    class _PromptStore:
        def __init__(self, _session) -> None:
            pass

        def get_effective(self, _feature: str) -> str:
            return "swap prompt"

    session = SimpleNamespace(execute=lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dependencies, "_get_ai_client", lambda *_args: _FakeAIClient())
    monkeypatch.setattr(dependencies, "SystemPromptStore", _PromptStore)

    use_case = dependencies.get_ai_suggest_swap_use_case(
        s=session, context_s=session, state_s=session, user=SimpleNamespace(id=7)
    )

    inventory = use_case._build_request._inventory
    assert isinstance(inventory, SqlInventoryRepository)
    assert inventory._session is session
