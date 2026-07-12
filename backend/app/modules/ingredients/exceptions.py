from __future__ import annotations

from app.core.exceptions import ConflictError, NotFoundError


class IngredientNotFoundError(NotFoundError):
    def __init__(self, ingredient_id: int) -> None:
        super().__init__(f"Không tìm thấy nguyên liệu id={ingredient_id}")


class IngredientNameExistsError(ConflictError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Tên nguyên liệu '{name}' đã tồn tại")
