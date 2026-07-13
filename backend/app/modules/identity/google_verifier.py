from __future__ import annotations

from google.auth.transport import requests
from google.auth.exceptions import GoogleAuthError
from google.oauth2 import id_token

from app.core.config import settings
from app.modules.identity.exceptions import (
    GoogleAuthenticationError,
    GoogleAuthenticationNotConfiguredError,
)
from app.modules.identity.use_cases import GoogleIdentity


class GoogleTokenVerifier:
    """Xác minh Google ID token trước khi identity module dùng email trong token."""

    def verify(self, credential: str) -> GoogleIdentity:
        if not settings.google_client_id:
            raise GoogleAuthenticationNotConfiguredError("Đăng nhập Google chưa được cấu hình")
        try:
            payload = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                settings.google_client_id,
            )
        except (GoogleAuthError, ValueError) as exc:
            raise GoogleAuthenticationError("Google token không hợp lệ hoặc đã hết hạn") from exc

        email = payload.get("email")
        if not payload.get("email_verified") or not isinstance(email, str):
            raise GoogleAuthenticationError("Google chưa xác minh địa chỉ email này")
        email = email.strip().lower()
        if not email.endswith("@gmail.com"):
            raise GoogleAuthenticationError("Chỉ hỗ trợ tài khoản Gmail")

        name = payload.get("name")
        return GoogleIdentity(email=email, full_name=name if isinstance(name, str) else None)
