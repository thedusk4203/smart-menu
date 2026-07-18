# ADR-0011 — Shopping-share là capability token giới hạn

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: public sharing/privacy

## Context

Share token cho danh sách đi chợ có scope hiển thị plan/ngày, hạn 7 ngày, revoke và cho phép toggle purchased.

## Decision

Không yêu cầu login cho public share nhưng token là capability nhạy cảm; public API chỉ expose shopping payload cần thiết.

Implementation note ngày 15/07/2026: GET tôn trọng day scope, nhưng public PATCH hiện chỉ kiểm `item_id` thuộc plan. Write-scope theo ngày chưa được cưỡng chế hoàn toàn và purchased state là toàn plan.

## Consequences

Không log/hiển thị token, revoke phải vô hiệu link hiện hành và docs/demo dùng token giả/ẩn. Nếu sản phẩm cần purchased riêng từng ngày hoặc write-scope chặt, phải thay schema/persistence/authorization và bổ sung regression test.

## Verification and revisit trigger

Kiểm shopping list tests, expiry/revoke/public UI smoke. Xem lại khi cần read-only share, identity tracking hoặc permission khác.
