from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.exceptions import AppException
from app.core.config import settings
from app.core.database import engine
from app.modules.ai.conversation_store import ConversationStore
from app.modules.ai.provider_store import AIRequestLogStore
from sqlmodel import Session


logger = logging.getLogger(__name__)


def _purge_expired_conversations() -> int:
    with Session(engine) as session:
        conversations = ConversationStore(session).purge_expired()
        AIRequestLogStore(session).purge_expired()
        return conversations


async def _conversation_retention_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(_purge_expired_conversations)
        except Exception:  # Không làm readiness/liveness của API bị ảnh hưởng bởi cleanup.
            logger.warning("Không thể dọn lịch sử chat quá hạn.", exc_info=True)
        await asyncio.sleep(max(60, settings.ai_conversation_cleanup_interval_seconds))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    cleanup_task = asyncio.create_task(_conversation_retention_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="Smart Menu API",
    description="API backend cho ứng dụng lập thực đơn theo ngân sách và dinh dưỡng",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
def handle_app_exception(_request: Request, exc: AppException) -> JSONResponse:
    """Map domain exception sang HTTP tại duy nhất application boundary này."""
    return JSONResponse(status_code=exc.status_code, content=exc.response_content())


_HTTP_ERROR_DEFAULTS: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "Yêu cầu chưa hợp lệ. Hãy kiểm tra rồi thử lại."),
    401: ("AUTH_SESSION_EXPIRED", "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để tiếp tục."),
    403: ("AUTH_FORBIDDEN", "Bạn không có quyền thực hiện thao tác này."),
    404: ("RESOURCE_NOT_FOUND", "Không tìm thấy dữ liệu được yêu cầu."),
    409: ("RESOURCE_CONFLICT", "Dữ liệu đã thay đổi hoặc đang được sử dụng. Hãy tải lại rồi thử lại."),
    410: ("RESOURCE_GONE", "Nội dung này không còn khả dụng."),
    422: ("VALIDATION_FAILED", "Một số thông tin chưa hợp lệ. Hãy kiểm tra rồi thử lại."),
    503: ("SERVICE_UNAVAILABLE", "Dịch vụ đang tạm gián đoạn. Hãy thử lại sau."),
}


@app.exception_handler(HTTPException)
def handle_http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
    code, message = _HTTP_ERROR_DEFAULTS.get(
        exc.status_code,
        ("HTTP_ERROR", "Không thể hoàn tất yêu cầu. Vui lòng thử lại."),
    )
    code = getattr(exc, "code", code)
    message = getattr(exc, "user_message", None) or message
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "detail": jsonable_encoder(exc.detail),
            "error": {"code": code, "message": message, "details": {}},
        },
    )


def _validation_fields(exc: RequestValidationError) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in exc.errors():
        path = ".".join(str(part) for part in item.get("loc", ()) if part not in {"body", "query", "path"})
        if not path or path in fields:
            continue
        error_type = str(item.get("type") or "")
        if error_type == "missing":
            fields[path] = "Vui lòng nhập thông tin này."
        elif "greater_than" in error_type or "less_than" in error_type:
            fields[path] = "Giá trị nằm ngoài phạm vi cho phép."
        else:
            fields[path] = "Giá trị chưa hợp lệ."
    return fields


@app.exception_handler(RequestValidationError)
def handle_request_validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "error": {
                "code": "REQUEST_VALIDATION_FAILED",
                "message": "Một số thông tin chưa hợp lệ. Hãy kiểm tra các trường được đánh dấu.",
                "details": {},
                "fields": _validation_fields(exc),
            },
        },
    )


@app.exception_handler(Exception)
def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error for %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Đã có lỗi xảy ra.",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Smart Menu chưa thể hoàn tất yêu cầu. Dữ liệu của bạn chưa bị thay đổi.",
                "details": {},
            },
        },
    )


app.include_router(api_router)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}


@app.get("/health/live", tags=["system"])
def liveness_check():
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"])
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database chưa sẵn sàng.",
        ) from exc
    return {"status": "ok"}



