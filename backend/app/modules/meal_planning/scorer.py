from __future__ import annotations

from dataclasses import dataclass, fields

from app.modules.meal_planning.domain import MealCandidate, PlanRequest


@dataclass(frozen=True)
class ScoringWeights:
    """Trọng số từng tiêu chí mềm SC-01..SC-08 (review D-06/D-15).

    Tổng KHÔNG cần bằng 1 — chỉ ảnh hưởng thang điểm tương đối; calo/protein
    được ưu tiên cao nhất theo tinh thần SRS. frozen -> bất biến, có thể inject
    bộ trọng số khác (ví dụ ưu tiên tiết kiệm) mà không sửa code planner."""
    calorie: float = 3.0     # SC-01
    protein: float = 2.5     # SC-02
    fat_carb: float = 1.5    # SC-03
    variety: float = 2.0     # SC-04
    easy_cook: float = 0.5   # SC-05
    cheap: float = 1.0       # SC-06
    reuse: float = 1.0       # SC-07
    preference: float = 1.5  # SC-08

    def __post_init__(self) -> None:
        for f in fields(self):
            if getattr(self, f.name) < 0:
                raise ValueError(f"Trọng số '{f.name}' không được âm.")


# Bộ trọng số mặc định (bất biến) dùng khi caller không truyền bộ riêng.
DEFAULT_WEIGHTS = ScoringWeights()

# Tag gợi ý "dễ nấu" (SC-05). Khớp không phân biệt hoa thường.
_EASY_TAGS = {"nhanh", "dễ nấu", "de nau", "đơn giản", "don gian"}

# Ngưỡng lệch fat/carb chấp nhận được trước khi bị phạt (SC-03): 20%.
_FAT_CARB_TOLERANCE = 0.20


def _closeness(actual: float, target: float) -> float:
    if target <= 0:
        return 0.5
    return max(0.0, 1.0 - abs(actual - target) / target)


def _calorie_score(candidate: MealCandidate, per_meal_calories: float) -> float:
    """SC-01: gần mục tiêu calo (chia đều cho số bữa/ngày)."""
    return _closeness(candidate.total_calories, per_meal_calories)


def _protein_score(candidate: MealCandidate, per_meal_protein: float) -> float:
    """SC-02: gần mục tiêu protein."""
    return _closeness(candidate.total_protein_g, per_meal_protein)


def _fat_carb_score(
    candidate: MealCandidate, per_meal_fat: float, per_meal_carb: float
) -> float:
    """SC-03: cân đối fat/carb — phạt nếu lệch quá _FAT_CARB_TOLERANCE."""
    def sub(actual: float, target: float) -> float:
        if target <= 0:
            return 0.5
        deviation = abs(actual - target) / target
        if deviation <= _FAT_CARB_TOLERANCE:
            return 1.0
        # Quá ngưỡng: giảm dần phần vượt.
        return max(0.0, 1.0 - (deviation - _FAT_CARB_TOLERANCE))

    return (sub(candidate.total_fat_g, per_meal_fat) + sub(candidate.total_carb_g, per_meal_carb)) / 2


def _variety_score(candidate: MealCandidate, usage_count: dict[int, int]) -> float:
    """SC-04: đa dạng món — phạt tăng dần theo số lần món đã xuất hiện."""
    used = usage_count.get(candidate.meal_id, 0)
    # 0 lần -> 1.0; mỗi lần lặp giảm một nửa (1, 0.5, 0.25, ...).
    return 1.0 / (2 ** used)


def _easy_cook_score(candidate: MealCandidate) -> float:
    """SC-05: dễ nấu — bonus nếu có tag thuộc _EASY_TAGS."""
    tags_lower = {str(t).strip().lower() for t in candidate.tags}
    return 1.0 if tags_lower & _EASY_TAGS else 0.0


def _cheap_score(candidate: MealCandidate, max_cost: float) -> float:
    """SC-06: tiết kiệm — món càng rẻ (so với món đắt nhất trong pool) càng cao."""
    if max_cost <= 0:
        return 0.5
    return max(0.0, 1.0 - candidate.estimated_cost / max_cost)


def _reuse_score(candidate: MealCandidate, day_ingredient_ids: set[int]) -> float:
    """SC-07: tái sử dụng nguyên liệu — bonus nếu dùng lại nguyên liệu đã có
    trong các bữa khác cùng ngày (giảm lãng phí)."""
    if not candidate.ingredient_ids or not day_ingredient_ids:
        return 0.0
    shared = sum(1 for iid in candidate.ingredient_ids if iid in day_ingredient_ids)
    return min(1.0, shared / len(candidate.ingredient_ids))


def _preference_score(candidate: MealCandidate, preferred_tags: list[str]) -> float:
    """SC-08: phù hợp sở thích — tỉ lệ tag ưa thích mà món khớp."""
    if not preferred_tags:
        return 0.0
    wanted = {t.strip().lower() for t in preferred_tags}
    tags_lower = {str(t).strip().lower() for t in candidate.tags}
    if not wanted:
        return 0.0
    matched = len(wanted & tags_lower)
    return matched / len(wanted)


def score_candidate(
    candidate: MealCandidate,
    request: PlanRequest,
    *,
    usage_count: dict[int, int],
    day_ingredient_ids: set[int],
    max_cost: float,
    weights: ScoringWeights = DEFAULT_WEIGHTS,
) -> float:
    mpd = max(request.meals_per_day, 1)
    per_meal_cal = request.target_calories / mpd
    per_meal_protein = request.target_protein_g / mpd
    per_meal_fat = request.target_fat_g / mpd
    per_meal_carb = request.target_carb_g / mpd

    return (
        weights.calorie * _calorie_score(candidate, per_meal_cal)
        + weights.protein * _protein_score(candidate, per_meal_protein)
        + weights.fat_carb * _fat_carb_score(candidate, per_meal_fat, per_meal_carb)
        + weights.variety * _variety_score(candidate, usage_count)
        + weights.easy_cook * _easy_cook_score(candidate)
        + weights.cheap * _cheap_score(candidate, max_cost)
        + weights.reuse * _reuse_score(candidate, day_ingredient_ids)
        + weights.preference * _preference_score(candidate, request.preferred_tags)
    )
