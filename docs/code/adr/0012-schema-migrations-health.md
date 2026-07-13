# ADR-0012 — Baseline schema, migration runner và health checks

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: operations/data deployment

## Context

Database mới dùng `init_db.sql`; database tồn tại dùng SQL migration runner và `schema_migrations`. Backend có liveness/readiness; Compose dùng DB health dependency.

## Decision

Giữ baseline schema cho fresh install và immutable incremental migration cho tồn tại. Readiness kiểm DB; liveness không bị ảnh hưởng bởi cleanup background lỗi.

## Consequences

Không sửa migration đã áp dụng; backup trước migration demo có data. Release phải kiểm health và migration order.

## Verification and revisit trigger

Kiểm migration runner, Compose health, `/health/live`, `/health/ready`. Xem lại khi đưa migration tool khác, multi-node hoặc zero-downtime requirement.

