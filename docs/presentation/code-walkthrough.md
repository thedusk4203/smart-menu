# Code walkthrough 6–8 phút: tạo thực đơn từ UI đến validation

## Mục tiêu

Trình bày một luồng dọc đủ sâu để chứng minh frontend, contract, planner và database nối với nhau như thế nào.

## Chuẩn bị

- Mở trước `frontend/src/app/router.tsx`, `pages/meal-planning/CreateMenu.tsx`, `api/mealPlanApi.ts`.
- Mở `backend/app/modules/meal_planning/router.py`, `use_cases.py`, `optimizer_v3.py`, `procurement_checker.py`.
- Mở `data/init_db.sql` tại `v_dish_candidates` và [API planner/shopping](../code/api/planner-shopping.md).
- Dùng dữ liệu demo đã có; không chiếu `.env`, token, provider secret hoặc share link thật.

## Kịch bản

| Thời gian | Điểm code | Nội dung nói | Bằng chứng |
| --- | --- | --- | --- |
| 0:00–0:45 | `router.tsx` → `CreateMenu` | Route User được guard, form thu thập ngày/budget/preference; UI không tự quyết plan hợp lệ. | Route `/create-menu` và guard |
| 0:45–1:30 | `mealPlanApi.generate` | Wrapper giữ `POST /api/meal-plans/generate` và TypeScript contract. | API reference request/response |
| 1:30–2:15 | Backend router + `BuildPlanRequestUseCase` | Backend xác thực User, đọc profile/exclusion, chuẩn hóa request. | 401/422/incomplete-profile path |
| 2:15–3:15 | Candidate provider + `v_dish_candidates` | Chỉ dish active/đủ recipe, nutrition, price mới vào planner. | View SQL + quality boundary |
| 3:15–4:30 | Feasibility + `ProcurementCpSatOptimizer` | Hard constraint giữ mục tiêu dinh dưỡng; objective tối ưu mua mới, tồn kho, FEFO và đa dạng. | Infeasible reason hoặc solver result |
| 4:30–5:20 | `validate_plan` | Checker chạy độc lập sau solver, chặn plan có exclusion/cấu trúc sai/budget sai. | Validation result/warning |
| 5:20–6:10 | Result page + save snapshot | UI render generated/infeasible union; save tạo history snapshot và shopping list. | `MealPlanResponse`, `plan_data` |
| 6:10–7:00 | Regenerate/swap/AI boundary | Signature chống trùng; AI chỉ xếp hạng swap, checker quyết định cuối. | `SuggestSwapUseCase` + ADR-0008 |

## Fallback

- Nếu solver demo infeasible: dùng chính response reason để giải thích feasibility, không đổi input ngầm.
- Nếu AI tắt: bỏ đoạn swap AI, vẫn trình bày form structured/planner/checker.
- Nếu database không sẵn: trình bày sequence/API schema, không bịa kết quả runtime.

## Kết luận nói trong 15 giây

“Điểm kiểm chứng không nằm ở một model AI hay một trang UI: request đi qua contract, dữ liệu candidate có quality gate, CP-SAT tìm nghiệm và checker độc lập xác nhận trước khi User thấy hoặc lưu plan.”
