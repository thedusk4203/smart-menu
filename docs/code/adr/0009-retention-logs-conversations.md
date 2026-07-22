# ADR-0009 — Conversation, request log và retention tách biệt

- Status: Accepted — retrospective
- Date: 2026-07-13; reviewed 2026-07-22
- Scope: privacy/operations

## Context

`ai_conversations`/turns là product history; `ai_request_logs` là vận hành. Conversation/turn nay còn lưu mode, personalization-used, grounding mode và citation. Conversation cleanup chạy background/trước read-write; cả hai có policy 30 ngày riêng.

## Decision

Giữ hai lifecycle độc lập, giới hạn 10 conversation/User và 20 turns/conversation; chỉ retry turn gần nhất.

## Consequences

Không dùng request log làm lịch sử UI. Xóa conversation không xóa request log cùng nội dung; quyền xem log và privacy notice phải phản ánh điều này. Retention phải test và không làm readiness fail nếu cleanup lỗi. Khi AI state dùng database riêng, mọi cleanup phải mở state session/engine thay vì primary engine.

## Verification and revisit trigger

Kiểm conversation retention/tests/main lifespan. Hiện vòng background trong `main.py` vẫn dùng primary `engine`, nên phải sửa hoặc xác minh trước deployment tách state database. Xem lại khi chính sách privacy, legal retention hoặc storage model đổi.
