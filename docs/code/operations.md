# Vận hành, môi trường và deployment

## Mục tiêu

Chạy Smart Menu an toàn ở local/demo, kiểm tra health, áp dụng migration và xử lý lỗi khởi động có hệ thống.

## Nguồn sự thật

- [Docker Compose](../../docker-compose.yml), `docker/`, `.env.example`, `backend/.env.example`.
- [Migration guide](../../data/migrations/README.md) và backend/frontend package manifests.

## Topology và cổng

| Môi trường | Frontend | Backend | PostgreSQL |
| --- | --- | --- | --- |
| Local | Vite `5173` | Uvicorn `8001` | Host `5433` |
| Docker demo | Nginx `8080` mặc định | Internal `8000` | Host `5433` (loopback) |

Không chạy local backend khác ở `8000`: Vite proxy `/api` tới `127.0.0.1:8001`. Docker profile `demo` tách backend/frontend khỏi database service mặc định.

## Local workflow

1. Tạo `.env` từ `.env.example` và `backend/.env` từ `backend/.env.example`; thay toàn bộ placeholder secret bằng giá trị local riêng.
2. Chạy PostgreSQL qua `docker compose up -d`.
3. Trong `backend`, dùng `uv sync --extra dev`, sau đó `uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001`.
4. Trong `frontend`, cài dependency rồi `npm run dev`.
5. Kiểm `/health/live` và `/health/ready`; `ready` kiểm database, `live` chỉ xác nhận process.

## Docker demo và migration

`docker compose --profile demo up --build -d` dùng env Docker. Database mới nhận baseline schema từ volume init. Database tồn tại cần migration runner; không hy vọng init script chạy lại khi volume đã có dữ liệu. `DEMO_SEED` là opt-in; account demo và secret không được commit/chụp ảnh.

## Troubleshooting nhanh

| Symptom | Kiểm tra đầu tiên |
| --- | --- |
| `ready` 503 | Connection env, DB container health, port 5433 |
| Login 401 | Token expiry, account active, backend secret/config |
| Google button không hiện | Client ID frontend config; backend verify vẫn bắt buộc |
| AI unavailable | Active provider, encrypted key, base URL/model/timeout; planner vẫn có form structured |
| Candidate ít | Quality issue/view `v_dish_candidates`, không phải solver timeout |
| Migration không chạy | `schema_migrations`, filename order, backup và runner log |

## Khi nào phải cập nhật tài liệu này

Cập nhật khi đổi port, Docker service/profile, env, health check, migration workflow, seed, deployment exposure hoặc troubleshooting policy.

## Kiểm tra mức độ hiểu

### Câu 1 (trắc nghiệm)

Endpoint nào xác minh database sẵn sàng?

A. `/health/live`  
B. `/health/ready`  
C. `/api/auth/me`

### Câu 2 (trắc nghiệm)

Vì sao `init_db.sql` không phải cách cập nhật database đã có dữ liệu?

A. Chỉ chạy khi database volume mới khởi tạo  
B. Không có SQL  
C. Chỉ dành cho frontend

### Câu 3 (trắc nghiệm)

Khi AI provider tắt, behavior đúng cho planner là gì?

A. Planner không thể dùng  
B. Form structured vẫn hoạt động  
C. Database bị reset

### Câu 4 (tình huống)

Docker frontend chạy nhưng API trả 502. Hãy nêu chuỗi kiểm tra từ container tới readiness.

### Câu 5 (tình huống)

Bạn chuẩn bị demo có seed. Hãy nêu các nguyên tắc dữ liệu/secret phải giữ.

## Đáp án, giải thích và bằng chứng mong đợi

1. **B.** Readiness thực hiện query kiểm DB.
2. **A.** Entrypoint init chỉ chạy lúc volume/database mới.
3. **B.** AI là optional assistance, không phải planner authority.
4. Kiểm backend container started/health, `/health/ready` trong network Docker, env DB/secret/CORS, frontend dependency URL/proxy rồi container logs có redaction.
5. Dùng account/dữ liệu giả, env riêng, không commit hay chiếu password/token/API key, thu hồi public share sau demo.


Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
