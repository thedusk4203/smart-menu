# Smart Menu - Đặc tả yêu cầu phần mềm (SRS)

## 1. Giới thiệu

### 1.1. Mục đích tài liệu

Tài liệu này mô tả yêu cầu phần mềm cho Smart Menu, một ứng dụng web hỗ trợ người dùng lập thực đơn theo ngân sách tuần, mục tiêu dinh dưỡng cơ bản, sở thích cá nhân và các ràng buộc như dị ứng hoặc thực phẩm không sử dụng.

### 1.2. Bối cảnh và vấn đề

Người dùng thường gặp khó khăn khi phải quyết định ăn gì trong nhiều ngày liên tiếp, vừa đảm bảo chi phí, vừa giữ mức dinh dưỡng tương đối hợp lý. Các vấn đề chính gồm:

- Không biết nên ăn gì trong tuần.
- Mất nhiều thời gian suy nghĩ và lập thực đơn.
- Khó kiểm soát ngân sách ăn uống.
- Mua nguyên liệu không có kế hoạch, dễ thừa hoặc lãng phí.
- Lặp lại quá nhiều món quen thuộc.
- Không biết ước lượng calo và các chỉ số dinh dưỡng cơ bản.

Smart Menu giải quyết bài toán này bằng cách kết hợp nhập liệu có cấu trúc, tính toán chi phí và dinh dưỡng theo dữ liệu, thuật toán lập thực đơn theo ràng buộc, và AI hỗ trợ diễn giải bằng tiếng Việt.

### 1.3. Phạm vi

Tập trung vào người trưởng thành không có bệnh lý đặc biệt.

Trong phạm vi:

- Đăng ký, đăng nhập, đăng xuất và phân quyền User/Admin.
- Quản lý hồ sơ người dùng phục vụ tính toán dinh dưỡng.
- Quản lý dữ liệu nguyên liệu, giá, dinh dưỡng, món ăn và công thức.
- Lập thực đơn theo chu kỳ 7 ngày. Hệ thống có thể mở rộng để cho phép chọn 1-7 ngày, nhưng MVP mặc định là 7 ngày.
- Hỗ trợ 2 hoặc 3 bữa/ngày theo hồ sơ hoặc yêu cầu.
- Ràng buộc ngân sách theo tuần.
- Tính toán calo, protein, fat và carb ở mức cơ bản.
- Lọc dị ứng và thực phẩm người dùng không sử dụng.
- Kiểm tra ràng buộc bằng logic deterministic.
- Sinh danh sách nguyên liệu cần mua.
- Lưu và xem lại lịch sử thực đơn.
- AI hỗ trợ hiểu yêu cầu tiếng Việt, chuyển thành JSON, giải thích thực đơn, gợi ý thay thế và diễn giải cảnh báo.

Ngoài phạm vi:

- Tư vấn y tế hoặc chế độ ăn điều trị bệnh.
- Tối ưu vi chất như vitamin, khoáng chất.
- Đảm bảo giá thực phẩm theo thời gian thực.
- Đặt hàng thực phẩm trực tiếp.
- Tối ưu cho gia đình nhiều thế hệ có nhu cầu y tế khác nhau.
- Để AI tự tính toán hoặc tự xác nhận kết quả cuối cùng.

### 1.4. Thuật ngữ

| Thuật ngữ | Ý nghĩa |
| --- | --- |
| SRS | Software Requirements Specification - Đặc tả yêu cầu phần mềm |
| AI | Trí tuệ nhân tạo |
| LLM | Mô hình ngôn ngữ lớn |
| BMR | Tỷ lệ trao đổi chất cơ bản |
| TDEE | Tổng năng lượng tiêu hao hằng ngày |
| Macro | Calo, protein, fat và carb |
| Heuristic planning | Lập kế hoạch bằng luật, điểm số và tối ưu gần đúng |
| Hard constraint | Ràng buộc cứng, bắt buộc không được vi phạm |
| Soft constraint | Ràng buộc mềm, dùng để chấm điểm và ưu tiên |
| Constraint Checker | Module kiểm tra ngân sách, dị ứng, số ngày, số bữa và dinh dưỡng |
| Price snapshot | Giá tham khảo được lưu tại một thời điểm thu thập |

## 2. Mô tả tổng quan hệ thống

### 2.1. Tổng quan sản phẩm

Smart Menu là ứng dụng web theo mô hình Modular Monolith. Người dùng tạo hồ sơ, nhập ngân sách và yêu cầu ăn uống, sau đó hệ thống tính nhu cầu dinh dưỡng, lọc món, sinh thực đơn, kiểm tra ràng buộc, tạo danh sách mua sắm và có thể dùng AI để giải thích kết quả đã được kiểm chứng.

AI không phải nguồn đúng sai của số liệu. Mọi giá tiền, calo và macro phải lấy từ dữ liệu có cấu trúc và module tính toán nội bộ.

### 2.2. Actors

| Actor | Mô tả | Quyền chính |
| --- | --- | --- |
| Guest | Người chưa đăng nhập | Xem giới thiệu, đăng ký, đăng nhập |
| User | Người dùng chính | Quản lý hồ sơ, tạo thực đơn, xem danh sách mua sắm, yêu cầu AI giải thích, lưu và dùng lại thực đơn |
| Admin | Người quản trị dữ liệu | Quản lý user, nguyên liệu, dinh dưỡng, giá, món ăn, công thức và kiểm tra chất lượng dữ liệu |
| AI Service | Dịch vụ LLM | Parse tiếng Việt, giải thích thực đơn, gợi ý thay thế, diễn giải cảnh báo |
| External Data Source | Nguồn dữ liệu bên ngoài | Cung cấp dữ liệu tham khảo về dinh dưỡng và giá thực phẩm |

### 2.3. User stories chính

- Là người dùng, tôi muốn nhập ngân sách tuần để thực đơn không vượt chi phí dự kiến.
- Là người dùng, tôi muốn nhập dị ứng và thực phẩm không ăn để hệ thống loại bỏ món không phù hợp.
- Là người dùng, tôi muốn xem calo và macro để biết thực đơn gần mục tiêu dinh dưỡng đến đâu.
- Là người dùng, tôi muốn có danh sách nguyên liệu cần mua để đi chợ dễ hơn.
- Là người dùng, tôi muốn AI giải thích vì sao hệ thống chọn các món trong thực đơn.
- Là Admin, tôi muốn quản lý dữ liệu nguyên liệu, giá, dinh dưỡng và món ăn để planner có dữ liệu đáng tin cậy.

### 2.4. Ràng buộc hệ thống

Ràng buộc nghiệp vụ:

- Người dùng phải đăng nhập để tạo, lưu và xem lịch sử thực đơn.
- Người dùng chỉ được truy cập dữ liệu thuộc tài khoản của mình.
- Chu kỳ mặc định của MVP là 7 ngày. Nếu cho phép chọn 1-7 ngày thì toàn bộ validation phải dùng đúng số ngày người dùng yêu cầu.
- Mỗi ngày phải có đúng số bữa theo hồ sơ hoặc request.
- Thực đơn hợp lệ không được chứa nguyên liệu dị ứng hoặc thực phẩm bị loại trừ.
- Nếu ngân sách là ràng buộc cứng, tổng chi phí không được vượt ngân sách.
- Khi không thể tạo thực đơn hợp lệ, hệ thống phải trả lý do rõ ràng và gợi ý điều chỉnh.

Ràng buộc kỹ thuật:

- Backend sử dụng Python FastAPI.
- Frontend sử dụng React, TypeScript và Tailwind CSS.
- Database sử dụng PostgreSQL.
- ORM sử dụng SQLModel hoặc SQLAlchemy-compatible pattern.
- Migration sử dụng Alembic.
- Backend đi theo Modular Monolith và Clean Architecture.
- Domain logic không phụ thuộc FastAPI, PostgreSQL, React hoặc SDK của AI provider.

Ràng buộc AI:

- AI không được tính giá món, tổng chi phí, calo, protein, fat hoặc carb.
- AI không được xác nhận thực đơn hợp lệ nếu chưa qua Constraint Checker.
- Output AI phải validate bằng schema trước khi dùng.
- Dữ liệu nhạy cảm gửi tới AI API phải được tối thiểu hóa.
- Nội dung AI chỉ mang tính hỗ trợ, không phải tư vấn y tế.

## 3. Yêu cầu chức năng

### 3.1. Tài khoản và phân quyền

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-ACC-01 | Guest có thể đăng ký bằng email và mật khẩu. | Cao | Email không trùng, mật khẩu hợp lệ, mật khẩu được hash trước khi lưu. |
| FR-ACC-02 | User có thể đăng nhập. | Cao | Thông tin hợp lệ tạo session hoặc token xác thực. |
| FR-ACC-03 | User có thể đăng xuất. | Cao | Session/token không còn dùng được sau khi đăng xuất. |
| FR-ACC-04 | Hệ thống hỗ trợ role User và Admin. | Trung bình | Route Admin từ chối user không có quyền Admin. |
| FR-ACC-05 | User có thể xem và cập nhật thông tin tài khoản. | Trung bình | Dữ liệu cập nhật được validate và lưu thành công. |

### 3.2. Hồ sơ người dùng

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-PRO-01 | User có thể tạo hồ sơ cá nhân. | Cao | Hồ sơ lưu tuổi, giới tính, chiều cao, cân nặng, mức vận động, mục tiêu, số bữa/ngày, ngân sách tuần, dị ứng và thực phẩm loại trừ. |
| FR-PRO-02 | User có thể cập nhật hồ sơ. | Cao | Hồ sơ mới được dùng cho lần tạo thực đơn tiếp theo. |
| FR-PRO-03 | Hệ thống tính nhu cầu dinh dưỡng cơ bản. | Cao | Trả về mục tiêu calo và macro/ngày từ dữ liệu hồ sơ. |
| FR-PRO-04 | User có thể quản lý dị ứng và thực phẩm không sử dụng. | Cao | Planner loại bỏ nguyên liệu tương ứng. |

### 3.3. Nguyên liệu và dữ liệu dinh dưỡng

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-ING-01 | User/Admin có thể xem danh sách nguyên liệu đang hoạt động. | Cao | Danh sách hỗ trợ tìm kiếm, lọc và phân trang. |
| FR-ING-02 | Admin có thể thêm nguyên liệu. | Cao | Validate trường bắt buộc và tên trùng. |
| FR-ING-03 | Admin có thể cập nhật giá và metadata nguyên liệu. | Cao | Dữ liệu mới được dùng cho tính toán sau đó. |
| FR-ING-04 | Admin có thể vô hiệu hóa nguyên liệu. | Trung bình | Nguyên liệu bị vô hiệu hóa không xuất hiện trong thực đơn mới. |
| FR-ING-05 | Hệ thống chuẩn hóa tên và đơn vị nguyên liệu. | Cao | Tính toán dùng đơn vị và tên thống nhất. |

### 3.4. Món ăn và công thức

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-MEAL-01 | User/Admin có thể xem danh sách món ăn. | Cao | Danh sách hỗ trợ tìm kiếm và lọc theo loại bữa/tag. |
| FR-MEAL-02 | Admin có thể thêm món ăn và công thức. | Cao | Món phải có nguyên liệu và định lượng hợp lệ. |
| FR-MEAL-03 | Admin có thể cập nhật món ăn và công thức. | Cao | Công thức mới được dùng trong lần tính toán tiếp theo. |
| FR-MEAL-04 | Admin có thể vô hiệu hóa món ăn. | Trung bình | Món bị vô hiệu hóa không được dùng trong thực đơn mới. |
| FR-MEAL-05 | Hệ thống tính giá và dinh dưỡng món từ công thức. | Cao | Tổng tiền và macro khớp với định lượng nguyên liệu, giá và nutrition facts. |

### 3.5. Tạo thực đơn

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-PLAN-01 | User có thể nhập yêu cầu tạo thực đơn. | Cao | Request có ngân sách, số ngày, số bữa, mục tiêu, sở thích, dị ứng và thực phẩm loại trừ. |
| FR-PLAN-02 | Hệ thống tạo thực đơn. | Cao | Thực đơn có đủ số ngày và slot bữa ăn theo yêu cầu. |
| FR-PLAN-03 | Hệ thống kiểm tra ràng buộc thực đơn. | Cao | Validator kiểm tra ngân sách, dị ứng, thực phẩm loại trừ, số bữa, loại bữa và dữ liệu tính toán. |
| FR-PLAN-04 | Hệ thống hiển thị cảnh báo. | Cao | Cảnh báo giải thích vấn đề về ngân sách, dinh dưỡng, lặp món hoặc bất khả thi. |
| FR-PLAN-05 | User có thể tạo lại thực đơn. | Trung bình | Hệ thống sinh candidate khác và validate trước khi hiển thị. |
| FR-PLAN-06 | User có thể thay thế món ăn. | Trung bình | Món thay thế được lọc và validate trước khi chấp nhận. |

### 3.6. Danh sách nguyên liệu cần mua

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-SHOP-01 | Hệ thống sinh shopping list từ thực đơn. | Cao | Nguyên liệu được gộp theo tổng định lượng và đơn vị. |
| FR-SHOP-02 | Hệ thống hiển thị tổng chi phí dự kiến. | Cao | Tổng tiền dùng cùng price snapshot và quy đổi đơn vị với thực đơn. |

### 3.7. Lịch sử thực đơn

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-HIS-01 | User có thể lưu thực đơn đã tạo. | Trung bình | Thực đơn lưu kèm snapshot request, tổng tiền, macro và cảnh báo. |
| FR-HIS-02 | User có thể xem lịch sử thực đơn. | Trung bình | Danh sách chỉ hiển thị dữ liệu của user hiện tại. |
| FR-HIS-03 | User có thể xem chi tiết thực đơn cũ. | Trung bình | Chi tiết có món, nguyên liệu, chi phí, macro và cảnh báo. |
| FR-HIS-04 | User có thể tái sử dụng thực đơn cũ. | Thấp | Hệ thống có thể copy hoặc regenerate từ tham số cũ. |

### 3.8. Quản trị

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-ADM-01 | Admin có thể quản lý tài khoản user. | Trung bình | Admin có thể xem, đổi trạng thái và phân quyền. |
| FR-ADM-02 | Admin có thể quản lý nguyên liệu. | Cao | Admin có thể thêm, sửa, vô hiệu hóa và kiểm tra dữ liệu. |
| FR-ADM-03 | Admin có thể quản lý món ăn. | Cao | Admin có thể thêm, sửa, vô hiệu hóa và validate công thức. |
| FR-ADM-04 | Admin có thể chạy kiểm tra chất lượng dữ liệu. | Trung bình | Hệ thống báo nguyên liệu thiếu dinh dưỡng, thiếu giá, định lượng sai hoặc phụ thuộc đã inactive. |

### 3.9. AI

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
| --- | --- | --- | --- |
| FR-AI-01 | AI hiểu yêu cầu tiếng Việt tự nhiên. | Cao | Nhận diện được ngân sách, số ngày, số bữa, sở thích và thực phẩm loại trừ nếu có. |
| FR-AI-02 | AI chuyển yêu cầu thành JSON có cấu trúc. | Cao | JSON phải pass schema backend trước khi dùng. |
| FR-AI-03 | AI giải thích lý do chọn món. | Trung bình | Giải thích chỉ dựa trên validated plan, không bịa số liệu. |
| FR-AI-04 | AI gợi ý thay thế món ăn. | Trung bình | Gợi ý lấy từ candidate hợp lệ và phải validate lại. |
| FR-AI-05 | AI diễn giải cảnh báo. | Trung bình | Cảnh báo thân thiện nhưng không mâu thuẫn với kết quả kỹ thuật. |

## 4. Yêu cầu dữ liệu

### 4.1. Các thực thể chính

| Entity | Dữ liệu cần có |
| --- | --- |
| `users` | `id`, `email`, `password_hash`, `role`, `status`, `created_at`, `updated_at` |
| `user_profiles` | `id`, `user_id`, `age`, `gender`, `height_cm`, `weight_kg`, `activity_level`, `fitness_goal`, `meals_per_day`, `weekly_budget`, `allergies`, `excluded_ingredients` |
| `ingredients` | `id`, `name`, `food_group`, `unit`, `selling_unit`, `reference_price`, `source`, `last_price_updated_at`, `is_active` |
| `nutrition_facts` | `id`, `ingredient_id`, `calories_per_100g`, `protein_per_100g`, `fat_per_100g`, `carb_per_100g`, `source` |
| `meals` | `id`, `name`, `meal_type`, `cooking_method`, `serving_size`, `cooking_time_minutes`, `tags`, `is_active` |
| `meal_ingredients` | `id`, `meal_id`, `ingredient_id`, `quantity`, `unit` |
| `price_snapshots` | `id`, `ingredient_id`, `product_name`, `price`, `quantity`, `selling_unit`, `price_per_100g`, `collected_at`, `source` |
| `meal_plans` | `id`, `user_id`, `profile_snapshot`, `request_snapshot`, `total_cost`, `total_macros`, `warnings`, `created_at` |
| `shopping_lists` | `id`, `meal_plan_id`, `items`, `estimated_total_cost`, `created_at` |

Các trường tính sẵn như `estimated_price`, `calories`, `protein`, `fat`, `carb` có thể được cache để tăng hiệu năng, nhưng nguồn dữ liệu gốc vẫn là `meal_ingredients`, `ingredients`, `nutrition_facts` và `price_snapshots`.

### 4.2. Quy tắc chuẩn hóa dữ liệu

- Tên nguyên liệu phải được chuẩn hóa để tránh trùng lặp ngoài ý muốn.
- Dữ liệu dinh dưỡng nên lưu theo 100g.
- Dữ liệu giá nên quy đổi về `price_per_100g`.
- Định lượng trong công thức phải dùng đơn vị có thể quy đổi.
- Món thiếu giá hoặc dinh dưỡng không được dùng trong thực đơn hợp lệ.
- Lịch sử thực đơn phải lưu snapshot để kết quả cũ không bị thay đổi khi cập nhật giá hoặc công thức.
- Input từ user phải validate trước khi lưu hoặc đưa vào planner.

### 4.3. Dataset tối thiểu cho MVP

- 50-100 nguyên liệu phổ biến.
- 30-50 món ăn đơn giản.
- Dữ liệu dinh dưỡng theo 100g cho mỗi nguyên liệu.
- Price snapshot từ nguồn tham khảo công khai hoặc siêu thị online.
- 5-10 hồ sơ user mẫu.
- Một số thực đơn mẫu để kiểm thử.

## 5. Yêu cầu AI và thuật toán

### 5.1. Vai trò của AI

AI chỉ đảm nhiệm các tác vụ ngôn ngữ:

- Hiểu yêu cầu tiếng Việt.
- Trích xuất thông tin từ câu nhập tự nhiên.
- Chuyển ý định thành JSON có cấu trúc.
- Giải thích thực đơn đã validate bằng ngôn ngữ dễ hiểu.
- Gợi ý thay thế từ danh sách candidate hợp lệ.
- Diễn giải cảnh báo kỹ thuật thành câu thân thiện.

AI không phải thành phần quyết định tính đúng đắn cuối cùng.

### 5.2. Những việc AI không được làm

AI không được:

- Tính giá nguyên liệu, giá món, chi phí ngày hoặc chi phí tuần.
- Tính calo, protein, fat hoặc carb.
- Kiểm tra ngân sách.
- Kiểm tra dị ứng hoặc thực phẩm loại trừ.
- Xác nhận thực đơn hợp lệ nếu chưa qua Constraint Checker.
- Tự thêm món hoặc nguyên liệu không có trong database.
- Đưa ra tư vấn điều trị bệnh hoặc thay thế bác sĩ/chuyên gia dinh dưỡng.

### 5.3. Dish-level CP-SAT planning

Planner không dùng `meal_sets` hoặc bảng `dynamic_meals`. `dish` là đơn vị
quyết định nhỏ nhất và bữa được ghép trong lúc solve:

1. Nhận request có cấu trúc, validate `days=1..7` và `meals_per_day ∈ {2,3}`.
2. Tải hồ sơ, ngân sách, target, dị ứng, thực phẩm loại trừ và sở thích.
3. Đọc `v_dish_candidates`: chỉ dish active có recipe, mọi ingredient active,
   đủ nutrition và normalized price.
4. Tiền kiểm pool theo role, chi phí tối thiểu và khoảng macro có thể đạt;
   trả reason có mã/số liệu thay vì gọi solver vô ích.
5. CP-SAT chọn toàn bộ dish cho toàn bộ ngày cùng lúc, với budget là hard
   constraint toàn cục.
6. Tối ưu theo tầng: nutrition/ngày → đa dạng → preference, cooking method,
   ingredient reuse và cost.
7. Constraint Checker độc lập kiểm tra nghiệm; chỉ nghiệm đạt mới được trả.
8. Server tự tính metrics/warnings và snapshot V2; client không được gửi role,
   cost hoặc nutrition để lưu.

### 5.4. Ràng buộc cứng

| Mã | Ràng buộc | Mô tả |
| --- | --- | --- |
| HC-01 | Ngân sách | Tổng chi phí không được vượt ngân sách nếu ngân sách là hard constraint. |
| HC-02 | Dị ứng | Không món nào chứa nguyên liệu dị ứng. |
| HC-03 | Thực phẩm loại trừ | Không món nào chứa thực phẩm user không sử dụng. |
| HC-04 | Số ngày | Thực đơn có đúng số ngày yêu cầu. MVP mặc định là 7 ngày. |
| HC-05 | Số bữa | Mỗi ngày có đúng số bữa theo hồ sơ/request. |
| HC-06 | Loại bữa | Món sáng/trưa/tối phải phù hợp slot bữa ăn. |
| HC-07 | Dữ liệu hợp lệ | Món phải đủ dữ liệu giá và dinh dưỡng để tính toán. |
| HC-08 | Cấu trúc bữa | Breakfast đúng 1 `breakfast`; lunch/dinner đúng 1 `staple`, 1 `savory`, 1 `vegetable_side` **hoặc** `soup`. |
| HC-09 | Không trùng dish | Một dish không được xuất hiện hai lần trong cùng một bữa. |

### 5.5. Ràng buộc mềm

| Mã | Ràng buộc | Mô tả |
| --- | --- | --- |
| SC-01 | Gần mục tiêu calo | Tổng calo/ngày nên gần target. |
| SC-02 | Gần mục tiêu protein | Protein/ngày nên gần target, nhất là mục tiêu high-protein. |
| SC-03 | Cân đối fat/carb | Fat và carb nên nằm trong khoảng chấp nhận. |
| SC-04 | Đa dạng món | Hạn chế lặp món quá nhiều. |
| SC-05 | Dễ nấu | Ưu tiên món thời gian nấu ngắn hoặc tag dễ nấu. |
| SC-06 | Tiết kiệm | Ưu tiên món chi phí thấp khi ngân sách hạn chế. |
| SC-07 | Tái sử dụng nguyên liệu | Dùng lại nguyên liệu hợp lý để giảm lãng phí. |
| SC-08 | Phù hợp sở thích | Ưu tiên món khớp tag hoặc yêu cầu user. |

### 5.6. Tiêu chí đánh giá thuật toán

| Tiêu chí | Cách đo | Mục tiêu |
| --- | --- | --- |
| Tỷ lệ tạo thành công | Số lần tạo được thực đơn / tổng request test | Tối thiểu 80% với profile khả thi |
| Tuân thủ ngân sách | So tổng chi phí với ngân sách | Không vi phạm hard budget trong plan hợp lệ |
| Tuân thủ dị ứng | Kiểm tra ingredient list | 100% |
| Độ lệch calo | So calo/ngày với target | Trong ngưỡng cấu hình |
| Độ lệch macro | So protein/fat/carb với target | Trong ngưỡng cấu hình |
| Đa dạng | Đếm số lần lặp món | Không vượt ngưỡng cấu hình |
| Thời gian xử lý | P95 generate với 7 ngày, 3 bữa, 50 dish | Dưới 500 ms sau warm-up |
| Regenerate | So nutrition score với plan trước | Không kém quá 5% và thay ít nhất một dish nếu có nghiệm gần tương đương |
| Khả năng giải thích | Có dữ liệu đủ để AI giải thích | Có với plan đã validate |

## 6. Yêu cầu phi chức năng

### 6.1. Hiệu suất

| Mã | Yêu cầu |
| --- | --- |
| NFR-PER-01 | API đăng nhập, hồ sơ và danh sách món phản hồi trong thời gian phù hợp với ứng dụng web thông thường. |
| NFR-PER-02 | P95 tạo thực đơn 7 ngày, 3 bữa, 50 dish dưới 500 ms sau warm-up. |
| NFR-PER-03 | API danh sách hỗ trợ phân trang, tìm kiếm và lọc. |
| NFR-PER-04 | Trợ lý AI stream câu trả lời theo SSE; partial response chỉ hiển thị tạm thời và chỉ được lưu khi stream hoàn tất. |

### 6.2. Độ tin cậy

| Mã | Yêu cầu |
| --- | --- |
| NFR-REL-01 | Hệ thống validate input trước khi xử lý. |
| NFR-REL-02 | Chi phí và dinh dưỡng phải do module nội bộ tính toán. |
| NFR-REL-03 | Nếu AI API lỗi, user vẫn có thể tạo thực đơn bằng form có cấu trúc. |
| NFR-REL-04 | Request bất khả thi phải trả lý do rõ ràng thay vì lỗi chung chung. |
| NFR-REL-05 | Thực đơn đã lưu không bị thay đổi ngoài ý muốn khi cập nhật giá hoặc công thức. |

### 6.3. Bảo mật

| Mã | Yêu cầu |
| --- | --- |
| NFR-SEC-01 | Mật khẩu phải hash trước khi lưu. |
| NFR-SEC-02 | API cần đăng nhập phải kiểm tra xác thực. |
| NFR-SEC-03 | User chỉ được truy cập dữ liệu của chính mình. |
| NFR-SEC-04 | API Admin phải kiểm tra quyền Admin. |
| NFR-SEC-05 | Request gửi AI không chứa dữ liệu nhạy cảm không cần thiết. |
| NFR-SEC-06 | Input phải validate để giảm lỗi định dạng và rủi ro injection. |
| NFR-SEC-07 | CORS, biến môi trường và secret key phải cấu hình an toàn. |

### 6.4. Giao diện

| Mã | Yêu cầu |
| --- | --- |
| NFR-UI-01 | Giao diện đơn giản, dễ dùng với người dùng phổ thông. |
| NFR-UI-02 | Form hồ sơ chia nhóm thông tin rõ ràng. |
| NFR-UI-03 | Kết quả thực đơn hiển thị theo ngày và bữa. |
| NFR-UI-04 | Tổng chi phí và macro dễ đọc. |
| NFR-UI-05 | Cảnh báo dễ hiểu, hạn chế thuật ngữ kỹ thuật. |
| NFR-UI-06 | Giao diện AI/chat thể hiện rõ AI chỉ hỗ trợ giải thích và xử lý ngôn ngữ. |

### 6.5. Khả năng bảo trì

- Hệ thống dùng Modular Monolith có ranh giới module rõ.
- Domain layer chứa entity, value object và business rule.
- Application layer chứa use case và repository interface.
- Infrastructure layer chứa database, ORM, migration, external API và AI client.
- Presentation layer chứa router và request/response DTO.
- Logic tính toán và constraint checker phải có unit test độc lập.

### 6.6. Đạo đức và dữ liệu

| Mã | Yêu cầu |
| --- | --- |
| NFR-ETH-01 | Hệ thống phải ghi rõ kết quả chỉ mang tính tham khảo, không thay thế tư vấn y tế. |
| NFR-ETH-02 | Không khuyến nghị chế độ ăn điều trị bệnh. |
| NFR-ETH-03 | Giá thực phẩm là giá tham khảo, có thể khác thực tế. |
| NFR-ETH-04 | Nên ghi nguồn dữ liệu dinh dưỡng và giá. |
| NFR-ETH-05 | Hạn chế gửi dữ liệu cá nhân tới AI provider. |
| NFR-ETH-06 | Mục tiêu dinh dưỡng quá cực đoan phải có cảnh báo. |

## 7. Giao tiếp bên ngoài

### 7.1. Giao diện người dùng

Các màn hình chính:

- Trang giới thiệu.
- Đăng ký và đăng nhập.
- Hồ sơ người dùng.
- Nhập yêu cầu tạo thực đơn.
- Kết quả thực đơn tuần.
- Chi tiết món ăn.
- Danh sách nguyên liệu cần mua.
- Lịch sử thực đơn.
- Quản trị dữ liệu.
- Chat hoặc panel giải thích AI.

### 7.2. Nhóm API nội bộ

| Nhóm API | Chức năng |
| --- | --- |
| `/api/auth/*` | Đăng ký, đăng nhập, đăng xuất, thông tin tài khoản hiện tại |
| `/api/users/*` | Quản lý user |
| `/api/profiles/*` | Tạo/cập nhật hồ sơ |
| `/api/ingredients/*` | Quản lý nguyên liệu |
| `/api/meals/*` | Quản lý món ăn và công thức |
| `/api/meal-plans/*` | Tạo, xem, lưu và dùng lại thực đơn |
| `/api/shopping-lists/*` | Sinh và xem danh sách mua sắm |
| `/api/ai/*` | Parse request, giải thích, gợi ý thay thế, diễn giải cảnh báo |
| `/api/admin/*` | Tác vụ quản trị |

### 7.3. Dịch vụ ngoài

- LLM API như DeepSeek API hoặc provider tương thích.
- Nguồn dữ liệu dinh dưỡng, import và chuẩn hóa trước khi dùng.
- Nguồn giá thực phẩm, import dưới dạng price snapshot.
- OAuth provider trong phiên bản mở rộng.

## 8. User flow chính

1. Guest đăng ký hoặc đăng nhập.
2. User tạo/cập nhật hồ sơ.
3. User nhập request bằng form hoặc tiếng Việt tự nhiên.
4. Nếu dùng tiếng Việt tự nhiên, AI parser chuyển request thành JSON.
5. Backend validate request.
6. Nutrition Calculator tính target dinh dưỡng.
7. Meal Planning Engine sinh candidate plan.
8. Constraint Checker validate thực đơn.
9. Hệ thống trả thực đơn, tổng chi phí, macro, cảnh báo và shopping list.
10. AI giải thích kết quả đã validate nếu user yêu cầu.
11. User lưu, tạo lại hoặc thay thế món.

## 9. Kiểm thử và tiêu chí nghiệm thu

### 9.1. Functional testing

- Đăng ký, đăng nhập, đăng xuất và truy cập route bảo vệ.
- Tạo/cập nhật hồ sơ.
- CRUD nguyên liệu và món ăn bởi Admin.
- Tính giá và macro của món.
- Tạo thực đơn với input khả thi.
- Trả kết quả bất khả thi với ngân sách quá thấp.
- Lọc dị ứng và thực phẩm loại trừ.
- Gộp shopping list.
- Lưu và xem lịch sử thực đơn.
- Tự động lưu, xem lại và tiếp tục tối đa 10 cuộc hội thoại AI cho mỗi user.
- Mỗi cuộc hội thoại giới hạn 20 câu hỏi; retry câu gần nhất thay câu trả lời cũ.

### 9.2. Integration testing

- Frontend form gọi backend API.
- Backend gọi repository/database.
- Planner phối hợp Nutrition Calculator và Constraint Checker.
- Meal plan sinh Shopping List.
- Output AI parser đi qua schema validation.
- Lịch sử chat lấy từ database theo ownership, không tin history do client gửi.

### 9.3. AI testing

- Input tiếng Việt hợp lệ được parse thành JSON đúng.
- Input mơ hồ yêu cầu nhập lại hoặc fallback về form.
- JSON AI sai schema bị reject.
- AI explanation không bịa số tiền hoặc macro.
- Gợi ý thay thế của AI được validate lại.
- Retry chỉ áp dụng turn cuối, không tăng số câu và giữ câu trả lời cũ nếu lần
  retry lỗi.

### 9.4. Security testing

- User chưa đăng nhập không gọi được API bảo vệ.
- User không truy cập được dữ liệu user khác.
- User không đọc, retry hoặc xóa conversation AI của user khác.
- User không có role Admin không gọi được Admin API.
- Password không lưu plain text.
- Input sai kiểu hoặc ngoài phạm vi bị reject.

### 9.5. Tiêu chí nghiệm thu

Được xem là đạt khi:

- User tạo hồ sơ và sinh được thực đơn 7 ngày.
- Thực đơn có chi tiết món, tổng ngày, tổng tuần và shopping list.
- Plan hợp lệ không vượt hard budget.
- Dị ứng và thực phẩm loại trừ không xuất hiện trong plan hợp lệ.
- Chi phí và dinh dưỡng do backend tính, không lấy từ AI.
- AI chỉ giải thích dựa trên validated plan.
- Ngân sách bất khả thi trả cảnh báo rõ.
- Module tính toán và constraint checker có unit test.

## 10. Rủi ro và giới hạn

| Rủi ro | Tác động | Giảm thiểu |
| --- | --- | --- |
| AI bịa số liệu | Mất độ tin cậy | Không cho AI tính hoặc override validator |
| Giá thực phẩm thay đổi | Kết quả không khớp giá thực tế | Dùng price snapshot và hiển thị nguồn/ngày |
| Mapping nguyên liệu không nhất quán | Sai chi phí hoặc dinh dưỡng | Chuẩn hóa tên, đơn vị và alias |
| Dataset nhỏ | Thực đơn dễ lặp | Chuẩn bị 30-50 món và 50-100 nguyên liệu |
| Ngân sách quá thấp | Planner không tạo được plan | Trả infeasible report và gợi ý điều chỉnh |
| Người dùng hiểu nhầm là tư vấn y tế | Rủi ro đạo đức/học thuật | Hiển thị medical boundary rõ ràng |
| UI tốn thời gian | Trễ MVP | Ưu tiên luồng chính trước tính năng nâng cao |


