# API — Meal Plan V3, Shopping List, Inventory và Public Sharing

> Đối chiếu OpenAPI runtime và code ngày 20/07/2026. Planner chỉ hỗ trợ snapshot schema 3. Các endpoint trừ public share đều cần access token.

## Operation index

| Method | Path | Body | Thành công |
| --- | --- | --- | --- |
| `POST` | `/api/meal-plans/generate` | `GenerateMealPlanRequest` | `GeneratedMealPlanResponse` hoặc `InfeasiblePlanResponse` |
| `POST` | `/api/meal-plans` | `MealPlanCreate` | `201 MealPlanResponse` |
| `GET` | `/api/meal-plans` | — | `MealPlanResponse[]` của User |
| `GET` | `/api/meal-plans/{plan_id}` | — | `MealPlanResponse` |
| `DELETE` | `/api/meal-plans/{plan_id}` | — | `204` |
| `GET` | `/api/meal-plans/{plan_id}/shopping-list` | — | `ShoppingListResponse` |
| `PATCH` | `/api/meal-plans/{plan_id}/shopping-list/items/{item_id}` | `PurchaseUpdate` | `ShoppingListResponse` |
| `POST` | `/api/meal-plans/{plan_id}/shopping-list/share` | — | `ShoppingShareResponse` |
| `DELETE` | `/api/meal-plans/{plan_id}/shopping-list/share` | — | `204` |
| `GET` | `/api/public/shopping-lists/{token}` | — | `PublicShoppingListResponse` |
| `PATCH` | `/api/public/shopping-lists/{token}/items/{item_id}` | `PurchaseUpdate` | `PublicShoppingListResponse` |
| `GET` | `/api/inventory-lots` | — | `InventoryLotResponse[]` |
| `PATCH` | `/api/inventory-lots/{lot_id}` | `InventoryLotUpdate` | `InventoryLotResponse` |

## Query parameters shopping

Ba owner endpoint GET/PATCH/share nhận cùng query:

| Field | Type | Quy tắc |
| --- | --- | --- |
| `day` | integer/null | 1–7 |
| `scope` | enum/null | `all`, `purchase_day`, `usage_day` |

`purchase_day` và `usage_day` cần `day`. Khi không truyền scope: có day → `usage_day`; không day → `all`.

Public endpoint không nhận day/scope qua query; phạm vi được ký trong token.

## GenerateMealPlanRequest

```json
{
  "days": 7,
  "meals_per_day": 3,
  "budget_limit": 900000,
  "preferred_tags": ["giàu đạm", "ít dầu"],
  "seed": 42,
  "previous_plan_signature": null,
  "start_date": "2026-07-20"
}
```

| Field | Type | Quy tắc |
| --- | --- | --- |
| `days` | integer/null | 1–7; backend mặc định 7 |
| `meals_per_day` | 2, 3 hoặc null | Mặc định từ profile |
| `budget_limit` | number/null | `>0`; nếu null có thể dùng daily budget × days |
| `preferred_tags` | string[] | Tối đa 12; trim, bỏ rỗng/trùng, mỗi tag tối đa 64 |
| `seed` | integer/null | Không có hard range |
| `previous_plan_signature` | string/null | Tối đa 4096 |
| `start_date` | date/null | Router mặc định ngày hiện tại HCM |

## Generate response

Thành công:

```json
{
  "user_id": 7,
  "name": "Thực đơn tuần",
  "start_date": "2026-07-20",
  "end_date": "2026-07-26",
  "budget_limit": 900000,
  "total_cost": 742000,
  "total_calories": 14010.5,
  "plan_data": { "schema_version": 3 }
}
```

Không có nghiệm vẫn là HTTP 200:

```json
{
  "status": "infeasible",
  "reasons": [
    {"code": "BUDGET_PURCHASE_BLOCK_CONFLICT", "message": "...", "details": {}}
  ],
  "warnings": []
}
```

Client phải kiểm `status`/shape, không chỉ HTTP status.

## MealPlanCreate

Save chỉ nhận selection và proof; backend reload/recompute snapshot V3.

```json
{
  "name": "Thực đơn 10:30 20/07/2026",
  "start_date": "2026-07-20",
  "budget_limit": 900000,
  "source_fingerprint": "64-hex-characters...",
  "days": [
    {
      "day": 1,
      "meals": [
        {
          "slot": "breakfast",
          "dish_ids": [12],
          "adjustments": [
            {"dish_id": 12, "ingredient_id": 5, "extra_quantity": 10}
          ]
        },
        {"slot": "lunch", "dish_ids": [2, 8, 16], "adjustments": []},
        {"slot": "dinner", "dish_ids": [1, 9, 17], "adjustments": []}
      ]
    }
  ]
}
```

Quy tắc:

- `name`: null hoặc tối đa 255; trim và không được rỗng sau trim.
- `start_date`: bắt buộc.
- `budget_limit`: null hoặc dương.
- `source_fingerprint`: đúng 64 ký tự.
- `days`: 1–7, day liên tục từ 1, không trùng.
- mỗi ngày 2–3 meal, slot không trùng và đúng thứ tự do backend kiểm.
- `dish_ids`: 1–3 ID dương, không trùng.
- adjustment có ba số dương: dish ID, ingredient ID, extra quantity.

Ngoài lỗi validation, save có thể trả conflict nghiệp vụ `PLAN_SOURCE_CHANGED`, `PLAN_ADJUSTMENTS_CHANGED`, `INVENTORY_CHANGED`.

## MealPlanResponse

| Field | Type |
| --- | --- |
| `id`, `user_id` | integer |
| `name` | string |
| `start_date` | date |
| `end_date` | date/null |
| `budget_limit` | number/null |
| `total_cost`, `total_calories` | number |
| `plan_data` | object snapshot V3 |
| `created_at` | datetime/null |

Nhánh quan trọng trong `plan_data`: `schema_version`, `algorithm_version`, `source_fingerprint`, `plan_signature`, `request_snapshot`, `nutrition_target`, `base_nutrition`, `final_nutrition`, `cost_summary`, `procurement`, `adjustments`, `days`, `metrics`, `warnings`, `meals_per_day`.

## ShoppingListResponse

| Field | Type | Ghi chú |
| --- | --- | --- |
| `plan_id` | integer | Plan nguồn |
| `plan_name` | string/null | Tên snapshot/entity |
| `day` | integer/null | Scope ngày |
| `date` | date/null | Ngày thực |
| `schema_version` | integer | Hiện là 3 |
| `shopping_schema_version` | integer | 3 có ledger; 2 là V3 fallback không ledger |
| `scope` | enum | `all/purchase_day/usage_day` |
| `items` | `ShoppingListItem[]` | Adapter cho checkbox chung |
| `total_estimated_cost` | number | Tổng item đang hiển thị |
| `purchase_items` | `PurchaseItem[]` | Các lần mua/block |
| `pantry_checks` | `PantryCheck[]` | Đồ giả định có sẵn |
| `carryover_usage` | `CarryoverUsage[]` | Đồ từ tồn/lần mua trước dùng ngày này |
| `leftovers` | `LeftoverItem[]` | Tồn cuối/waste |
| `daily_ledger` | `DailyLedgerDay[]` | Opening+mua−dùng−hết hạn=closing |
| `summary` | object number/integer | Cost hierarchy và visible cost |
| `warnings` | `{code,message}[]` | Warning từ plan |

### ShoppingListItem

`id|null`, `ingredient_id`, `name`, `quantity`, `unit`, `estimated_cost`, `is_purchased`, `item_key|null`, `item_kind` (`purchase|pantry`), `scheduled_day|null`.

### PurchaseItem

Kế thừa item và thêm `required_quantity`, `purchase_quantity`, `purchase_cost`, `purchase_increment`, `block_count`, `remaining_quantity`, `expired_waste_quantity`, `carryover_quantity`, `storage_splits[]`.

### CarryoverUsage

`ingredient_id`, `name`, `quantity`, `unit`, `purchase_day`, `use_day`, `storage_mode`, `expiry_day`, `dish_name|null`.

### LeftoverItem

`ingredient_id`, `name`, `quantity`, `unit`, `purchase_day`, `status` thuộc `carryover|closing_stock|expired_waste`.

### DailyLedgerItem

`item_key`, `source_kind` (`inventory|purchase`), `inventory_lot_id|null`, ingredient identity, unit, `opening_quantity`, `purchase_quantity`, `usage_quantity`, `expired_quantity`, `closing_quantity`, `unit_value`, `purchase_cost`, `allocations[]`.

## PurchaseUpdate

```json
{"is_purchased": true}
```

Owner và public PATCH đều build visible scope trước; item ngoài scope trả 404.

## Share schemas

`ShoppingShareResponse` gồm `token`, `expires_at`, `day|null`, `scope`. `PublicShoppingListResponse` kế thừa toàn bộ shopping response và thêm `expires_at`.

Token sai/hết hạn/revoked trả 410. Revoke theo plan làm mọi token dùng cùng share record mất hiệu lực.

## InventoryLotResponse

| Field | Type |
| --- | --- |
| `id`, `ingredient_id` | integer |
| `name`, `unit` | string |
| `quantity_remaining`, `reserved_quantity` | number |
| `available_from`, `expires_on` | date |
| `storage_mode` | `room|fridge|freezer|same_day` |
| `cost_basis_per_unit` | number |
| `source_plan_id`, `source_plan_name` | integer/string hoặc null |
| `status` | `projected|available|consumed|expired|discarded` |
| `created_at` | datetime |

## InventoryLotUpdate

Body nhận ít nhất một field:

- `quantity_remaining`: number `>=0`;
- `expires_on`: date;
- `storage_mode`: enum;
- `status`: chỉ `available` hoặc `discarded`.

Lot có reservation không được discard hoặc giảm lượng. Expiry không được trước available date. Endpoint luôn scope theo User hiện tại.

## Ownership và lỗi

- Plan GET/delete/shopping cho owner; Admin/Super Admin có một số quyền hỗ trợ theo router hiện tại.
- List plan luôn dùng User ID hiện tại.
- Public link không cấp quyền đọc profile hoặc plan JSON đầy đủ.
- `422` là schema/query/business validation; `404` che item ngoài scope; `409` có thể xuất hiện từ conflict fingerprint/inventory/dependency; `410` dành cho share capability không còn hiệu lực.

## Kiểm tra mức độ hiểu

1. Generate infeasible dùng HTTP nào? A. 200 B. 404 C. 409 D. 500
2. Save gửi snapshot procurement từ client không? A. Có B. Không C. Chỉ Admin D. Chỉ public
3. Scope theo ngày cần field nào? A. `day` B. `email` C. `role` D. `seed_name`
4. Public PATCH item ngoài token scope trả gì? A. 404 B. 201 C. 302 D. 204
5. Lot đang reserve có được giảm quantity không? A. Có B. Không C. Chỉ ngày 1 D. Chỉ freezer

## Đáp án

1. **A.** Infeasible là kết quả nghiệp vụ hợp lệ của generate.
2. **B.** Backend reload và tự dựng snapshot V3.
3. **A.** `purchase_day/usage_day` cần ngày 1–7.
4. **A.** Router kiểm visible item trước update.
5. **B.** Giảm sẽ phá plan đang giữ lot.
