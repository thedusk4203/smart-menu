# File: backend/app/tests/test_meal_planning/test_scorer.py
# Unit test cho scorer (soft constraints SC-01..SC-08) + ScoringWeights.

import dataclasses

import pytest

from app.modules.meal_planning import scorer
from app.modules.meal_planning.scorer import DEFAULT_WEIGHTS, ScoringWeights
from app.tests.test_meal_planning.factories import make_candidate, make_request


def _score(candidate, request, *, usage_count=None, day_ingredient_ids=None,
           max_cost=20000.0, weights=DEFAULT_WEIGHTS):
    return scorer.score_candidate(
        candidate,
        request,
        usage_count=usage_count or {},
        day_ingredient_ids=day_ingredient_ids or set(),
        max_cost=max_cost,
        weights=weights,
    )


# ---------------------------------------------------------------------------
# ScoringWeights (D-06 / D-15)
# ---------------------------------------------------------------------------

class TestScoringWeights:
    def test_default_values(self):
        w = ScoringWeights()
        assert w.calorie == 3.0
        assert w.protein == 2.5

    def test_is_frozen(self):
        w = ScoringWeights()
        with pytest.raises(dataclasses.FrozenInstanceError):
            w.calorie = 9.0  # type: ignore[misc]

    def test_negative_weight_rejected(self):
        with pytest.raises(ValueError, match="không được âm"):
            ScoringWeights(calorie=-1.0)

    def test_custom_weights_allowed(self):
        w = ScoringWeights(calorie=1.0, protein=1.0, fat_carb=1.0, variety=1.0,
                           easy_cook=1.0, cheap=1.0, reuse=1.0, preference=1.0)
        assert w.cheap == 1.0


# ---------------------------------------------------------------------------
# Từng tiêu chí ảnh hưởng điểm như kỳ vọng
# ---------------------------------------------------------------------------

class TestScoringBehaviour:
    def test_closer_calorie_scores_higher(self):
        # per_meal_cal = 2000 / 2 = 1000.
        req = make_request(meals_per_day=2, target_calories=2000.0,
                           target_protein_g=120.0, target_fat_g=60.0, target_carb_g=250.0)
        perfect = make_candidate(1, calories=1000.0, protein=60.0, fat=30.0, carb=125.0)
        far = make_candidate(2, calories=500.0, protein=60.0, fat=30.0, carb=125.0)
        assert _score(perfect, req) > _score(far, req)

    def test_repeated_meal_scores_lower(self):
        req = make_request()
        c = make_candidate(1)
        fresh = _score(c, req, usage_count={})
        repeated = _score(c, req, usage_count={1: 2})
        assert repeated < fresh

    def test_cheaper_scores_higher(self):
        req = make_request()
        cheap = make_candidate(1, cost=5000.0)
        pricey = make_candidate(2, cost=15000.0)
        assert _score(cheap, req, max_cost=15000.0) > _score(pricey, req, max_cost=15000.0)

    def test_preferred_tag_bonus(self):
        req = make_request(preferred_tags=["gà"])
        with_tag = make_candidate(1, tags=["gà"])
        without = make_candidate(2, tags=["bò"])
        assert _score(with_tag, req) > _score(without, req)

    def test_reuse_ingredient_bonus(self):
        req = make_request()
        c = make_candidate(1, ingredient_ids=[10, 11])
        reused = _score(c, req, day_ingredient_ids={10, 11})
        fresh = _score(c, req, day_ingredient_ids=set())
        assert reused > fresh


# ---------------------------------------------------------------------------
# Trọng số cấu hình được THỰC SỰ đổi thứ hạng (D-06)
# ---------------------------------------------------------------------------

class TestConfigurableWeights:
    def test_cheap_heavy_weights_flip_ranking(self):
        req = make_request(meals_per_day=2, target_calories=2000.0)
        # A: dinh dưỡng hoàn hảo nhưng đắt. B: dinh dưỡng kém nhưng rẻ.
        good_pricey = make_candidate(1, calories=1000.0, protein=60.0, cost=20000.0)
        poor_cheap = make_candidate(2, calories=200.0, protein=5.0, cost=1000.0)

        # Mặc định ưu tiên dinh dưỡng -> A thắng.
        assert _score(good_pricey, req, max_cost=20000.0) > _score(poor_cheap, req, max_cost=20000.0)

        # Trọng số ưu tiên tiết kiệm tuyệt đối -> B thắng.
        cheap_first = ScoringWeights(
            calorie=0.0, protein=0.0, fat_carb=0.0, variety=0.0,
            easy_cook=0.0, cheap=10.0, reuse=0.0, preference=0.0,
        )
        assert _score(poor_cheap, req, max_cost=20000.0, weights=cheap_first) > \
            _score(good_pricey, req, max_cost=20000.0, weights=cheap_first)
