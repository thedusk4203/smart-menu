from __future__ import annotations

from typing import Any

from app.modules.ai.schemas import ExplainPlanRequest, PlanExplanationContent


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

