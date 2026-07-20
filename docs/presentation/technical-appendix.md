# Phụ lục kỹ thuật — slide dự phòng khi bảo vệ

Không tính các slide này vào 22 slide chính. Dùng khi hội đồng hỏi sâu về code, contract hoặc vận hành.

| # | Nội dung trên slide | Visual/code anchor | Speaker note | Câu hỏi có thể gặp |
| --- | --- | --- | --- | --- |
| A1 | Modular monolith: React, FastAPI, PostgreSQL, provider AI tùy chọn | Sơ đồ trong `code/architecture.md` | “Chia module theo nghiệp vụ để giữ deploy đơn giản nhưng không trộn business rule.” | Vì sao không microservice? |
| A2 | Backend layering và composition root | `backend/app/api.py`, `dependencies.py` | “Router xử lý HTTP, use case điều phối, repository cách ly SQL.” | Dependency injection đem lại gì? |
| A3 | Frontend route guard không phải security boundary | `frontend/src/app/router.tsx`, `core/deps.py` | “UI điều hướng; backend vẫn trả 401/403.” | Data editor vào Admin có làm được mọi thứ? |
| A4 | API contract: 70 path, 97 operation, 101 schema | `code/api/README.md` | “Schema copy từ OpenAPI; mỗi thay đổi router/schema phải đồng bộ docs.” | Làm sao tránh API docs cũ? |
| A5 | Database: candidate view và snapshot | `data/init_db.sql`, `code/database.md` | “Planner không đọc raw dish; history dùng snapshot.” | Vì sao tồn tại meals và dishes? |
| A6 | Planner V3 CP-SAT + ledger checker | `optimizer_v3.py`, `procurement_checker.py` | “Solver tối ưu mua mới và tồn kho; checker chứng minh lại ledger và dinh dưỡng độc lập.” | AI có tạo thực đơn không? |
| A7 | AI provider/SSE/retention | `ai/client.py`, `ai/use_cases.py` | “AI làm ngôn ngữ; backend giữ authority dữ liệu và log/history tách nhau.” | Khi AI tắt thì sao? |
| A8 | Admin import và quality | `admin/use_cases.py`, `tag_catalog` | “Preview phát hiện lỗi/conflict; commit mới mutation.” | Vì sao typed tag? |
| A9 | Security và public sharing | `core/deps.py`, `shopping_lists` | “Share token là capability 7 ngày, revoke được.” | Token link có an toàn không? |
| A10 | Evidence phát hành | `code/testing.md`, `launch-readiness.md` | “189 test backend, TypeScript/ESLint/release guard/build đã kiểm tại mốc tài liệu.” | Test pass có nghĩa hết bug không? |

## Quy tắc trả lời kỹ thuật

- Chỉ khẳng định điều có source/test/contract chứng minh.
- Nêu giới hạn thật: mobile Menuto còn có nhãn bị cắt ở 390 px; chưa có E2E/axe CI và audit security độc lập.
- Khi không nhớ field schema, mở Swagger hoặc API reference thay vì đoán.
