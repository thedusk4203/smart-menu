# Dàn ý 22 slide báo cáo đồ án Smart Menu

**Thời lượng mục tiêu:** 18–20 phút trình bày + 6–8 phút demo + hỏi đáp.  
**Placeholder cần thay:** `[Tên trường]`, `[Tên môn]`, `[Giảng viên]`, `[Nhóm]`, `[Thành viên]`.

| # | Nội dung chính trên slide | Nguồn hình/visual | Speaker notes | Thời lượng |
| --- | --- | --- | --- | --- |
| 1 | **Smart Menu** — lập thực đơn theo ngân sách và dinh dưỡng; tên nhóm/môn/trường | Logo chữ + ảnh `../assets/guides/01-bat-dau-ho-so/dashboard.png` | Mở bằng một câu: người dùng không chỉ cần “món ngon” mà cần một kế hoạch có thể kiểm tra. | 0:35 |
| 2 | **Vấn đề** — mất thời gian chọn món; khó kiểm soát tổng chi phí; khó cân đối dinh dưỡng nhiều ngày | Ba biểu tượng: thời gian, ví tiền, dinh dưỡng | Phân biệt “gợi ý món” với “lập kế hoạch có ràng buộc”. | 1:00 |
| 3 | **Người dùng** — User; Biên tập dữ liệu; Quản trị hệ thống | Sơ đồ 3 persona | User lập kế hoạch; Data Editor giữ dữ liệu sạch; Super Admin quản tài khoản và AI. | 0:55 |
| 4 | **Phạm vi** — 1–7 ngày, 2–3 bữa/ngày, ngân sách, dị ứng/không thích, shopping list; ngoài phạm vi: chẩn đoán y khoa, giá realtime | Bảng “Có / Không” | Nêu giới hạn sớm để tránh hiểu sản phẩm là bác sĩ hoặc hệ thống mua hàng. | 1:00 |
| 5 | **Giải pháp** — Hồ sơ → yêu cầu → planner → kiểm chứng → lưu/đi chợ | Flow 5 bước từ `../technical-overview.md` | Giá trị cốt lõi là kết quả có nguồn dữ liệu và bước kiểm tra độc lập. | 0:55 |
| 6 | **Bản đồ tính năng** — auth Google/email, profile, catalog, planner, history, share, Menuto; admin user/data/tag/quality/import/AI | Feature map hai nhánh User/Admin | Chỉ ra tính năng mới: 4 role, tag theo loại, public share theo ngày và retention chat thật. | 1:05 |
| 7 | **Demo trực tiếp 6–8 phút** — User journey rồi Admin journey | Dùng [demo-script.md](demo-script.md) | Chuyển sang demo. Nếu demo chậm, dùng ảnh trong `../assets/guides/`. | 0:20 + demo |
| 8 | **Kiến trúc tổng thể** — React/TypeScript, FastAPI modular monolith, PostgreSQL, LLM tùy chọn | System context trong `../technical-overview.md` | Giải thích lý do modular monolith phù hợp quy mô đồ án và vẫn tách module rõ. | 1:10 |
| 9 | **Mô hình dữ liệu** — User/Profile/Exclusion; Ingredient/Nutrition/Price; Dish/Recipe; Plan/Share; Conversation | ERD trong `../technical-overview.md` | Nhấn mạnh snapshot giúp lịch sử ổn định khi dữ liệu món thay đổi. | 1:05 |
| 10 | **Dữ liệu đầu vào planner** — chỉ món active, đủ công thức, giá, dinh dưỡng và nguyên liệu hợp lệ | Ảnh `../assets/guides/07-admin-du-lieu-thuc-pham/dishes.png` | `v_dish_candidates` là cổng chất lượng chung cho catalog User và planner. | 0:55 |
| 11 | **CP-SAT planner** — tiền kiểm; nghiệm cứng; tối ưu dinh dưỡng; tối ưu đa dạng/ưu tiên/chi phí | Pipeline trong `../technical-overview.md` | Không chọn từng bữa theo greedy; solver nhìn toàn bộ số ngày và ngân sách cùng lúc. | 1:25 |
| 12 | **Cấu trúc bữa và ràng buộc** — sáng 1 món; trưa/tối = tinh bột + mặn + rau/canh; ngân sách/dị ứng/dữ liệu và nutrition band là cứng | Bảng hard/soft constraints | Target chính xác vẫn là mục tiêu tối ưu; vượt hard band, ngân sách hoặc dị ứng thì không được trả plan hợp lệ. | 1:15 |
| 13 | **Tạo lại và đổi món** — signature khác; AI xếp hạng gợi ý; hệ thống kiểm tra lại toàn plan | Ảnh `../assets/guides/03-tao-quan-ly-thuc-don/menu-result.png` | “Đổi món” không thay trực tiếp; chỉ phương án qua Constraint Checker mới được chọn. | 0:55 |
| 14 | **Ranh giới AI** — parse/giải thích/xếp hạng/hội thoại; không tính giá, macro hay quyết định hợp lệ | Sơ đồ AI boundary | Câu chốt: AI xử lý ngôn ngữ; backend và dữ liệu có cấu trúc xử lý sự thật. | 1:10 |
| 15 | **Quản trị và chất lượng dữ liệu** — 4 role, Quality, typed tag, preview/import, export | `../assets/guides/06-admin-tong-quan-nguoi-dung/dashboard.png` và `../assets/guides/08-admin-chat-luong-import/imports.png` | Preview không ghi dữ liệu; conflict cần chọn bỏ qua/thay thế từng dòng. | 1:05 |
| 16 | **Shopping list & public sharing** — theo toàn plan/từng ngày, trạng thái đã mua đồng bộ, hạn 7 ngày, thu hồi | `../assets/guides/04-danh-sach-mua-sam-chia-se/public-list-mobile.png` | Người có link có quyền tích đã mua; link phải được coi như thông tin nhạy cảm. | 0:55 |
| 17 | **Bảo mật và riêng tư** — hash mật khẩu, verify Google token, ownership/role, env secret, log/retention | Shield + ma trận quyền | Conversation và request log đều 30 ngày nhưng là hai dữ liệu khác nhau; không chiếu log chi tiết. | 1:00 |
| 18 | **Accessibility & responsive** — keyboard/focus, skip link, trạng thái rỗng/lỗi, public page 390×844; ngăn Menuto mobile còn cắt nhãn dài | `../assets/guides/05-tro-ly-menuto/assistant-mobile.png` | Nêu kết quả kiểm tra thật: luồng chọn cuộc hoạt động nhưng responsive chưa hoàn thiện; ảnh là bằng chứng của giới hạn, không chỉ là hình trang trí. | 0:50 |
| 19 | **Kiểm thử và bằng chứng** — 217 backend tests, coverage 67,63%; 17 frontend tests; Ruff, TypeScript, ESLint, release guard và build pass ngày 20/07/2026 | Bảng từ `../launch-readiness.md` | Nêu mục tiêu 70% chưa đạt và browser chưa được chạy lại; không biến “pass unit test” thành khẳng định không còn lỗi. | 1:05 |
| 20 | **Triển khai** — Docker Compose: frontend/nginx, backend, PostgreSQL; health live/ready; seed opt-in | Deployment diagram | Backend/database không cần bind công khai; secret và demo seed cấu hình bằng env. | 0:55 |
| 21 | **Giới hạn & roadmap** — E2E/axe CI, audit security, dữ liệu giá rộng hơn, quan sát latency AI | Timeline Now/Next/Later | Giới hạn hiện tại là việc cần làm tiếp, không che giấu trong phần hỏi đáp. | 0:55 |
| 22 | **Kết luận** — một hệ thống lập kế hoạch có thể kiểm chứng; Q&A | Ba từ khóa: Dữ liệu · Ràng buộc · Kiểm chứng | Chốt: “AI giúp hiểu và giải thích; hệ thống chịu trách nhiệm tính và kiểm tra.” | 0:40 |

## Câu chốt đề xuất

> Smart Menu không để AI tự quyết một thực đơn. AI hỗ trợ ngôn ngữ; chi phí, dinh dưỡng, dị ứng, ngân sách và tính hợp lệ được xác nhận bằng dữ liệu có cấu trúc, CP-SAT và Constraint Checker độc lập.

## Checklist biên tập slide

1. Thay toàn bộ placeholder trước ngày bảo vệ.
2. Mỗi slide chỉ giữ 3–5 ý; chuyển speaker notes vào phần ghi chú của PowerPoint.
3. Không đưa URL chia sẻ, mật khẩu, API key, access token hoặc log request/response vào slide.
4. Nếu code thay đổi, chạy lại checklist trong `../launch-readiness.md` và cập nhật slide 19.

## Phụ lục cho phần hỏi đáp kỹ thuật

Không thêm vào 22 slide chính. Khi cần, dùng [technical appendix](technical-appendix.md) và [code walkthrough](code-walkthrough.md) để mở source/contract theo một luồng cụ thể.
