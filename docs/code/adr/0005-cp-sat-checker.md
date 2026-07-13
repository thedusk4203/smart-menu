# ADR-0005 — CP-SAT cùng Constraint Checker độc lập

- Status: Accepted — retrospective
- Date: 2026-07-13
- Scope: meal planning

## Context

Planner có feasibility assessment, `DishCpSatOptimizer`, composition và `validate_plan` độc lập.

## Decision

Dùng CP-SAT để tìm/tối ưu nghiệm; luôn revalidate kết quả bằng checker trước response/save.

## Consequences

Rule mới phải hiện diện ở optimizer **và** checker; checker có thể chặn solver result. Điều này tăng code/test nhưng giảm nguy cơ invalid plan.

## Verification and revisit trigger

Kiểm test planner/model và infeasible cases. Xem lại khi solver model đổi hoặc checker duplication trở thành bottleneck.

