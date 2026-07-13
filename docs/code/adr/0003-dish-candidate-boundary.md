# ADR-0003 — Boundary dishes, meals và planner-ready candidate

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: food catalog/planner compatibility

## Context

Schema còn `meals` CRUD và `dishes` recipe catalog. User dishes router và planner provider đọc `v_dish_candidates`.

## Decision

`v_dish_candidates` là candidate boundary hiện tại. `meals` vẫn được giữ như legacy CRUD/compatibility, không thay thế `dishes` trong planner.

## Consequences

Chất lượng dữ liệu quyết định candidate availability; không bypass view bằng raw table query. Refactor hợp nhất hai model cần migration/compatibility plan riêng.

## Verification and revisit trigger

Kiểm dish candidate invariants, router queries và quality tests. Xem lại khi deprecate `meals` hoặc thay planner data model.

