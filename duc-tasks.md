# Task của Đức — Nhật ký triển khai (meal-planning + nutrition)

> File này ghi lại **những gì đã làm, vì sao, và ở đâu** để bất kỳ ai (kể cả Đức)
> đọc là hiểu. Cập nhật gần nhất: 2026-07-03.

## 1. Bức tranh tổng thể

Phần lõi của Đức = **sinh thực đơn tự động theo ngân sách + dinh dưỡng**.
Trước đợt này, backend đã xong thuật toán nhưng **frontend chưa gọi tới**, và
module `nutrition` **chưa có API**. Đợt này hoàn thiện các mảnh còn thiếu để tính
năng chạy **end-to-end** (người dùng bấm nút → ra thực đơn thật).

Trạng thái sau đợt này:

| Hạng mục | Trước | Sau |
|---|---|---|
| Thuật toán sinh thực đơn (planner/scorer/constraint_checker) | ✅ có | ✅ giữ nguyên |
| Endpoint `POST /api/meal-plans/generate` | ✅ có | ✅ + tham số `seed` |
| Tạo lại thực đơn khác (FR-PLAN-05) | ❌ deterministic, luôn ra 1 kết quả | ✅ có seed → ra phương án khác |
| Frontend gọi `/generate` | ❌ chỉ `navigate` | ✅ nối đầy đủ |
| Module `nutrition` có API | ❌ không router | ✅ `POST /api/nutrition/target` |
| Test backend | 139 pass | 142 pass (thêm 3) |

---

## 2. Backend — cơ chế "Tạo lại thực đơn khác" (FR-PLAN-05)

**Vấn đề:** planner cũ luôn chọn món **điểm cao nhất** cho mỗi bữa → chạy lại
với cùng hồ sơ luôn cho **y hệt** một thực đơn. SRS FR-PLAN-05 yêu cầu "tạo lại"
phải ra phương án **khác**.

**Cách giải:** thêm tham số `seed` xuyên suốt. Khi có `seed`, thay vì luôn chọn
món tốt nhất, planner **bốc ngẫu nhiên trong top-K (K=3) món điểm cao nhất** còn
hợp lệ. Nhờ đó:
- Vẫn ưu tiên món tốt → chất lượng không giảm.
- Vẫn đi qua toàn bộ Constraint Checker → không vi phạm ràng buộc cứng.
- Cùng `seed` → **tái lập** đúng kết quả (debug được).
- `seed = None` (mặc định) → giữ **nguyên hành vi cũ** (deterministic) nên 139
  test cũ không đổi.

**File đã sửa:**
- `backend/app/modules/meal_planning/ports.py` — thêm kw `seed` vào abstract
  `MealPlannerPort.generate`.
- `backend/app/modules/meal_planning/planner.py`
  - Thêm `import random`, hằng `_VARIETY_TOP_K = 3`.
  - `generate(...)` nhận `seed`; tạo `rng = random.Random(seed)` khi có seed.
  - `_pick_for_slot(...)` nhận `rng`: nếu `rng is None` → `max(...)` như cũ;
    ngược lại `sorted(...)` theo điểm giảm dần, lấy top-K rồi `rng.choice(top)`.
- `backend/app/modules/meal_planning/use_cases.py` — `GenerateMealPlanUseCase.execute`
  nhận `seed` và truyền xuống planner.
- `backend/app/modules/meal_planning/schemas.py` — `GenerateMealPlanRequest`
  thêm field `seed: int | None = None`.
- `backend/app/modules/meal_planning/router.py` — `POST /generate` đọc `data.seed`
  và gọi `generate.execute(request, seed=data.seed)`.

**Test đã thêm** (`backend/app/tests/test_meal_planning/`):
- `test_planner.py` → class `TestRegenerateSeed`:
  - `test_same_seed_is_reproducible` — cùng seed ⇒ `plan_data` giống hệt.
  - `test_different_seeds_can_produce_different_plans` — quét 10 seed, phải có
    ≥ 2 phương án khác nhau.
  - `test_no_seed_stays_deterministic` — không seed ⇒ vẫn giống nhau giữa 2 lần.
- `test_use_cases.py` → cập nhật fake `_RecordingPlanner.generate` để nhận `seed`
  (vì use case giờ luôn truyền tham số này).

---

## 3. Backend — Router cho module `nutrition`

**Vấn đề:** `NutritionCalculator` (BMR → TDEE → calo mục tiêu → macro + cảnh báo)
đã hoàn chỉnh và được `meal_planning` dùng nội bộ, nhưng **không có HTTP endpoint**
nên frontend không hiển thị được nhu cầu dinh dưỡng cho người dùng.

**Cách giải:** thêm 1 endpoint thuần tính toán (không đọc DB, không cần đăng nhập).

**File đã thêm/sửa:**
- `backend/app/modules/nutrition/router.py` (MỚI) — `POST /api/nutrition/target`,
  nhận `NutritionProfileInput`, trả `NutritionTargetResponse`.
- `backend/app/dependencies.py` — thêm provider `get_calculate_nutrition_target_use_case()`
  (dùng `CalculateNutritionTargetUseCase` sẵn có; stateless nên **không** cần `Session`).
- `backend/app/api.py` — `include_router(nutrition_router)`.

**Ví dụ gọi:**
```
POST /api/nutrition/target
{ "gender":"male","age":25,"weight_kg":70,"height_cm":175,
  "activity_level":"moderate","fitness_goal":"maintain" }
→ { bmr, tdee, target_calories, daily_protein_g, daily_fat_g, daily_carb_g,
    bmi, is_feasible, warnings:[{code,message}] }
```

---

## 4. Frontend — Nối tính năng sinh thực đơn (phần quan trọng nhất)

**Vấn đề:** nút "Tạo Thực Đơn Ngay" chỉ `navigate("/menu-result")`, và
`MenuResult` hiển thị **dữ liệu giả cứng** (mock 7 ngày). Toàn bộ thuật toán
backend chưa được người dùng chạm tới.

**Điểm mấu chốt:** endpoint `/generate` trả `plan_data.days[*].meals[*]` đã có
sẵn **tên món, calo, chi phí** → frontend render trực tiếp, **không** cần gọi
thêm API món ăn.

**File đã thêm/sửa:**
- `frontend/src/api/mealPlanApi.ts` — thêm:
  - Kiểu `PlannedMeal`, `PlannedDay`, `GeneratedMealPlan`, `InfeasibleResult`,
    `GenerateParams`.
  - `isInfeasible(r)` — type guard phân biệt kết quả bất khả thi vs thực đơn.
  - `generateMealPlan(params)` — `POST /api/meal-plans/generate` (tự gắn `user_id`
    từ `getMe()`; **không tự lưu**).
- `frontend/src/api/nutritionApi.ts` (MỚI) — `calculateNutritionTarget(input)`
  gọi `POST /api/nutrition/target` (dùng cho trang Hồ sơ xem trước BMR/TDEE/macro).
- `frontend/src/app/CreateMenu.tsx` — viết lại phần logic:
  - Ô ngân sách + ô "Yêu cầu đặc biệt" giờ là **state** thật.
  - "Yêu cầu đặc biệt" tách theo dấu phẩy/xuống dòng thành `preferred_tags`
    (ràng buộc **mềm** — an toàn khi chưa có AI parse).
  - Bấm nút → gọi `generateMealPlan` → có **loading**, **báo lỗi**, và khi
    **bất khả thi** thì liệt kê lý do (không điều hướng).
  - Thành công → `navigate("/menu-result", { state: { plan, params } })`.
- `frontend/src/app/MenuResult.tsx` — viết lại để chạy dữ liệu thật:
  - Đọc thực đơn từ `location.state`; nếu vào thẳng (refresh) → màn hình rỗng
    kèm nút quay lại tạo mới.
  - Render tổng chi phí, calo trung bình/ngày, **cảnh báo dinh dưỡng** (nếu có),
    và từng ngày/bữa từ `plan_data`.
  - Nút **"Tạo lại thực đơn khác"** → gọi `generateMealPlan({...params, seed})`
    với seed ngẫu nhiên (FR-PLAN-05).
  - Nút **"Lưu thực đơn"** → `saveMealPlan(...)` (gán `start_date` = hôm nay vì
    thực đơn vừa sinh chưa có ngày).

**Luồng dữ liệu:**
```
CreateMenu (form) ──generateMealPlan()──> POST /api/meal-plans/generate
      │                                          │
      │  navigate(state:{plan,params})           ├─ ok → GeneratedMealPlan
      ▼                                          └─ infeasible → {reasons}
MenuResult (render) ──"Tạo lại" (seed mới)──> /generate
                    └──"Lưu" ─────────────────> POST /api/meal-plans
```

---

## 5. Việc CÒN LẠI / lưu ý cho người sau

- **[Blocker môi trường] `python-multipart` chưa cài** trong `backend/.venv`.
  Endpoint `POST /api/auth/login` (form OAuth2, do phần identity merge từ main)
  cần gói này, nếu thiếu thì **cả server không khởi động được** (`from app.main
  import app` lỗi). Khắc phục: `cd backend && uv add python-multipart` (hoặc
  `uv sync`). *Không thuộc phần meal-planning của Đức nhưng chặn chạy thử.*
- **`frontend/` chưa cài `node_modules`.** Chạy `cd frontend && npm install`
  trước khi `npm run dev` / `npm run build`.
- **"Đổi món bằng AI"** (ô chat trong MenuResult cũ, `aiApi.ts`, module `ai/`)
  và **shopping list** (`shoppingListApi.ts`) vẫn là stub — thuộc người khác.
- **`preferred_tags`** hiện tách thô từ text; khi có AI parser (module `ai`) nên
  thay bằng parse tiếng Việt đúng nghĩa.

## 6. Cách kiểm thử nhanh
```bash
# Backend
cd backend
uv sync --extra dev
uv add python-multipart          # nếu chưa có (xem mục 5)
uv run pytest                     # kỳ vọng: 142 passed
uv run uvicorn app.main:app --reload

# Frontend (terminal khác)
cd frontend
npm install
npm run dev                       # mở trang, đăng nhập, vào "Tạo thực đơn"
```
