# Trạng thái sẵn sàng trình diễn

**Kết luận tự động ngày 20/07/2026:** refactor hiện vượt các quality gate đã cấu hình và phù hợp demo/local có kiểm soát; chưa được đánh giá như một dịch vụ Internet công cộng.

## Bằng chứng vừa chạy

| Kiểm tra | Kết quả |
| --- | --- |
| Backend `pytest -q --cov` | **217 passed**, coverage **67,63%**, vượt gate 65% |
| Backend Ruff | Pass |
| TypeScript `tsc -b` | Pass |
| ESLint | Pass |
| Release guard | Pass |
| Frontend Vitest coverage | **17 passed**; `apiClient.ts`: 95% statement, 84% branch, 82,6% function, 100% line |
| Vite production build | Pass, 2.753 module |
| Bundle chính | 342,50 kB; gzip 109,62 kB |
| Chunk Assistant | 246,46 kB; gzip 78,35 kB |
| Kiểm tra browser thủ công | Chưa chạy lại trong lượt xác minh refactor này; bằng chứng browser phía dưới là kết quả cũ cần refresh trước demo |

Một cảnh báo pytest do sandbox không ghi được `.pytest_cache`; không có test thất bại. Kế hoạch đặt mục tiêu coverage 70%, nhưng cấu hình hiện tại mới `fail_under=65` và kết quả thực tế là 67,63%.

## Trạng thái đã xác minh thủ công trước refactor

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
