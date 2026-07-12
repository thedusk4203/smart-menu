from __future__ import annotations

from app.core.exceptions import ConflictError, NotFoundError


class ProfileNotFoundError(NotFoundError):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"Chưa có hồ sơ cho tài khoản id={user_id}")


class ExclusionAlreadyExistsError(ConflictError):
    def __init__(self, ingredient_id: int) -> None:
        super().__init__(f"Nguyên liệu id={ingredient_id} đã có trong danh sách loại trừ")


class ExclusionNotFoundError(NotFoundError):
    def __init__(self, ingredient_id: int) -> None:
        super().__init__(f"Không tìm thấy mục loại trừ cho nguyên liệu id={ingredient_id}")
