# API reference Smart Menu

## Cách dùng

API reference này được chia theo domain để dễ bảo trì. Các file domain chứa method/path, parameter, content type và schema cần thiết để dùng/debug contract; OpenAPI runtime vẫn là nguồn máy đọc đầy đủ nhất.

| Domain | Operation baseline | File |
| --- | ---: | --- |
| System/Auth/User/Profile/Nutrition | 24 | [auth-profile.md](auth-profile.md) |
| Catalog/Dish/Meal/Tag | 17 | [catalog-tags.md](catalog-tags.md) |
| Meal plan/Shopping/Inventory/Public share | 13 | [planner-shopping.md](planner-shopping.md) |
| User AI/Admin AI | 24 | [ai.md](ai.md) |
| Admin user/data/quality/import | 25 | [admin.md](admin.md) |

Baseline ngày 20/07/2026: **75 paths, 103 operations, 112 component schemas**. OpenAPI runtime tại `/openapi.json` và Swagger tại `/docs` là nguồn kiểm chứng; không xem count trong Markdown là hằng số.

## Contract chung

- API private dùng `Authorization: Bearer <access_token>`; token không bao giờ được đưa vào docs/example.
- Lỗi business theo handler có body `{ "detail": "..." }`. Lỗi request validation là `HTTPValidationError`/`ValidationError` trong schema catalog.
- `401` áp dụng khi token thiếu/sai/hết hạn hoặc account inactive; `403` khi role/ownership không đủ; `404` khi resource không tồn tại hoặc không được phép lộ; `422` khi parameter/body không hợp lệ.
- `204` không có response body. Chat/retry AI dùng `text/event-stream` thay JSON; file AI mô tả content type và payload schema liên quan.
- Mỗi thay đổi router/schema phải chạy lại `/openapi.json`, cập nhật đúng domain, đảm bảo không mất schema reference và sửa frontend wrapper nếu có consumer.

## Quy tắc bảo trì schema

Schema JSON trong từng domain là full OpenAPI copy, gồm `required`, `nullable` (`anyOf` với `null`), enum, format, range, default và nested `$ref`. `$ref` luôn trỏ tới heading schema trong cùng file hoặc API domain liên quan; nếu di chuyển schema, phải sửa link/reference và kiểm lại closure.
