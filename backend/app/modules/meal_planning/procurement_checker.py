"""Independent invariants for procurement-aware plan results."""
from __future__ import annotations

import math

from app.modules.meal_planning.domain import PlanRequest, ValidationResult
from app.modules.meal_planning.optimizer_contracts import V3OptimizationResult


def validate_v3(result: V3OptimizationResult, request: PlanRequest) -> ValidationResult:
    violations: list[str] = []
    procurement = result.procurement_plan
    purchase_items = procurement.get("purchase_items", [])
    inventory_items = procurement.get("inventory_items", [])
    calculated_cost = 0.0
    for item in purchase_items:
        increment = float(item["purchase_increment"])
        quantity = float(item["purchase_quantity"])
        blocks = int(item["block_count"])
        if increment <= 0 or blocks <= 0 or abs(quantity - increment * blocks) > 1e-6:
            violations.append(f"PROC-BLOCK: {item['name']} không đúng bội số mua.")
        expected_cost = math.ceil(increment * float(item["price_per_default_unit"]) - 1e-9) * blocks
        if abs(float(item["purchase_cost"]) - expected_cost) > 1e-6:
            violations.append(f"PROC-COST: {item['name']} sai giá block.")
        calculated_cost += float(item["purchase_cost"])
        allocated = 0.0
        same_day_allocated = 0.0
        for allocation in item.get("allocations", []):
            quantity_allocated = float(allocation["quantity"])
            allocated += quantity_allocated
            if int(allocation["day"]) == int(item["purchase_day"]):
                same_day_allocated += quantity_allocated
            if int(allocation["day"]) < int(item["purchase_day"]):
                violations.append(f"PROC-DATE: {item['name']} được dùng trước ngày mua.")
            if int(allocation["day"]) > int(allocation["expiry_day"]):
                violations.append(f"PROC-EXPIRY: {item['name']} được dùng sau hạn.")
        if same_day_allocated <= 1e-8:
            violations.append(
                f"PROC-JIT: {item['name']} được mua ngày {item['purchase_day']} nhưng không dùng trong ngày."
            )
        remaining = float(item.get("remaining_quantity", 0))
        if abs(quantity - allocated - remaining) > 0.011:
            violations.append(f"PROC-BALANCE: {item['name']} không cân bằng tồn kho.")
        if abs(
            remaining
            - float(item.get("expired_waste_quantity", 0))
            - float(item.get("carryover_quantity", 0))
        ) > 0.011:
            violations.append(f"PROC-ENDING: {item['name']} phân loại tồn cuối sai.")

    for item in inventory_items:
        starting = float(item.get("starting_quantity", 0))
        allocated = sum(float(value["quantity"]) for value in item.get("allocations", []))
        remaining = float(item.get("remaining_quantity", 0))
        if abs(starting - allocated - remaining) > 0.011:
            violations.append(f"INV-BALANCE: {item['name']} không cân bằng tồn đầu kỳ.")
        for allocation in item.get("allocations", []):
            if int(allocation["day"]) > int(allocation["expiry_day"]):
                violations.append(f"INV-EXPIRY: {item['name']} được dùng sau hạn.")

    summary_cost = float(procurement.get("cost_summary", {}).get("purchase_cost", 0))
    if abs(round(calculated_cost) - summary_cost) > 1:
        violations.append("PROC-TOTAL: Tổng tiền mua không khớp các purchase item.")
    if request.budget_limit is not None and summary_cost > request.budget_limit + 1e-6:
        violations.append(
            f"HC-BUDGET: tiền mua {summary_cost:.0f}đ vượt ngân sách {request.budget_limit:.0f}đ."
        )

    ledger = procurement.get("daily_ledger", [])
    if procurement.get("ledger_version") != 2 or len(ledger) != request.days:
        violations.append("LEDGER-SCHEMA: ledger V2 thiếu hoặc sai số ngày.")
    for day in ledger:
        for row in day.get("items", []):
            if (
                row.get("source_kind") == "purchase"
                and float(row["purchase_quantity"]) > 1e-8
                and float(row["usage_quantity"]) <= 1e-8
            ):
                violations.append(
                    f"LEDGER-JIT: {row['name']} ngày {day.get('day')} mua nhưng không dùng."
                )
            expected = (
                float(row["opening_quantity"])
                + float(row["purchase_quantity"])
                - float(row["usage_quantity"])
                - float(row["expired_quantity"])
            )
            if abs(expected - float(row["closing_quantity"])) > 0.011:
                violations.append(
                    f"LEDGER-BALANCE: {row['name']} ngày {day.get('day')} không cân bằng."
                )

    if len(result.final_nutrition) != request.days:
        violations.append("NUTRITION-DAYS: số ngày dinh dưỡng không khớp request.")
    else:
        calories = []
        proteins = []
        for day_index, totals in enumerate(result.final_nutrition, start=1):
            day_calories = float(totals["calories"])
            calories.append(day_calories)
            proteins.append(float(totals["protein_g"]))
            if not request.target_calories * 0.80 - 1e-6 <= day_calories <= request.target_calories * 1.20 + 1e-6:
                violations.append(f"HC-CALORIE-DAY: ngày {day_index} ngoài biên ±20%.")
        average_calories = sum(calories) / request.days
        if not request.target_calories * 0.90 - 1e-6 <= average_calories <= request.target_calories * 1.10 + 1e-6:
            violations.append("HC-CALORIE-AVERAGE: trung bình plan ngoài biên ±10%.")
        if sum(proteins) / request.days < request.target_protein_g * 0.90 - 1e-6:
            violations.append("HC-PROTEIN: protein trung bình dưới 90% target.")

    adjustment_keys: set[tuple[int, str, int, int]] = set()
    for adjustment in result.adjustments:
        key = (
            int(adjustment["day"]),
            str(adjustment["slot"]),
            int(adjustment["dish_id"]),
            int(adjustment["ingredient_id"]),
        )
        if key in adjustment_keys:
            violations.append("PROC-EXTRA-DUPLICATE: adjustment bị lặp.")
        adjustment_keys.add(key)
        if float(adjustment["extra_quantity"]) <= 0:
            violations.append("PROC-EXTRA: lượng tăng phải dương.")
        if abs(
            float(adjustment["actual_quantity"])
            - float(adjustment["base_quantity"])
            - float(adjustment["extra_quantity"])
        ) > 1e-6:
            violations.append("PROC-EXTRA-BALANCE: base + extra không khớp actual.")

    if violations:
        return ValidationResult(status="infeasible", hard_violations=violations)
    return ValidationResult(status="valid")
