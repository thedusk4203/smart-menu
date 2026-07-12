FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/app ./app
COPY backend/scripts ./scripts

CMD ["sh", "-c", "if [ \"$DEMO_SEED\" = \"true\" ]; then uv run --no-sync python scripts/seed_demo.py; fi; exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000"]
