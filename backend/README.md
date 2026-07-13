# Smart Menu Backend

FastAPI backend chạy local ở `127.0.0.1:8001`; Docker demo dùng port nội bộ `8000`.

```powershell
uv sync --extra dev
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
uv run pytest -q
```

Tạo `backend/.env` từ `.env.example`; không commit secret. Database local mặc định ở PostgreSQL port `5433`. Với database tồn tại, áp dụng migration bằng `uv run python scripts/apply_migrations.py`.

Đọc [backend handbook](../docs/code/backend.md), [API reference](../docs/code/api/README.md), [database/migrations](../docs/code/database.md) và [operations](../docs/code/operations.md) trước khi sửa contract hoặc persistence.

