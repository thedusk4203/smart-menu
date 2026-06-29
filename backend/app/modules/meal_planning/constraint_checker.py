from __future__ import annotations

from app.modules.meal_planning.domain import MealCandidate, PlanRequest, ValidationResult

# Thứ tự slot bữa ăn theo số bữa/ngày. hỗ trợ 2 hoặc 3 bữa.
_SLOTS_BY_MEALS_PER_DAY: dict[int, list[str]] = {
    2: ["breakfast", "dinner"],
    3: ["breakfast", "lunch", "dinner"],
}


def slots_for(meals_per_day: int) -> list[str]:
    """Trả về danh sách loại bữa (meal_type) cho mỗi ngày theo số bữa/ngày.

    Mặc định 3 bữa nếu giá trị không nằm trong bảng (an toàn cho MVP)."""
    return _SLOTS_BY_MEALS_PER_DAY.get(meals_per_day, _SLOTS_BY_MEALS_PER_DAY[3])

# HC theo từng candidate (dùng khi lọc trước lúc ghép)

def has_excluded_ingredient(candidate: MealCandidate, excluded: set[int]) -> bool:
    """HC-02 (dị ứng) + HC-03 (thực phẩm loại trừ): True nếu món chứa bất kỳ
    nguyên liệu nào trong danh sách loại trừ.

    `excluded` là một set đã dựng SẴN (review D-07) — caller dựng một lần rồi
    truyền vào, tránh tạo lại set cho mỗi candidate × slot khi lọc."""
    if not excluded:
        return False
    return any(iid in excluded for iid in candidate.ingredient_ids)


def has_valid_data(candidate: MealCandidate) -> bool:
    """HC-07: món phải đủ dữ liệu giá + dinh dưỡng để tính toán.

    Một món không có nguyên liệu (estimated_cost == 0 và calories == 0) không
    thể dùng để lập thực đơn có nghĩa, nên bị loại."""
    return candidate.estimated_cost > 0 and candidate.total_calories > 0


def matches_slot(candidate: MealCandidate, slot: str) -> bool:
    """HC-06: loại bữa của món phải khớp slot (breakfast/lunch/dinner)."""
    return candidate.meal_type == slot


def candidate_is_eligible(
    candidate: MealCandidate, slot: str, excluded: set[int]
) -> bool:
    """Gộp các hard constraint áp dụng được ở mức từng món + slot
    (HC-02, HC-03, HC-06, HC-07). `excluded` là set đã dựng sẵn (D-07)."""
    return (
        has_valid_data(candidate)
        and matches_slot(candidate, slot)
        and not has_excluded_ingredient(candidate, excluded)
    )

# Validate toàn bộ thực đơn (sau khi planner đã ghép xong)

def validate_plan(
    days: list[list[MealCandidate]],
    request: PlanRequest,
) -> ValidationResult:
    """Kiểm tra một thực đơn đã ghép (list theo ngày, mỗi ngày là list món)
    với toàn bộ ràng buộc cứng (SRS §5.4).

    Trả về ValidationResult với status:
      - "infeasible" nếu vi phạm bất kỳ ràng buộc cứng nào
      - "valid"      nếu đạt mọi ràng buộc cứng

    (Cảnh báo mềm được scorer/planner gắn thêm; ở đây chỉ xét hard constraint.)
    """
    violations: list[str] = []
    expected_slots = slots_for(request.meals_per_day)
    excluded = set(request.excluded_ingredient_ids)

    # HC-04: đúng số ngày
    if len(days) != request.days:
        violations.append(
            f"HC-04: thực đơn có {len(days)} ngày, yêu cầu {request.days} ngày."
        )

    total_cost = 0.0
    for day_index, day in enumerate(days, start=1):
        # HC-05: đúng số bữa mỗi ngày
        if len(day) != request.meals_per_day:
            violations.append(
                f"HC-05: ngày {day_index} có {len(day)} bữa, yêu cầu {request.meals_per_day} bữa."
            )

        for slot_index, meal in enumerate(day):
            total_cost += meal.estimated_cost

            # HC-06: loại bữa khớp slot (chỉ so khi slot tồn tại trong layout)
            if slot_index < len(expected_slots) and meal.meal_type != expected_slots[slot_index]:
                violations.append(
                    f"HC-06: ngày {day_index} slot {slot_index + 1} là '{meal.meal_type}', "
                    f"cần '{expected_slots[slot_index]}'."
                )

            # HC-02/HC-03: không chứa nguyên liệu loại trừ
            if excluded and any(iid in excluded for iid in meal.ingredient_ids):
                violations.append(
                    f"HC-02/03: ngày {day_index} món '{meal.name}' chứa nguyên liệu bị loại trừ."
                )

            # HC-07: dữ liệu hợp lệ
            if not has_valid_data(meal):
                violations.append(
                    f"HC-07: ngày {day_index} món '{meal.name}' thiếu dữ liệu giá/dinh dưỡng."
                )

    # HC-01: tổng chi phí không vượt ngân sách. budget_limit=None nghĩa là
    # KHÔNG giới hạn -> bỏ qua kiểm tra (review D-01).
    if request.budget_limit is not None and total_cost > request.budget_limit:
        violations.append(
            f"HC-01: tổng chi phí {total_cost:.0f}đ vượt ngân sách {request.budget_limit:.0f}đ."
        )

    if violations:
        return ValidationResult(status="infeasible", hard_violations=violations)
    return ValidationResult(status="valid")
