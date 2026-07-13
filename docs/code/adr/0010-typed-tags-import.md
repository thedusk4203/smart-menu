# ADR-0010 — Typed tags và import preview/commit

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: data governance

## Context

Tag catalog có entity type dish/ingredient; import tạo preview/conflict job rồi commit theo lựa chọn replace/skip.

## Decision

Tag uniqueness theo type + name. Import không ghi catalog tại preview; commit dùng job preview đã lưu và transaction có kiểm conflict.

## Consequences

Rename/active/import phải giữ tag reference nhất quán. Template/export/docs cần version theo contract data.

## Verification and revisit trigger

Kiểm typed-tags, import-template, quality tests. Xem lại khi thêm entity type hoặc async bulk import.

