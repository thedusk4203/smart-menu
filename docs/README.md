# Smart Menu — Tài liệu hiện hành

Đây là bộ tài liệu chuẩn đi cùng mã nguồn Smart Menu, được đối chiếu gần nhất với working tree ngày **22/07/2026**. Cấu trúc được giữ gọn theo hai tầng: bộ Dusk giải thích sâu nhưng dễ đọc và handbook dành cho bảo trì kỹ thuật.

## Bắt đầu nhanh

- [Tổng quan kỹ thuật](technical-overview.md): kiến trúc, dữ liệu, planner, AI và phân quyền.
- [Dusk Docs](dusk/README.md): 16 bài học dễ hiểu về Meal Plan V3, Nutrition, AI, Shopping List và inventory liên quan; mỗi bài có quiz.
- [Handbook kỹ thuật cho developer](code/README.md): architecture, code map, API/ADR, security, testing và operations.

## Tài liệu nguồn trong repository

- [README dự án](../README.md): cách chạy local và Docker Compose.
- [Mô tả sản phẩm](../PRODUCT.md): định hướng sản phẩm và trải nghiệm.
- [Backend README](../backend/README.md): cấu trúc API và lệnh phát triển backend.
- [Hướng dẫn migrations](../data/migrations/README.md): cách áp dụng thay đổi database.
- [AGENTS.md](../AGENTS.md): quy ước làm việc trong repository.
- [ADR retrospective](code/adr/README.md): các quyết định kiến trúc và hệ quả bảo trì hiện tại.

## Phạm vi và cách đọc kết quả

Smart Menu lập thực đơn từ dữ liệu món, công thức, giá và dinh dưỡng có cấu trúc. AI chỉ hỗ trợ **phân tích câu tiếng Việt, giải thích kết quả và xếp hạng gợi ý**; chi phí, dinh dưỡng, lọc dị ứng/nguyên liệu loại trừ, tuân thủ ngân sách và tính hợp lệ cuối cùng được hệ thống kiểm tra.

Giá và dinh dưỡng là số liệu tham khảo cho lập kế hoạch ăn uống, không thay thế tư vấn y tế hoặc phác đồ điều trị. Số liệu test/OpenAPI/database trong tài liệu là baseline có ngày kiểm chứng, không phải hằng số.
