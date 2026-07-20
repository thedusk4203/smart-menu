from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_access_token
from app.modules.identity.domain import UserEntity
from app.modules.identity.repository import SqlUserRepository
from app.shared.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _http_error(
    status_code: int,
    detail: str,
    code: str,
    user_message: str | None = None,
) -> HTTPException:
    """Keep FastAPI dependency compatibility while attaching the structured contract."""
    exc = HTTPException(status_code=status_code, detail=detail)
    exc.code = code  # type: ignore[attr-defined]
    exc.user_message = user_message  # type: ignore[attr-defined]
    return exc


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> UserEntity:
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise _http_error(
            status.HTTP_401_UNAUTHORIZED,
            "Token không hợp lệ hoặc đã hết hạn",
            "AUTH_TOKEN_INVALID",
        )
    repo = SqlUserRepository(session)
    user = repo.get_by_id(int(payload["sub"]))
    if user is None or not user.is_active:
        raise _http_error(
            status.HTTP_401_UNAUTHORIZED,
            "Người dùng không tồn tại hoặc đã bị khoá",
            "AUTH_ACCOUNT_UNAVAILABLE",
            "Tài khoản không còn khả dụng. Hãy liên hệ quản trị viên nếu bạn cần hỗ trợ.",
        )
    return user


def require_admin(current_user: UserEntity = Depends(get_current_user)) -> UserEntity:
    """Tương thích ngược: admin cũ được xem như super admin."""
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        raise _http_error(
            status.HTTP_403_FORBIDDEN,
            "Yêu cầu quyền quản trị (admin)",
            "AUTH_ADMIN_REQUIRED",
        )
    return current_user


def require_super_admin(current_user: UserEntity = Depends(get_current_user)) -> UserEntity:
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        raise _http_error(
            status.HTTP_403_FORBIDDEN,
            "Chỉ quản trị viên hệ thống mới được thực hiện thao tác này",
            "AUTH_SYSTEM_ADMIN_REQUIRED",
        )
    return current_user


def require_data_editor(current_user: UserEntity = Depends(get_current_user)) -> UserEntity:
    if current_user.role not in {
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
        UserRole.DATA_EDITOR,
    }:
        raise _http_error(
            status.HTTP_403_FORBIDDEN,
            "Bạn không có quyền quản lý dữ liệu thực phẩm",
            "AUTH_DATA_EDITOR_REQUIRED",
        )
    return current_user
