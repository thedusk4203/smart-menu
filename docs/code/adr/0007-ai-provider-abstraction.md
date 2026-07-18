# ADR-0007 — AI provider abstraction và structured validation

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: AI integration

## Context

AI dùng `AIClientPort`, OpenAI-compatible adapter, disabled adapter và logged wrapper; provider config được mã hóa.

## Decision

Use case phụ thuộc port; provider active được resolve qua dependency factory và output có cấu trúc qua Pydantic validation. Provider secret/header không đi vào log, nhưng content request/response hiện chưa có redaction tổng quát.

## Consequences

Provider mới cần adapter/test/fallback, không gọi HTTP rải rác từ router. Secret không đi vào response/audit/docs; prompt, context và response log phải được coi là dữ liệu nhạy cảm có quyền truy cập hẹp.

## Verification and revisit trigger

Kiểm provider config/use case/tests. Xem lại khi thêm non-compatible provider hoặc queue/async execution.
