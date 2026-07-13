# ADR-0006 — Infeasible, regenerate và swap phải có cấu trúc

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: planner UX/contract

## Context

Budget/pool/nutrition có thể không khả thi; regenerate dùng signature và swap có AI ranking.

## Decision

Trả infeasible reason có cấu trúc thay vì plan sai. Regenerate yêu cầu signature khác; swap chỉ trả sau full-plan validation.

## Consequences

Frontend phải render outcome union đúng schema. AI ranking không được coi là validity proof.

## Verification and revisit trigger

Kiểm feasibility, planner và swap tests. Xem lại khi thêm objective/ràng buộc hoặc UX chỉnh reason code.

