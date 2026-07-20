# ADR-0012 — Baseline schema, migration runner và health checks

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: operations/data deployment

## Context

Database mới dùng `init_db.sql`; database tồn tại dùng SQL migration runner và `schema_migrations`. Backend có liveness/readiness; Compose dùng DB health dependency.

## Decision

Giữ baseline schema cho fresh install và immutable incremental migration cho tồn tại. Runner dùng registry tường minh, SHA-256 checksum, advisory lock và chế độ `--plan`. Migration phá dữ liệu bị chặn mặc định và chỉ chạy khi có `--allow-destructive`. Readiness kiểm DB; liveness không bị ảnh hưởng bởi cleanup background lỗi.

## Consequences

Không sửa migration đã áp dụng; file lạ hoặc thiếu trong registry làm release dừng. Cutover V3 cố ý xóa plan V1/V2 cùng shopping/share phụ thuộc, nên phải backup và kiểm impact count trước. Release phải kiểm health, checksum và migration order. Project không duy trì Alembic song song với SQL runner.

## Verification and revisit trigger

Kiểm `--plan`, checksum mismatch, destructive opt-in, Compose health, `/health/live`, `/health/ready`. Xem lại khi đưa migration tool khác, multi-node hoặc zero-downtime requirement.
