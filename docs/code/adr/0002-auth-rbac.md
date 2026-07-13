# ADR-0002 — JWT, Google verification và RBAC

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: identity/security

## Context

Backend decode Bearer JWT, kiểm account active và enforce role dependencies. Google credential được verify backend; roles gồm user, data editor, admin legacy và super admin.

## Decision

Backend là authority cuối cho authentication, ownership và RBAC; `admin` được tương thích như super admin. Frontend guards chỉ điều hướng UX.

## Consequences

Mỗi endpoint mutation phải chọn dependency role hẹp nhất và test 401/403. Không tin role/token data do client tự gửi.

## Verification and revisit trigger

Kiểm `core/deps.py`, identity tests và API role matrix. Xem lại khi thêm SSO, token rotation hoặc role mới.

