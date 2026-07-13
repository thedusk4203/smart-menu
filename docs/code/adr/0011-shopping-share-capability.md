# ADR-0011 — Shopping-share là capability token giới hạn

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: public sharing/privacy

## Context

Share token cho danh sách đi chợ có scope plan/ngày, hạn 7 ngày, revoke và cho phép toggle purchased trong scope.

## Decision

Không yêu cầu login cho public share nhưng token là capability nhạy cảm; public API chỉ expose shopping payload cần thiết.

## Consequences

Không log/hiển thị token, revoke phải vô hiệu link hiện hành và docs/demo dùng token giả/ẩn.

## Verification and revisit trigger

Kiểm shopping list tests, expiry/revoke/public UI smoke. Xem lại khi cần read-only share, identity tracking hoặc permission khác.

