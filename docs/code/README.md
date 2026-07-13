# Smart Menu — Handbook kỹ thuật

Tài liệu này dành cho developer bảo trì Smart Menu và người thuyết trình phần kỹ thuật. Nguồn sự thật là working tree hiện tại, được đối chiếu ngày **13/07/2026**. Không tài liệu nào ở đây thay thế code, OpenAPI runtime hoặc migration SQL.

## Lộ trình đọc

1. [Kiến trúc hệ thống](architecture.md) để hiểu ranh giới thành phần và quyền.
2. [Backend](backend.md), [frontend](frontend.md), rồi [database](database.md) để biết vị trí code.
3. Đọc [planner](meal-planner.md), [AI](ai.md) và [vòng đời dữ liệu Admin](admin-data.md) trước khi sửa nghiệp vụ.
4. Đọc [bảo mật](security.md), [testing](testing.md), [vận hành](operations.md) và [quy trình bảo trì](maintenance.md) trước khi phát hành.
5. Tra [API reference](api/README.md) khi thay đổi contract HTTP; tra [ADR](adr/README.md) khi cần biết quyết định hiện tại và hệ quả.

## Mục lục đầy đủ

- [Architecture](architecture.md), [Backend](backend.md), [Frontend](frontend.md), [Database](database.md)
- [Meal planner](meal-planner.md), [AI](ai.md), [Admin data lifecycle](admin-data.md), [Security](security.md)
- [Testing](testing.md), [Operations](operations.md), [Maintenance workflow](maintenance.md)
- [API reference theo domain](api/README.md) và [ADR retrospective](adr/README.md)

## Quy ước đọc code

- Backend là FastAPI modular monolith. Luồng chuẩn: `router.py` → `schemas.py` → `use_cases.py` → `ports.py`/`repository.py` → PostgreSQL.
- Frontend là React/TypeScript. Luồng chuẩn: `router.tsx` → `pages/` → `api/` → `lib/apiClient.ts` → backend.
- Chỉ `dishes` qua `v_dish_candidates` là catalog User/planner hiện tại. `meals` vẫn tồn tại như CRUD/legacy compatibility; không giả định hai nguồn này thay thế nhau.
- AI chỉ parse, giải thích, xếp hạng và hội thoại. Backend cùng dữ liệu có cấu trúc kiểm tra giá, dinh dưỡng, nguyên liệu loại trừ, ngân sách và plan hợp lệ.

## Mốc kiểm chứng hiện tại

| Mục | Giá trị |
| --- | --- |
| Frontend routes khai báo | 23 |
| OpenAPI paths / operations / schemas | 70 / 97 / 101 |
| PostgreSQL tables / views / enums | 20 / 5 / 9 |
| Backend tests gần nhất | 189 passed |

Các số này là baseline, không phải hằng số. Khi code thay đổi, chạy lại kiểm kê trong [testing](testing.md) và cập nhật tài liệu liên quan.

## Tài liệu liên quan

- [Tổng quan kỹ thuật ngắn](../technical-overview.md)
- [Tài liệu người dùng](../guides/README.md)
- [Dàn ý trình bày](../presentation/slide-outline.md)
- [Technical appendix](../presentation/technical-appendix.md)
- [Code walkthrough khi bảo vệ](../presentation/code-walkthrough.md)
