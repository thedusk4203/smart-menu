from __future__ import annotations

import pytest

from app.modules.ai.request_parser import extract_menu_fields


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("thực đơn 4 ngày", 4),
        ("lập thực đơn trong 7 ngày", 7),
        ("thực đơn 8 ngày", None),
    ],
)
def test_extract_days(message, expected):
    assert extract_menu_fields(message).days == expected


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("2 bữa/ngày", 2),
        ("2 bữa một ngày", 2),
        ("mỗi ngày 3 bữa", 3),
        ("4 bữa mỗi ngày", None),
    ],
)
def test_extract_meals_per_day(message, expected):
    assert extract_menu_fields(message).meals_per_day == expected


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("ngân sách 600k", 600_000),
        ("ngân sách 600 nghìn", 600_000),
        ("ngân sách 600 ngàn", 600_000),
        ("ngân sách 600.000đ", 600_000),
        ("ngân sách 0,6 triệu", 600_000),
        ("budget 1,2tr", 1_200_000),
    ],
)
def test_extract_budget(message, expected):
    assert extract_menu_fields(message).budget_limit == expected


def test_extract_screenshot_request():
    result = extract_menu_fields("thực đơn 4 ngày, ngân sách 600k. 2 bữa một ngày")

    assert result.days == 4
    assert result.meals_per_day == 2
    assert result.budget_limit == 600_000
