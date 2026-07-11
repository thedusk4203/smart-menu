# Database design — Dish Planner V2

`dishes` và `dish_ingredients` là mô hình chuẩn duy nhất cho planner. Không có
bảng meal set hoặc dynamic meal: composition là dữ liệu runtime trong `plan_data`.

`v_dishes_full` tính totals và completeness theo từng ingredient: `ingredient_count`,
`nutrition_count`, `priced_ingredient_count`, `all_ingredients_active`,
`has_complete_nutrition`, `has_complete_price`, ingredient JSON và IDs.

`v_dish_candidates` lọc chỉ dish active có đủ recipe, mọi ingredient active,
nutrition/price hoàn chỉnh, calories và cost dương. Nó là nguồn duy nhất của
`SqlDishCandidateProvider`.

`meal_plans.plan_data`:

- V1 tiếp tục đọc để hiển thị lịch sử.
- V2 lưu `schema_version=2`, request/target snapshot, dish snapshot gồm totals
  và ingredient quantity/unit/cost, metrics, structured warnings và signature.

Migration `data/migrations/20260710_dish_planner_v2.sql` gỡ view/table/type
Meal Sets theo dependency order nhưng không xóa `meal_plans`, vì vậy lịch sử V1
không bị mất.

## AI conversation history

`ai_conversations` lưu tối đa 10 cuộc hội thoại cho mỗi user theo ràng buộc ở
use case, gồm title suy ra từ câu đầu và thời gian hoạt động. Bảng
`ai_conversation_turns` lưu tối đa 20 lượt, mỗi lượt ghép một câu hỏi với một
câu trả lời và trạng thái `pending/completed/failed`; unique
`(conversation_id, turn_number)` bảo đảm thứ tự ổn định.

Hai bảng cascade theo user/conversation và tồn tại đến khi user xóa. Chúng tách
khỏi `ai_request_logs`: log vận hành vẫn tự hết hạn sau 30 ngày và không được
dùng làm lịch sử sản phẩm. Migration tương ứng là
`data/migrations/20260711_ai_conversations.sql`.

