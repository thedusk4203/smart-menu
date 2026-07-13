# Kiểm thử và bằng chứng chất lượng

## Mục tiêu

Biết test nào bảo vệ rule nào, chạy đúng gate trước khi bàn giao và thêm regression test khi sửa bug.

## Nguồn sự thật

- `backend/app/tests/` và `backend/pyproject.toml`.
- `frontend/package.json`, `frontend/scripts/release-check.mjs` và `docs/launch-readiness.md`.

## Test map

| Khu vực | Evidence chính |
| --- | --- |
| Identity/profile/nutrition | Registration, Google login, profile update, calculator/domain tests |
| Catalog/data | Dish candidate invariants, typed tags, quality issues, import templates |
| Planner/shopping | Dish planner, models, shopping list, infeasible/constraint behavior |
| AI | Request parser, chat template, use cases, provider config, conversations, retention, plan explanation |
| Frontend | TypeScript compilation, ESLint, release guard, Vite production build |

Không có ngưỡng coverage số; thay đổi behavior phải có test có ý nghĩa tại module/use-case và regression test cho bug đã thấy.

## Lệnh bắt buộc

Chạy từ root repository trừ khi ghi khác:

```powershell
cd backend; uv run pytest -q
cd frontend; npm run build
cd frontend; npm run lint
cd frontend; npm run check:release
```

Production build đã bao gồm `tsc -b` trước Vite. Khi docs ghi số lượng test, chạy lại ở thời điểm authoring; baseline 13/07/2026 là 189 passed với 3 warning không làm fail.

## Thêm regression test

1. Viết test biểu diễn bug hoặc contract mới trước/song song patch.
2. Đặt theo feature trong `backend/app/tests/test_<feature>/test_<behavior>.py`.
3. Với planner, cover cả candidate/feasibility/optimizer/checker nếu rule xuất hiện ở nhiều lớp.
4. Với role/share/AI, test unauthorized, expired/disabled, fallback và happy path.
5. Cập nhật API/developer docs nếu contract hay invariant thay đổi.

## Manual smoke matrix

Validate bằng demo accounts: incomplete profile, feasible/infeasible planner, regenerate/swap, AI disabled, empty history, public share mobile, admin import conflict/quality, AI provider disabled/active. Đây là smoke bổ sung, không thay unit/integration tests.

## Khi nào phải cập nhật tài liệu này

Cập nhật khi thêm test framework, CI, release gate, module test, warning policy, smoke scenario hoặc số liệu evidence.

## Kiểm tra mức độ hiểu

### Câu 1 (trắc nghiệm)

Lệnh nào type-check và tạo production bundle frontend?

A. `npm run build`  
B. `npm run dev`  
C. `docker compose down`

### Câu 2 (trắc nghiệm)

Bug planner đã sửa nên có test ở đâu?

A. Chỉ screenshot slide  
B. Test backend feature phù hợp, ưu tiên use case/invariant bị lỗi  
C. Chỉ ESLint

### Câu 3 (trắc nghiệm)

Smoke test manual có thay được pytest không?

A. Có  
B. Không  
C. Chỉ khi AI tắt

### Câu 4 (tình huống)

Một swap AI được xếp hạng cao nhưng checker từ chối. Hãy nêu test regression và expected response.

### Câu 5 (tình huống)

Build pass nhưng route mới không tải được lazy page. Hãy nêu các kiểm tra cần làm.

## Đáp án, giải thích và bằng chứng mong đợi

1. **A.** Script chạy TypeScript build rồi Vite.
2. **B.** Test phải bảo vệ behavior, không chỉ visual evidence.
3. **B.** Hai lớp kiểm chứng mục tiêu khác nhau.
4. Test SuggestSwap/constraint checker với candidate đó và xác nhận API không trả suggestion invalid; AI ranking không override validation.
5. Kiểm route path/lazy import/export default mapping, guard/layout, console/network, TypeScript type và production build/release guard.


Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
