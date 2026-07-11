from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DeterministicMenuFields:
    days: int | None = None
    meals_per_day: int | None = None
    budget_limit: float | None = None

    @property
    def has_value(self) -> bool:
        return any(value is not None for value in (self.days, self.meals_per_day, self.budget_limit))


_DAYS_RE = re.compile(r"(?<!\d)(\d{1,2})\s*(?:ngày|day)\b", re.IGNORECASE)
_MEALS_RE = re.compile(r"(?<!\d)(\d{1,2})\s*bữa\b", re.IGNORECASE)
_MEALS_REVERSED_RE = re.compile(r"mỗi\s*ngày\s*(\d{1,2})\s*bữa\b", re.IGNORECASE)
_BUDGET_RE = re.compile(
    r"(?:ngân\s*sách|budget)\s*(?:(?:là|khoảng|tầm)\s*)?[:=]?\s*"
    r"(\d+(?:[.,]\d+)*)\s*(k|nghìn|ngàn|triệu|tr|m|đ|vnd)?\b",
    re.IGNORECASE,
)


def extract_menu_fields(message: str) -> DeterministicMenuFields:
    text = " ".join(message.casefold().split())
    days = _bounded_int(_first_group(_DAYS_RE, text), minimum=1, maximum=7)
    meals_match = _MEALS_RE.search(text) or _MEALS_REVERSED_RE.search(text)
    meals_per_day = _bounded_int(meals_match.group(1) if meals_match else None, minimum=2, maximum=3)

    budget_limit: float | None = None
    budget_match = _BUDGET_RE.search(text)
    if budget_match:
        budget_limit = _parse_budget(budget_match.group(1), budget_match.group(2))

    return DeterministicMenuFields(
        days=days,
        meals_per_day=meals_per_day,
        budget_limit=budget_limit,
    )


def _first_group(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1) if match else None


def _bounded_int(raw: str | None, *, minimum: int, maximum: int) -> int | None:
    if raw is None:
        return None
    value = int(raw)
    return value if minimum <= value <= maximum else None


def _parse_budget(raw: str, unit: str | None) -> float | None:
    normalized_unit = (unit or "").casefold()
    multiplier = 1.0
    if normalized_unit in {"k", "nghìn", "ngàn"}:
        multiplier = 1_000.0
    elif normalized_unit in {"triệu", "tr", "m"}:
        multiplier = 1_000_000.0

    number_text = raw.strip()
    if multiplier > 1:
        # Với hậu tố k/triệu, dấu phẩy hoặc một dấu chấm là phần thập phân.
        if "," in number_text:
            number_text = number_text.replace(".", "").replace(",", ".")
        elif number_text.count(".") > 1:
            number_text = number_text.replace(".", "")
    else:
        # Không có hệ số: 600.000 và 1.200.000 là cách viết phân tách hàng nghìn.
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", number_text):
            number_text = number_text.replace(".", "").replace(",", "")
        elif "," in number_text:
            number_text = number_text.replace(".", "").replace(",", ".")

    try:
        value = float(number_text) * multiplier
    except ValueError:
        return None
    return value if value > 0 else None
