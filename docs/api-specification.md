# API specification — Dish Planner V2

`POST /api/meal-plans/generate`

```json
{"days": 7, "meals_per_day": 3, "budget_limit": 700000, "preferred_tags": ["ít dầu"], "previous_plan_signature": "..."}
```

Success trả `plan_data.schema_version=2`, `plan_signature`, `metrics`, structured
warnings và meals có `candidate_type="dynamic_meal"` với `dishes[]`. Infeasible
trả `{ "status": "infeasible", "reasons": [{"code", "message", "details"}] }`.

`POST /api/meal-plans`

```json
{"name":"Tuần 1", "start_date":"2026-07-10", "days":[{"day":1,"meals":[{"slot":"breakfast","dish_ids":[31]},{"slot":"lunch","dish_ids":[1,8,15]},{"slot":"dinner","dish_ids":[2,9,20]}]}]}
```

Backend reload dish IDs, suy ra role từ `dish_type`, rebuild target/exclusions,
validate checker và snapshot lại; không tin role/totals từ client. Lỗi selection
trả 422.

`GET /api/meal-plans/{plan_id}/shopping-list` trả grocery list đã group theo
`ingredient_id + unit`. V2 đọc snapshot; V1 dùng current recipe best effort và
trả warning `LEGACY_PLAN_USES_CURRENT_RECIPE`.

## AI conversation history

`POST /api/ai/chat` tự tạo conversation khi `conversation_id=null`, hoặc nối
tiếp conversation thuộc user hiện tại khi có ID:

```json
{"message":"Gợi ý bữa sáng giàu đạm", "conversation_id":12}
```

Response là `text/event-stream`. Backend tự đọc lịch sử từ database; `history`
do client cũ gửi không được dùng làm nguồn chính thức. Các event theo thứ tự:

- `start`: `{conversation_id, turn}` với turn `pending`.
- `delta`: `{content}` cho từng phần câu trả lời.
- `done`: `{reply, conversation_id, turn}` khi turn đã `completed` và được lưu.
- `error`: `{detail, conversation_id, turn_id, retryable:true}` khi stream lỗi.

Lỗi ownership/giới hạn được kiểm tra trước khi mở stream và vẫn trả JSON HTTP
`404`, `409` hoặc `422`. Khi stream đã bắt đầu, lỗi provider được gửi bằng event
`error`, turn được đánh dấu `failed` và có thể Retry. Câu trả lời partial không
được lưu vào lịch sử.

- `GET /api/ai/conversations`: tối đa 10 summary, mới hoạt động gần nhất trước.
- `GET /api/ai/conversations/{id}`: toàn bộ tối đa 20 turns.
- `DELETE /api/ai/conversations/{id}`: xóa conversation của user hiện tại.
- `POST /api/ai/conversations/{id}/turns/{turn_id}/retry`: chỉ retry turn cuối,
  dùng cùng SSE contract và thay assistant response khi thành công.

Tạo conversation thứ 11 hoặc câu thứ 21 trả `409`. ID không thuộc user hiện tại
trả `404`. LLM chỉ nhận tối đa 10 message/12.000 ký tự gần nhất; lịch sử hiển
thị vẫn giữ đủ 20 turns.

Tất cả provider dùng sampling và giới hạn output mặc định của model: payload AI
không gửi `temperature` hoặc `max_tokens`. Chỉ chat/retry gửi `stream:true`; các
tác vụ AI còn lại gửi `stream:false`.

