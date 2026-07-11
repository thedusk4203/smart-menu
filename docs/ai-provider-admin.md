# AI Provider Administration

## Phạm vi

Smart Menu dùng LLM cho bốn tác vụ ngôn ngữ: chat, parse yêu cầu thực đơn,
giải thích plan đã validate và xếp hạng candidate đổi món. Planner, giá, dinh
dưỡng và hard constraints không phụ thuộc kết quả LLM.

## Cài đặt database và secret

1. Chạy `data/migrations/20260711_ai_provider_admin.sql` trên database hiện có.
2. Đặt `AI_CONFIG_ENCRYPTION_KEY` thành một secret dài, ổn định trong môi trường
   backend. Nếu mất key này, API key đã lưu phải được nhập lại.
3. Khởi động lại backend, đăng nhập bằng `admin` hoặc `super_admin`, mở
   `/admin/ai`.

Không commit API key hoặc `AI_CONFIG_ENCRYPTION_KEY`. Cấu hình `.env` cũ chỉ là
fallback khi bảng provider còn trống; sau khi admin tạo provider đầu tiên, DB là
nguồn cấu hình runtime.

## Vòng đời provider

Provider mới luôn là draft. Admin test kết nối, text completion và structured
output trước khi kích hoạt. Mọi thay đổi connectivity làm test cũ mất hiệu lực.
Provider active không sửa trực tiếp; clone thành draft, chỉnh, test và activate
để chuyển đổi nguyên tử.

Preset hỗ trợ OpenAI, DeepSeek, Google Gemini, LM Studio và custom
OpenAI-compatible. Google Gemini dùng endpoint OpenAI-compatible
`https://generativelanguage.googleapis.com/v1beta/openai`. DeepSeek
dùng JSON Object + Pydantic validation; các provider hỗ trợ schema dùng strict
JSON Schema.

Khi dùng model Qwythos trong LM Studio, cài
[`Chat Template Menuto`](./lmstudio-chat-template.md) để giữ reasoning nhưng giới
hạn model trong phạm vi Smart Menu và tránh identity mặc định ghi đè system
prompt của ứng dụng.

## Log và riêng tư

Prompt/response được lưu đầy đủ trong `ai_request_logs` tối đa 30 ngày. Chỉ
super admin đọc hoặc purge log. API key, authorization header và access token
không được ghi. Dữ liệu hết hạn được dọn khi có AI traffic hoặc khi admin mở
danh sách log; admin cũng có nút purge thủ công.
