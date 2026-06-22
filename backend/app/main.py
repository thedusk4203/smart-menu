# File: backend/app/main.py
# Application entrypoint.
#
# NOTE: schema CSDL do data/init_db.sql (hoặc Alembic migrations) quản lý —
# KHÔNG gọi SQLModel.metadata.create_all() ở đây.
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.exceptions import AppException

app = FastAPI(
    title="Smart Menu API",
    description="API backend cho ứng dụng lập thực đơn theo ngân sách & dinh dưỡng",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo; siết lại theo domain frontend khi deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """Map mọi domain exception (NotFoundError/ConflictError/...) sang HTTP
    response. Use case/domain layer không phụ thuộc FastAPI — chỉ có điểm
    này mới biết tới HTTP."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(api_router)


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
