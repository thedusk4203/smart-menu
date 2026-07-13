from __future__ import annotations

import json

import pytest

from app.modules.ai.exceptions import AIResponseValidationError
from app.modules.ai.ports import AIClientPort
from app.modules.ai.schemas import ExplainPlanRequest
from app.modules.ai.use_cases import ExplainPlanUseCase


class ExplanationClient(AIClientPort):
    def __init__(self, response: dict) -> None:
        self.response = response
        self.messages = None
        self.schema_name = None

    def complete_text(self, messages):
        raise AssertionError("explain plan must use structured output")

    def stream_text(self, messages):
        return iter(())

    def complete_json(self, messages, *, schema_name, json_schema):
        self.messages = messages
        self.schema_name = schema_name
        return self.response


def _request() -> ExplainPlanRequest:
    return ExplainPlanRequest(
        total_cost=754_582,
        total_calories=17_499,
        budget_limit=900_000,
        plan_data={
            "meals_per_day": 3,
            "nutrition_target": {"calories": 2556, "protein_g": 120, "fat_g": 70, "carb_g": 300},
            "metrics": {"average_calorie_deviation_pct": 2.2, "protein_shortage_pct": 0},
            "warnings": [],
            "days": [{
                "day": day,
                "day_calories": 2500,
                "day_cost": 107_797,
                "meals": [{
                    "meal_type": "lunch",
                    "name": "Cơm và cá kho",
                    "protein_g": 103,
                    "fat_g": 80,
                    "carb_g": 250,
                    "dishes": [],
                }],
            } for day in range(1, 8)],
        },
    )


def test_explain_plan_requires_actionable_structured_analysis():
    client = ExplanationClient({
        "summary": "Thực đơn 7 ngày bám khá sát mục tiêu năng lượng và vẫn nằm trong ngân sách.",
        "budget_assessment": "Tổng chi phí là 754.582đ, còn 145.418đ so với ngân sách 900.000đ.",
        "nutrition_assessment": "Trung bình khoảng 2.500 kcal/ngày so với mục tiêu 2.556 kcal/ngày.",
        "highlights": ["Độ lệch calo trung bình chỉ 2,2%."],
        "cautions": [],
        "recommendations": ["Xem từng ngày và đổi món nếu muốn tăng độ đa dạng."],
    })

    result = ExplainPlanUseCase(client).execute(_request())

    assert result.summary.startswith("Thực đơn 7 ngày")
    assert "Ngân sách" in result.reply
    assert "Gợi ý tiếp theo" in result.reply
    assert client.schema_name == "smart_menu_plan_explanation"
    payload = json.loads(client.messages[1]["content"])
    assert payload["analysis_facts"]["remaining_budget"] == 145_418
    assert payload["analysis_facts"]["average_calories_per_day"] == 2499.9
    assert "ingredients" not in client.messages[1]["content"]


def test_explain_plan_rejects_generic_acknowledgement_shape():
    client = ExplanationClient({"summary": "Bạn muốn mình làm gì tiếp theo?"})

    with pytest.raises(AIResponseValidationError, match="đúng định dạng"):
        ExplainPlanUseCase(client).execute(_request())


def test_explain_plan_adds_metric_caution_when_model_omits_it():
    request = _request()
    request.plan_data["metrics"]["protein_shortage_pct"] = 14
    client = ExplanationClient({
        "summary": "Thực đơn bám sát mục tiêu calo và vẫn nằm trong giới hạn ngân sách đã chọn.",
        "budget_assessment": "Tổng chi phí thấp hơn ngân sách và vẫn còn khoản dự phòng.",
        "nutrition_assessment": "Calo bám sát mục tiêu nhưng lượng protein chưa đạt mức tham chiếu.",
        "highlights": ["Các macro đều trong khoảng ±15% mục tiêu."],
        "cautions": [],
        "recommendations": ["Chạy lại solver với mục tiêu protein cao hơn."],
    })

    result = ExplainPlanUseCase(client).execute(request)
    payload = json.loads(client.messages[1]["content"])

    assert any("đạm" in item for item in result.cautions)
    assert any("tinh bột" in item for item in result.cautions)
    assert all("±15%" not in item for item in result.highlights)
    assert all("solver" not in item.casefold() for item in result.recommendations)
    assert result.summary == (
        "Thực đơn 7 ngày, gồm 3 bữa/ngày, tổng chi phí 754.582đ "
        "và cung cấp trung bình 2.499,9 kcal/ngày."
    )
    assert payload["analysis_facts"]["macro_comparison"]["protein_g"] == {
        "average_per_day": 103.0,
        "target_per_day": 120.0,
        "deviation_pct": 14.2,
        "direction": "below",
    }
