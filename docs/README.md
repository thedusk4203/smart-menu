# Smart Menu — Bộ tài liệu đồ án

Đây là bộ tài liệu chuẩn đi cùng mã nguồn Smart Menu, được đối chiếu với working tree ngày **13/07/2026**. Tài liệu phục vụ hai mục đích: chuẩn bị báo cáo đồ án dài hơn 20 phút và giúp người không chuyên kỹ thuật tự thao tác, quan sát kết quả rồi kiểm tra mức độ hiểu.

## Bắt đầu nhanh

- [Dàn ý 22 slide](presentation/slide-outline.md): nội dung trên slide, nguồn hình, lời nói và thời lượng.
- [Kịch bản demo 6–8 phút](presentation/demo-script.md): hành trình User/Admin và phương án dự phòng.
- [Phụ lục kỹ thuật](presentation/technical-appendix.md) và [code walkthrough](presentation/code-walkthrough.md): nội dung dự phòng khi hội đồng hỏi về code.
- [Mục lục 9 hướng dẫn sử dụng](guides/README.md): hướng dẫn tiếng Việt, ảnh minh họa và bài kiểm tra ở cuối từng bài.
- [Tổng quan kỹ thuật](technical-overview.md): kiến trúc, dữ liệu, planner, AI và phân quyền.
- [Handbook kỹ thuật cho developer](code/README.md): architecture, code map, API đầy đủ, database, ADR, test và vận hành.
- [Trạng thái sẵn sàng trình diễn](launch-readiness.md): bằng chứng kiểm thử mới nhất và giới hạn còn lại.

## Tài liệu nguồn trong repository

- [README dự án](../README.md): cách chạy local và Docker Compose.
- [Mô tả sản phẩm](../PRODUCT.md): định hướng sản phẩm và trải nghiệm.
- [Backend README](../backend/README.md): cấu trúc API và lệnh phát triển backend.
- [Hướng dẫn migrations](../data/migrations/README.md): cách áp dụng thay đổi database.
- [AGENTS.md](../AGENTS.md): quy ước làm việc trong repository.
- [ADR retrospective](code/adr/README.md): các quyết định kiến trúc và hệ quả bảo trì hiện tại.

## Phạm vi và cách đọc kết quả

Smart Menu lập thực đơn từ dữ liệu món, công thức, giá và dinh dưỡng có cấu trúc. AI chỉ hỗ trợ **phân tích câu tiếng Việt, giải thích kết quả và xếp hạng gợi ý**; chi phí, dinh dưỡng, lọc dị ứng/nguyên liệu loại trừ, tuân thủ ngân sách và tính hợp lệ cuối cùng được hệ thống kiểm tra.

Giá và dinh dưỡng là số liệu tham khảo cho lập kế hoạch ăn uống, không thay thế tư vấn y tế hoặc phác đồ điều trị. Ảnh trong `docs/assets/guides/` chỉ dùng tài khoản và dữ liệu minh họa; không chứa mật khẩu, access token, API key hay dữ liệu cá nhân thật.
