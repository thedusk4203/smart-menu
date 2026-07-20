# ADR-0005 — CP-SAT cùng Constraint Checker độc lập

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: meal planning

## Context

Planner có feasibility assessment, `ProcurementCpSatOptimizer`, composition và hai checker độc lập.

## Decision

Dùng CP-SAT để tìm/tối ưu nghiệm; luôn revalidate kết quả bằng checker trước response/save.

Planner V3 mở rộng cùng boundary này sang procurement:

- admin sở hữu `purchase_mode`, bước mua, hạn bảo quản và provenance của ingredient;
- CP-SAT chọn món cùng số block mua, dùng tiền phải chi làm hard budget;
- hard nutrition giữ calo mỗi ngày 80–120%, trung bình plan 90–110% và protein trung bình tối thiểu 90%;
- objective chạy theo thứ tự dinh dưỡng, tiền mua, phần hết hạn, ưu tiên lot sắp hết hạn, số ngày đi chợ, tồn cuối và đa dạng mềm;
- pass FEFO sau solve giải thích cả lot tồn từ plan trước lẫn lot mua mới; `procurement_checker.validate_v3` kiểm tra lại bội số mua, tiền, ledger, hạn và dinh dưỡng;
- phần dư chỉ được thêm vào lần dùng sau khi không quá 20% bước mua, không phát sinh block, đúng giới hạn linh hoạt do admin duyệt và không làm nutrition score xấu đi;
- snapshot V3 lưu fingerprint, procurement, base/final nutrition và adjustment; save reload dữ liệu rồi giải lại selection cố định trước khi persist.

`regular` tham gia tối ưu mua, `pantry` chỉ tạo checklist giả định có sẵn và `ignored` không tạo shopping item. Planner V3 là contract duy nhất; dữ liệu mua thiếu làm generation thất bại có cấu trúc. Cờ `MEAL_PLANNER_V3_LEDGER_ENABLED` chỉ rollout ledger xuyên nhiều plan, không chọn phiên bản planner.

## Consequences

Rule mới phải hiện diện ở optimizer **và** checker; checker có thể chặn solver result. Save plan giữ/chuyển lot trong cùng transaction để hai plan không tiêu cùng một phần dư. Admin/import quản lý procurement metadata và flex rule; shopping list hiển thị ledger mở đầu + mua − dùng − hết hạn = tồn cuối.

## Verification and revisit trigger

Kiểm test planner/model, procurement/ledger invariant, save tampering, shopping scope, migration database sạch và frontend build. Xem lại khi solver model đổi, checker duplication trở thành bottleneck, hoặc sản phẩm hỗ trợ nhiều cửa hàng.
