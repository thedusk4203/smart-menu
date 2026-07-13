# ADR-0004 — Dữ liệu có cấu trúc và snapshot thực đơn

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: data integrity

## Context

Nutrition/price/recipe nằm trong bảng có cấu trúc; meal plan lưu `plan_data` snapshot và shopping list materialize purchase state.

## Decision

Tính giá/nutrition từ structured data và giữ snapshot plan tại thời điểm tạo; không suy diễn lại lịch sử từ AI hoặc catalog đã đổi.

## Consequences

Schema snapshot thay đổi phải có migration/reader compatibility. Giá là snapshot tham khảo, không phải realtime guarantee.

## Verification and revisit trigger

Kiểm planner/save/shopping tests và schema database. Xem lại khi cần versioned event store hoặc price source realtime.

