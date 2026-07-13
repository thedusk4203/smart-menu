# Kịch bản demo Smart Menu (6–8 phút)

## Mục tiêu demo

Chứng minh một yêu cầu ăn uống đi qua dữ liệu có cấu trúc, planner và bước kiểm tra; sau đó cho thấy Admin kiểm soát dữ liệu đầu vào. Không cần demo mọi nút.

## Chuẩn bị trước buổi báo cáo

- Chạy frontend, backend và PostgreSQL; `/health/live` và `/health/ready` trả `200`.
- User demo có hồ sơ hoàn chỉnh, một thực đơn 1 ngày đã lưu và không có dữ liệu cá nhân thật.
- Super Admin demo chỉ dùng dữ liệu minh họa; tab Admin mở sẵn ở dashboard.
- Chuẩn bị trước một link shopping list còn hạn; thu hồi sau buổi demo.
- Mở `docs/assets/guides/` làm phương án ảnh tĩnh.
- Không để password manager, `.env`, terminal có secret, URL chứa token hoặc log AI chi tiết trên màn hình.

## Luồng User — 4 đến 5 phút

### 1. Dashboard và hồ sơ — 45 giây

1. Mở **Tổng quan**, chỉ vào calo mục tiêu và ngân sách/ngày.
2. Mở **Hồ sơ**, cho thấy thông tin cơ thể, preview BMR/TDEE/macro và danh sách nguyên liệu loại trừ.
3. Nói: “Calo mục tiêu được backend tính lại; dị ứng và không thích đều trở thành nguyên liệu bị loại khỏi candidate.”

**Kết quả mong đợi:** không có banner “Hoàn thiện hồ sơ”; preview dinh dưỡng hiển thị.

### 2. Tạo thực đơn — 70 giây

1. Mở **Tạo thực đơn**; chọn 1 ngày, 3 bữa và ngân sách tổng phù hợp.
2. Nếu AI sẵn sàng, nhập “1 ngày, 3 bữa, ngân sách 120 nghìn, ưu tiên giàu đạm” rồi chọn **Phân tích yêu cầu**.
3. Kiểm tra lại các trường; nhấn **Sinh thực đơn**.
4. Nói: “AI chỉ điền form. CP-SAT và Constraint Checker mới tạo và kiểm tra thực đơn.”

**Kết quả mong đợi:** trang kết quả có 1 món sáng; trưa/tối mỗi bữa có 3 món đúng vai trò; tổng chi phí không vượt ngân sách.

### 3. Kết quả, đổi món và lưu — 75 giây

1. Chỉ vào tổng chi phí, calo, la bàn dinh dưỡng và cảnh báo solver nếu có.
2. Chọn **Tạo lại** hoặc mở **Đổi món** ở một món; giải thích phương án đổi phải được kiểm tra lại toàn plan.
3. Chọn **Phân tích thực đơn** nếu AI hoạt động; nói rõ phần này diễn giải số liệu đã kiểm tra.
4. Đặt tên rồi chọn **Lưu thực đơn**; mở **Lịch sử**.

**Kết quả mong đợi:** menu được lưu theo tài khoản và mở lại được.

### 4. Đi chợ và chia sẻ — 60 giây

1. Mở **Đi chợ**, chọn thực đơn và phạm vi toàn bộ/từng ngày.
2. Tích một nguyên liệu; bộ đếm đã mua tăng.
3. Chọn **Chia sẻ**, nêu hạn 7 ngày nhưng không chiếu token thật.
4. Chuyển sang public page đã chuẩn bị; tích trạng thái để cho thấy dữ liệu dùng chung.

**Kết quả mong đợi:** public page không yêu cầu đăng nhập, chỉ hiển thị phạm vi đã chia sẻ và cho phép tích đã mua.

### 5. Menuto — 30 giây

Mở **Trợ lý Menuto**, chỉ vào danh sách cuộc hội thoại, giới hạn 10 cuộc × 20 câu và thông báo lưu tối đa 30 ngày. Không cần chờ một câu trả lời dài trong demo.

## Luồng Admin — 2 đến 3 phút

### 1. Dashboard và phân quyền — 40 giây

1. Mở **Tổng quan quản trị**, chỉ số món planner-ready và “Việc cần xử lý”.
2. Nêu: Data Editor quản dữ liệu thực phẩm; Super Admin mới quản user và AI.

### 2. Dữ liệu, thẻ và Quality — 55 giây

1. Mở **Món thành phần**; chỉ vào công thức, tổng dinh dưỡng/chi phí và badge thiếu dữ liệu.
2. Mở **Thẻ**; cho thấy thẻ món và thẻ nguyên liệu là hai danh mục riêng.
3. Mở **Chất lượng dữ liệu**; nêu dữ liệu thiếu không vào `v_dish_candidates`.

### 3. Import và AI Provider — 45 giây

1. Mở **Lịch sử import**; giải thích luồng tải mẫu → preview → xử lý conflict → commit.
2. Mở **AI & LLM Provider**; chỉ trạng thái test/active và log 30 ngày. Không mở log chi tiết hoặc trường API key.

## Phương án dự phòng

| Tình huống | Cách xử lý trong demo |
| --- | --- |
| AI tắt/lỗi/chậm | Bỏ bước parse/phân tích; dùng form có cấu trúc và menu đã lưu. Nói đây là fallback theo thiết kế. |
| Planner trả `infeasible` | Dùng kết quả để chứng minh hệ thống không trả menu sai; đọc lý do rồi tăng ngân sách hoặc giảm số ngày. |
| Không có dữ liệu món phù hợp | Mở Admin Quality/Dishes và giải thích candidate bị loại do thiếu loại món hoặc dữ liệu. |
| Link public hết hạn | Dùng ảnh `../assets/guides/04-danh-sach-mua-sam-chia-se/public-list-mobile.png`; không tạo link mới trước hội đồng nếu không cần. |
| Mạng/ứng dụng chậm | Dùng menu đã lưu và bộ screenshot; tiếp tục lời trình bày theo kết quả mong đợi. |
| Tài khoản bị khóa/sai role | Chuyển sang tài khoản demo đã kiểm tra; không sửa role trực tiếp trên sân khấu. |

## Lời nói không được vượt quá bằng chứng

- Không gọi kết quả là tư vấn hoặc chẩn đoán y khoa.
- Không nói AI tính giá, calo, lọc dị ứng, kiểm tra ngân sách hay xác nhận plan hợp lệ.
- Không nói link public là chỉ xem: người có link có thể tích trạng thái đã mua.
- Không nói mọi test đều tự động qua browser: browser E2E/axe hiện vẫn là kiểm tra thủ công.
- Có thể nói lịch sử Menuto không hoạt động quá 30 ngày được backend dọn; đây là hành vi đã triển khai hiện tại.

