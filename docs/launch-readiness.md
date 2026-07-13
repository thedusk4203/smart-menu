# Trạng thái sẵn sàng trình diễn

**Kết luận ngày 13/07/2026:** phù hợp demo đồ án/local có kiểm soát; chưa được đánh giá như một dịch vụ Internet công cộng.

## Bằng chứng vừa chạy

| Kiểm tra | Kết quả |
| --- | --- |
| Backend `pytest -q` | **189 passed**, 3 cảnh báo không làm test fail |
| TypeScript `tsc -b` | Pass |
| ESLint | Pass |
| Release guard | Pass |
| Vite production build | Pass, 1.666 module |
| Bundle chính | 337,10 kB; gzip 108,16 kB |
| Kiểm tra browser thủ công | Các luồng User/Admin, planner, shopping list, chia sẻ mobile và lịch sử Menuto chạy được; phát hiện giới hạn responsive ở ngăn lịch sử Menuto 390 px |

Ba cảnh báo pytest gồm hai cảnh báo Pydantic về `class Config` cũ và một cảnh báo không ghi được `.pytest_cache`; không có test thất bại.

## Trạng thái đã xác minh thủ công

- Đăng nhập email và nút Google khi có cấu hình.
- Hồ sơ hoàn chỉnh, preview nhu cầu dinh dưỡng và nguyên liệu loại trừ.
- Tạo thực đơn khả thi; kết quả CP-SAT có cảnh báo minh bạch nếu hết thời gian tối ưu nhưng đã có nghiệm hợp lệ.
- Lưu/lịch sử, shopping list, đánh dấu đã mua, link public 390×844 và hạn 7 ngày.
- Menuto hiển thị lịch sử desktop/mobile; retention 30 ngày đã có cleanup backend.
- Dashboard quản trị, phân quyền, dữ liệu nguyên liệu/món/tag, Quality, import và AI provider/log.

## Giới hạn trước khi phát hành công cộng

- Chưa có browser E2E/axe tự động trong CI; kiểm tra browser hiện là thủ công.
- Chưa có audit dependency và penetration test độc lập.
- Giá là snapshot tham khảo, không phải giá realtime tại mọi địa điểm.
- Kết quả dinh dưỡng không thay thế tư vấn y tế.
- Cần theo dõi timeout của provider local/remote; planner vẫn hoạt động khi AI tắt.
- Ngăn lịch sử Menuto trên viewport 390 px có thể cắt một số nhãn dài ở mép phải; cần sửa responsive trước khi coi trải nghiệm mobile là hoàn thiện.

## Checklist trước buổi bảo vệ

1. Dùng `.env` riêng cho demo; không chiếu secret, mật khẩu, token chia sẻ hoặc API key.
2. Chạy `docker compose --profile demo up --build -d` hoặc local backend/frontend theo README.
3. Kiểm tra `/health/live` và `/health/ready` trả `200`.
4. Chuẩn bị User và Super Admin chỉ chứa dữ liệu minh họa.
5. Tạo trước một thực đơn đã lưu và một link public; thu hồi link sau buổi demo.
6. Chạy lại pytest, TypeScript, ESLint, release guard và build nếu code thay đổi; cập nhật số liệu slide 19.
