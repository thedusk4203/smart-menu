# ADR-0008 — AI không là authority cho business fact

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: AI safety/product correctness

## Context

AI parse Vietnamese, explain plan, suggest swap và chat; planner/database đã có validation riêng.

## Decision

AI chỉ parse/giải thích/xếp hạng. Backend dữ liệu có cấu trúc quyết định price, nutrition, exclusions, budget và plan validity; explanation được ground bằng facts.

## Consequences

AI disabled không được làm planner structured form ngừng hoạt động. New AI task cần nêu authority boundary trong code/docs/test.

## Verification and revisit trigger

Kiểm AI use case, planner checker và disabled-provider smoke. Xem lại khi có tool-calling mutation hoặc clinical feature.

