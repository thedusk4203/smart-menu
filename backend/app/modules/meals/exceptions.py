# File: backend/app/modules/meals/exceptions.py
from __future__ import annotations

from app.core.exceptions import NotFoundError


class MealNotFoundError(NotFoundError):
    def __init__(self, meal_id: int) -> None:
        super().__init__(f"Không tìm thấy món ăn id={meal_id}")
