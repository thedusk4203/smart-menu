from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.exceptions import AppException
from app.core.config import settings
from app.core.database import engine
from app.modules.ai.conversation_store import ConversationStore
from sqlmodel import Session


logger = logging.getLogger(__name__)


def _purge_expired_conversations() -> int:
    with Session(engine) as session:
        return ConversationStore(session).purge_expired()


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
    description="API backend cho á»©ng dá»¥ng láº­p thá»±c Ä‘Æ¡n theo ngÃ¢n sÃ¡ch & dinh dÆ°á»¡ng",
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
def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """Map má»i domain exception (NotFoundError/ConflictError/...) sang HTTP
    response. Use case/domain layer khÃ´ng phá»¥ thuá»™c FastAPI â€” chá»‰ cÃ³ Ä‘iá»ƒm
    nÃ y má»›i biáº¿t tá»›i HTTP."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


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



