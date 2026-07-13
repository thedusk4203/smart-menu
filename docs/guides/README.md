# Hướng dẫn sử dụng Smart Menu

Chín bài dưới đây được viết cho người không chuyên kỹ thuật. Nên đọc theo thứ tự User trước, Admin sau. Mỗi bài có đúng 5 câu kiểm tra; đáp án, giải thích và thang điểm luôn nằm ở phần cuối cùng để người đọc tự làm trước khi xem.

## Hành trình User

1. [Đăng nhập, dashboard và hồ sơ](01-bat-dau-va-ho-so.md)
2. [Nguyên liệu, món ăn và chi tiết món](02-nguyen-lieu-va-mon-an.md)
3. [Tạo, tạo lại, phân tích, đổi, lưu và xem thực đơn](03-tao-va-quan-ly-thuc-don.md)
4. [Danh sách đi chợ và chia sẻ công khai](04-danh-sach-mua-sam-va-chia-se.md)
5. [Trợ lý Menuto và lịch sử hội thoại](05-tro-ly-menuto.md)

## Hành trình Admin

6. [Tổng quan quản trị và người dùng](06-admin-tong-quan-va-nguoi-dung.md)
7. [Nguyên liệu, món thành phần và thẻ](07-admin-du-lieu-thuc-pham.md)
8. [Chất lượng dữ liệu và import](08-admin-chat-luong-va-import.md)
9. [AI provider và nhật ký](09-admin-ai.md)

## Thuật ngữ cần biết

- **Món thành phần (dish):** một công thức chuẩn. Bữa trưa/tối được ghép từ món tinh bột, món mặn và món rau hoặc canh.
- **Planner-ready:** món đang hoạt động, có công thức, giá và dinh dưỡng đầy đủ để planner sử dụng.
- **Planner:** bộ máy CP-SAT chọn món cho toàn bộ số ngày theo các ràng buộc.
- **Constraint Checker:** bước kiểm tra độc lập sau planner để xác nhận ngân sách, dị ứng, cấu trúc bữa và dữ liệu.
- **Preview import:** đọc và kiểm tra file nhưng chưa ghi thay đổi vào dữ liệu đang dùng.
- **Provider:** dịch vụ/mô hình ngôn ngữ cung cấp chức năng AI.

> Ranh giới chung: AI chỉ phân tích câu tiếng Việt, giải thích và xếp hạng gợi ý. Chi phí, dinh dưỡng, lọc dị ứng/nguyên liệu loại trừ, tuân thủ ngân sách và tính hợp lệ của thực đơn được hệ thống kiểm tra.

