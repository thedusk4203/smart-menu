# Smart Menu

Smart Menu tạo thực đơn theo mục tiêu dinh dưỡng và ngân sách từ dữ liệu nguyên liệu/món có cấu trúc. Frontend dùng React/TypeScript, backend FastAPI modular monolith và PostgreSQL; AI là trợ lý tùy chọn, không phải authority cho giá, dinh dưỡng hoặc tính hợp lệ thực đơn.

## Bắt đầu nhanh

1. Tạo `.env` từ `.env.example` và `backend/.env` từ `backend/.env.example`; thay placeholder secret bằng dữ liệu local riêng.
2. Chạy database: `docker compose up -d` (PostgreSQL local port `5433`).
3. Backend: `cd backend; uv sync --extra dev; uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001`.
4. Frontend: `cd frontend; npm install; npm run dev` (Vite port `5173`, proxy `/api` tới `8001`).
5. Kiểm backend bằng `/health/live` và `/health/ready`.

Docker demo dùng `docker compose --profile demo up --build -d`; frontend mặc định ở `127.0.0.1:8080`, backend `8000` chỉ ở Docker network.

## Tài liệu

- [Bộ tài liệu đồ án](docs/README.md): slide, demo và hướng dẫn non-tech.
- [Handbook kỹ thuật](docs/code/README.md): code architecture, database và 16 bài học chuyên sâu về Meal Plan, Nutrition, AI, Shopping List, kèm quiz có đáp án.
- [API reference](docs/code/api/README.md): schema đầy đủ theo domain; Swagger runtime ở `/docs`.
- [ADR](docs/code/adr/README.md): quyết định kiến trúc retrospective.

## Kiểm tra trước khi bàn giao

```powershell
cd backend; uv run pytest -q
cd frontend; npm run build
cd frontend; npm run lint
cd frontend; npm run check:release
```

## Quy tắc làm việc

- Không commit `.env`, database password, token, API key, log hoặc build artifact.
- Một commit chỉ giải quyết một vấn đề; không push trực tiếp `main`.
- Thay đổi `docker-compose.yml`, backend `main.py`, frontend `router.tsx`/`App.tsx` cần phối hợp nhóm.
- Khi thay đổi contract/schema/feature, cập nhật API docs, handbook, test và guide liên quan theo [maintenance workflow](docs/code/maintenance.md).
