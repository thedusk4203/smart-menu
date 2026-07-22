# Trạng thái sẵn sàng trình diễn

**Kết luận tự động ngày 22/07/2026:** working tree hiện vượt các quality gate đã cấu hình và phù hợp demo/local có kiểm soát; chưa được đánh giá như một dịch vụ Internet công cộng.

## Bằng chứng vừa chạy

| Kiểm tra | Kết quả |
| --- | --- |
| Backend `pytest -q --cov` | **232 passed**, coverage **67,54%**, vượt gate 65% |
| Backend Ruff | Pass |
| TypeScript `tsc -b` | Pass |
| ESLint | Pass |
| Release guard | Pass |
| Frontend Vitest coverage | **25 passed**; `apiClient.ts`: 93,15% statement, 87,06% branch, 86,66% function, 97,58% line |
| Vite production build | Pass, 2.758 module |
| Bundle chính | 350,33 kB; gzip 112,10 kB |
| Chunk Assistant | 249,21 kB; gzip 79,24 kB |
| Kiểm tra browser thủ công | Chưa chạy lại trong lượt xác minh refactor này; bằng chứng browser phía dưới là kết quả cũ cần refresh trước demo |

Một cảnh báo pytest do `.pytest_cache` đã tồn tại ở trạng thái không ghi được; không có test thất bại. Kế hoạch đặt mục tiêu coverage 70%, nhưng cấu hình hiện tại mới `fail_under=65` và kết quả thực tế là 67,54%.

## Trạng thái đã xác minh thủ công trước refactor

- Đăng nhập email và nút Google khi có cấu hình.
- Hồ sơ hoàn chỉnh, preview nhu cầu dinh dưỡng và nguyên liệu loại trừ.
- Tạo thực đơn khả thi; kết quả CP-SAT có cảnh báo minh bạch nếu hết thời gian tối ưu nhưng đã có nghiệm hợp lệ.
- Lưu/lịch sử, shopping list, đánh dấu đã mua, link public 390×844 và hạn 7 ngày.
- Menuto hiển thị lịch sử desktop/mobile; cleanup 30 ngày đã có, nhưng cần chuyển vòng background sang `ai_state_engine` trước khi tách AI state sang database vật lý khác.
- Dashboard quản trị, phân quyền, dữ liệu nguyên liệu/món/tag, Quality, import và AI provider/log.

## Giới hạn trước khi phát hành công cộng

- Chưa có browser E2E/axe tự động trong CI; kiểm tra browser hiện là thủ công.
- Chưa có audit dependency và penetration test độc lập.
- Giá là snapshot tham khảo, không phải giá realtime tại mọi địa điểm.
- Kết quả dinh dưỡng không thay thế tư vấn y tế.
- Chế độ health reference cần provider có native web-search citation hợp lệ; fallback phải được ghi rõ là chưa kiểm chứng web theo thời gian thực.
- Cần theo dõi timeout của provider local/remote; planner vẫn hoạt động khi AI tắt.
- Ngăn lịch sử Menuto trên viewport 390 px có thể cắt một số nhãn dài ở mép phải; cần sửa responsive trước khi coi trải nghiệm mobile là hoàn thiện.

## Checklist trước buổi bảo vệ

1. Dùng `.env` riêng cho demo; không chiếu secret, mật khẩu, token chia sẻ hoặc API key.
2. Chạy `docker compose --profile demo up --build -d` hoặc local backend/frontend theo README.
3. Kiểm tra `/health/live` và `/health/ready` trả `200`.
4. Chuẩn bị User và Super Admin chỉ chứa dữ liệu minh họa.
5. Tạo trước một thực đơn đã lưu và một link public; thu hồi link sau buổi demo.
6. Chạy lại pytest, TypeScript, ESLint, release guard và build nếu code thay đổi; cập nhật số liệu slide 19.
