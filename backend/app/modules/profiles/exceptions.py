from __future__ import annotations

from app.core.exceptions import ConflictError, NotFoundError


class ProfileNotFoundError(NotFoundError):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            f"Chưa có hồ sơ cho tài khoản id={user_id}",
            code="PROFILE_NOT_FOUND",
            user_message="Bạn chưa có hồ sơ dinh dưỡng. Hãy bổ sung thông tin để tiếp tục.",
            details={"user_id": user_id},
        )


class ExclusionAlreadyExistsError(ConflictError):
    def __init__(self, ingredient_id: int) -> None:
        super().__init__(
            f"Nguyên liệu id={ingredient_id} đã có trong danh sách loại trừ",
            code="EXCLUSION_ALREADY_EXISTS",
            user_message="Nguyên liệu này đã có trong danh sách loại trừ.",
            details={"ingredient_id": ingredient_id},
        )


class ExclusionNotFoundError(NotFoundError):
    def __init__(self, ingredient_id: int) -> None:
        super().__init__(
            f"Không tìm thấy mục loại trừ cho nguyên liệu id={ingredient_id}",
            code="EXCLUSION_NOT_FOUND",
            user_message="Nguyên liệu này không còn trong danh sách loại trừ.",
            details={"ingredient_id": ingredient_id},
        )
