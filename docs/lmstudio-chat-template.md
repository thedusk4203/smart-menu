# Chat Template Menuto cho LM Studio

Template dùng cho model LM Studio của Smart Menu nằm tại
[`lmstudio-smart-menu-chat-template.jinja`](./lmstudio-smart-menu-chat-template.jinja).

Template giữ nguyên ChatML, vision, tool calls và reasoning của model gốc, nhưng
thay identity thành **Menuto**. Menuto hỗ trợ rộng các chủ đề liên quan như gợi ý
món, nguyên liệu, nấu ăn, meal prep, mua sắm và dinh dưỡng phổ thông, kể cả khi
người dùng không nhắc tên ứng dụng. Model chỉ từ chối yêu cầu rõ ràng không liên
quan. Identity không được phép ghi đè system prompt theo tác vụ và không được
chèn lời giới thiệu hoặc câu từ chối vào structured JSON.

Gợi ý dựa trên kiến thức phổ thông phải được phân biệt với dữ liệu riêng của
Smart Menu. Khi backend không cung cấp ngữ cảnh, model không được khẳng định một
món, mức giá, calo hoặc macro cụ thể đang tồn tại trong hệ thống.

## Cài đặt

1. Trong LM Studio, mở **My Models** và bấm biểu tượng bánh răng của model.
2. Mở **Prompt Template**, chọn **Jinja/Custom**.
3. Dán toàn bộ nội dung file `.jinja` ở trên và lưu.
4. Unload rồi load lại model.
5. Trong **Admin → AI Provider** của Smart Menu, bấm **Test** trước khi activate.

Reasoning hoạt động giống template gốc: mặc định template mở `<think>`. Runtime
có thể truyền `enable_thinking=false` để tạo khối reasoning rỗng và đi thẳng
đến final response.

Base URL local không đổi: `http://localhost:1234/v1`.
