# File: backend/app/main.py
# Application entrypoint.
#
# NOTE: schema CSDL do data/init_db.sql (hoáº·c Alembic migrations) quáº£n lÃ½ â€”
# KHÃ”NG gá»i SQLModel.metadata.create_all() á»Ÿ Ä‘Ã¢y.
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.exceptions import AppException

app = FastAPI(
    title="Smart Menu API",
    description="API backend cho á»©ng dá»¥ng láº­p thá»±c Ä‘Æ¡n theo ngÃ¢n sÃ¡ch & dinh dÆ°á»¡ng",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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



