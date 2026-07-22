# ADR-0008 — AI không là authority cho business fact

- Status: Accepted — retrospective
- Date: 2026-07-13; reviewed 2026-07-22
- Scope: AI safety/product correctness

## Context

AI parse Vietnamese, explain plan, suggest swap và chat; planner/database đã có validation riêng.

## Decision

AI chỉ parse/giải thích/xếp hạng. Backend dữ liệu có cấu trúc quyết định price, nutrition, exclusions, budget và plan validity; explanation được ground bằng facts.

Chat được chia theo purpose: `general` không đọc hồ sơ; `meal_advice` và `health_reference` chỉ đọc projection đã giới hạn sau consent. Health reference ưu tiên native web search và chỉ công bố trạng thái grounded khi có citation URL hợp lệ; nếu capability không sẵn sàng, UI phải ghi rõ đây là model fallback chưa được kiểm chứng web theo thời gian thực. Citation làm rõ nguồn tham khảo, không biến AI thành authority y khoa.

## Consequences

AI disabled không được làm planner structured form ngừng hoạt động. Tag do AI parse chỉ được đưa vào planner khi khớp catalog active; tag không nhận diện nằm ở `unresolved_tags`. New AI task cần nêu authority boundary, purpose dữ liệu và grounding state trong code/docs/test.

## Verification and revisit trigger

Kiểm AI use case, planner checker và disabled-provider smoke. Xem lại khi có tool-calling mutation hoặc clinical feature.
