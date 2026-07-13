# ADR-0009 — Conversation, request log và retention tách biệt

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: privacy/operations

## Context

`ai_conversations`/turns là product history; `ai_request_logs` là vận hành. Conversation cleanup chạy background/trước read-write; cả hai có policy 30 ngày riêng.

## Decision

Giữ hai lifecycle độc lập, giới hạn 10 conversation/User và 20 turns/conversation; chỉ retry turn gần nhất.

## Consequences

Không dùng request log làm lịch sử UI. Retention phải test và không làm readiness fail nếu cleanup lỗi.

## Verification and revisit trigger

Kiểm conversation retention/tests/main lifespan. Xem lại khi chính sách privacy, legal retention hoặc storage model đổi.

