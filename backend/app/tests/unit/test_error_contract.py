from app.core.exceptions import AppException, ValidationAppError


def test_app_exception_keeps_legacy_detail_and_adds_structured_error() -> None:
    exc = AppException(
        "Database constraint failed",
        code="SAVE_FAILED",
        user_message="Chưa lưu được dữ liệu.",
        details={"request_id": "req-1"},
        fields={"name": "Tên chưa hợp lệ."},
    )

    assert exc.response_content() == {
        "detail": "Database constraint failed",
        "error": {
            "code": "SAVE_FAILED",
            "message": "Chưa lưu được dữ liệu.",
            "details": {"request_id": "req-1"},
            "fields": {"name": "Tên chưa hợp lệ."},
        },
    }


def test_subclass_supplies_stable_default_code() -> None:
    exc = ValidationAppError("Invalid input")

    assert exc.status_code == 422
    assert exc.response_content()["detail"] == "Invalid input"
    assert exc.response_content()["error"]["code"] == "VALIDATION_FAILED"
