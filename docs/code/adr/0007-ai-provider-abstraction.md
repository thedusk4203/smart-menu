# ADR-0007 — AI provider abstraction và structured validation

- Status: Accepted — retrospective
- Date: 2026-07-13; reviewed 2026-07-22
- Scope: AI integration

## Context

AI dùng `AIClientPort`, OpenAI-compatible adapter, disabled adapter và logged wrapper; provider config được mã hóa.

## Decision

Use case phụ thuộc port; provider active được resolve qua dependency factory và output có cấu trúc qua Pydantic validation. Provider secret/header không đi vào log. Personal context có marker riêng và được thay bằng `[PERSONAL_CONTEXT_REDACTED]` trước khi ghi request log; content khác vẫn chưa có redaction PII tổng quát.

Capability native web search được cấu hình rõ trên provider. Provider test chỉ xác nhận capability này khi response có citation `http`/`https` hợp lệ; health reference không được tự gắn nhãn grounded chỉ vì model trả văn bản.

## Consequences

Provider mới cần adapter/test/fallback, không gọi HTTP rải rác từ router. Secret không đi vào response/audit/docs; prompt, câu hỏi và response log vẫn phải được coi là dữ liệu nhạy cảm có quyền truy cập hẹp. Citation là provenance, không phải bảo chứng y khoa.

## Verification and revisit trigger

Kiểm provider config/use case/tests. Xem lại khi thêm non-compatible provider hoặc queue/async execution.
