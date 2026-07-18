# API — Meal Plan, Shopping List và Public Sharing

> Full schema catalog được sao chép từ OpenAPI runtime ngày 13/07/2026. `401`, `403`, `404`, `422` và `{ "detail": string }` áp dụng theo authentication, quyền, ownership, target và validation.

## Operation index

| Method | Path | Request | Success response |
| --- | --- | --- | --- |
| GET | `/api/meal-plans` |  | 200: array<MealPlanResponse> |
| POST | `/api/meal-plans` | MealPlanCreate | 201: MealPlanResponse<br>422: HTTPValidationError |
| DELETE | `/api/meal-plans/{plan_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/meal-plans/{plan_id}` |  | 200: MealPlanResponse<br>422: HTTPValidationError |
| GET | `/api/meal-plans/{plan_id}/shopping-list` |  | 200: ShoppingListResponse<br>422: HTTPValidationError |
| PATCH | `/api/meal-plans/{plan_id}/shopping-list/items/{item_id}` | PurchaseUpdate | 200: ShoppingListResponse<br>422: HTTPValidationError |
| DELETE | `/api/meal-plans/{plan_id}/shopping-list/share` |  | 204: no body<br>422: HTTPValidationError |
| POST | `/api/meal-plans/{plan_id}/shopping-list/share` |  | 200: ShoppingShareResponse<br>422: HTTPValidationError |
| POST | `/api/meal-plans/generate` | GenerateMealPlanRequest | 200: GeneratedMealPlanResponse **hoặc** InfeasiblePlanResponse<br>422: HTTPValidationError |
| GET | `/api/public/shopping-lists/{token}` |  | 200: PublicShoppingListResponse<br>422: HTTPValidationError |
| PATCH | `/api/public/shopping-lists/{token}/items/{item_id}` | PurchaseUpdate | 200: PublicShoppingListResponse<br>422: HTTPValidationError |

## Parameters and content type
### `GET /api/meal-plans`
No path/query parameter.

### `POST /api/meal-plans`
No path/query parameter.
Request content type: `application/json`

### `DELETE /api/meal-plans/{plan_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `plan_id` | path | True | integer |

### `GET /api/meal-plans/{plan_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `plan_id` | path | True | integer |

### `GET /api/meal-plans/{plan_id}/shopping-list`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `plan_id` | path | True | integer |
| `day` | query | False | integer 1–7 hoặc null |

### `PATCH /api/meal-plans/{plan_id}/shopping-list/items/{item_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `plan_id` | path | True | integer |
| `item_id` | path | True | integer |
| `day` | query | False | integer 1–7 hoặc null |
Request content type: `application/json`

### `DELETE /api/meal-plans/{plan_id}/shopping-list/share`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `plan_id` | path | True | integer |

### `POST /api/meal-plans/{plan_id}/shopping-list/share`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `plan_id` | path | True | integer |
| `day` | query | False | integer 1–7 hoặc null |

### `POST /api/meal-plans/generate`
No path/query parameter.
Request content type: `application/json`

Response `200` là union: body thành công dùng `GeneratedMealPlanResponse`; bài toán hợp lệ về request nhưng không có nghiệm hard-valid dùng `InfeasiblePlanResponse` với `status="infeasible"`. Client phải phân nhánh theo shape/status, không chỉ theo HTTP code.

### `GET /api/public/shopping-lists/{token}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `token` | path | True | string |

### `PATCH /api/public/shopping-lists/{token}/items/{item_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `token` | path | True | string |
| `item_id` | path | True | integer |
Request content type: `application/json`

## Schema catalog
### `GeneratedMealPlanResponse`
```json
{
  "properties": {
    "user_id": {
      "type": "integer",
      "title": "User Id"
    },
    "name": {
      "type": "string",
      "title": "Name"
    },
    "start_date": {
      "anyOf": [
        {
          "type": "string",
          "format": "date"
        },
        {
          "type": "null"
        }
      ],
      "title": "Start Date"
    },
    "end_date": {
      "anyOf": [
        {
          "type": "string",
          "format": "date"
        },
        {
          "type": "null"
        }
      ],
      "title": "End Date"
    },
    "budget_limit": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Budget Limit"
    },
    "total_cost": {
      "type": "number",
      "title": "Total Cost"
    },
    "total_calories": {
      "type": "number",
      "title": "Total Calories"
    },
    "plan_data": {
      "additionalProperties": true,
      "type": "object",
      "title": "Plan Data"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "name",
    "start_date",
    "end_date",
    "budget_limit",
    "total_cost",
    "total_calories",
    "plan_data"
  ],
  "title": "GeneratedMealPlanResponse"
}
```

### `GenerateMealPlanRequest`
```json
{
  "properties": {
    "days": {
      "anyOf": [
        {
          "type": "integer",
          "maximum": 7.0,
          "minimum": 1.0
        },
        {
          "type": "null"
        }
      ],
      "title": "Days"
    },
    "meals_per_day": {
      "anyOf": [
        {
          "type": "integer",
          "enum": [
            2,
            3
          ]
        },
        {
          "type": "null"
        }
      ],
      "title": "Meals Per Day"
    },
    "budget_limit": {
      "anyOf": [
        {
          "type": "number",
          "exclusiveMinimum": 0.0
        },
        {
          "type": "null"
        }
      ],
      "title": "Budget Limit"
    },
    "preferred_tags": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "maxItems": 12,
      "title": "Preferred Tags"
    },
    "seed": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Seed"
    },
    "previous_plan_signature": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 4096
        },
        {
          "type": "null"
        }
      ],
      "title": "Previous Plan Signature"
    }
  },
  "type": "object",
  "title": "GenerateMealPlanRequest"
}
```

### `HTTPValidationError`
```json
{
  "properties": {
    "detail": {
      "items": {
        "$ref": "#/components/schemas/ValidationError"
      },
      "type": "array",
      "title": "Detail"
    }
  },
  "type": "object",
  "title": "HTTPValidationError"
}
```

### `InfeasiblePlanResponse`
```json
{
  "properties": {
    "status": {
      "type": "string",
      "title": "Status",
      "default": "infeasible"
    },
    "reasons": {
      "items": {
        "$ref": "#/components/schemas/InfeasibleReasonResponse"
      },
      "type": "array",
      "title": "Reasons"
    },
    "warnings": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array",
      "title": "Warnings"
    }
  },
  "type": "object",
  "title": "InfeasiblePlanResponse"
}
```

### `InfeasibleReasonResponse`
```json
{
  "properties": {
    "code": {
      "type": "string",
      "title": "Code"
    },
    "message": {
      "type": "string",
      "title": "Message"
    },
    "details": {
      "additionalProperties": {
        "anyOf": [
          {
            "type": "number"
          },
          {
            "type": "integer"
          },
          {
            "type": "string"
          }
        ]
      },
      "type": "object",
      "title": "Details"
    }
  },
  "type": "object",
  "required": [
    "code",
    "message"
  ],
  "title": "InfeasibleReasonResponse"
}
```

### `MealPlanCreate`
```json
{
  "properties": {
    "name": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 255
        },
        {
          "type": "null"
        }
      ],
      "title": "Name"
    },
    "start_date": {
      "type": "string",
      "format": "date",
      "title": "Start Date"
    },
    "budget_limit": {
      "anyOf": [
        {
          "type": "number",
          "exclusiveMinimum": 0.0
        },
        {
          "type": "null"
        }
      ],
      "title": "Budget Limit"
    },
    "days": {
      "items": {
        "$ref": "#/components/schemas/SavedPlanDay"
      },
      "type": "array",
      "maxItems": 7,
      "minItems": 1,
      "title": "Days"
    }
  },
  "type": "object",
  "required": [
    "start_date",
    "days"
  ],
  "title": "MealPlanCreate"
}
```

### `MealPlanResponse`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "user_id": {
      "type": "integer",
      "title": "User Id"
    },
    "name": {
      "type": "string",
      "title": "Name"
    },
    "start_date": {
      "type": "string",
      "format": "date",
      "title": "Start Date"
    },
    "end_date": {
      "anyOf": [
        {
          "type": "string",
          "format": "date"
        },
        {
          "type": "null"
        }
      ],
      "title": "End Date"
    },
    "budget_limit": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Budget Limit"
    },
    "total_cost": {
      "type": "number",
      "title": "Total Cost"
    },
    "total_calories": {
      "type": "number",
      "title": "Total Calories"
    },
    "plan_data": {
      "additionalProperties": true,
      "type": "object",
      "title": "Plan Data"
    },
    "created_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Created At"
    }
  },
  "type": "object",
  "required": [
    "id",
    "user_id",
    "name",
    "start_date",
    "end_date",
    "budget_limit",
    "total_cost",
    "total_calories",
    "plan_data"
  ],
  "title": "MealPlanResponse"
}
```

### `MealType`
```json
{
  "type": "string",
  "enum": [
    "breakfast",
    "lunch",
    "dinner"
  ],
  "title": "MealType",
  "description": "Loại bữa ăn."
}
```

### `PublicShoppingListResponse`
```json
{
  "properties": {
    "plan_id": {
      "type": "integer",
      "title": "Plan Id"
    },
    "plan_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Plan Name"
    },
    "day": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Day"
    },
    "date": {
      "anyOf": [
        {
          "type": "string",
          "format": "date"
        },
        {
          "type": "null"
        }
      ],
      "title": "Date"
    },
    "schema_version": {
      "type": "integer",
      "title": "Schema Version"
    },
    "items": {
      "items": {
        "$ref": "#/components/schemas/ShoppingListItem"
      },
      "type": "array",
      "title": "Items"
    },
    "total_estimated_cost": {
      "type": "number",
      "title": "Total Estimated Cost"
    },
    "warnings": {
      "items": {
        "$ref": "#/components/schemas/ShoppingListWarning"
      },
      "type": "array",
      "title": "Warnings"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time",
      "title": "Expires At"
    }
  },
  "type": "object",
  "required": [
    "plan_id",
    "schema_version",
    "total_estimated_cost",
    "expires_at"
  ],
  "title": "PublicShoppingListResponse"
}
```

### `PurchaseUpdate`
```json
{
  "properties": {
    "is_purchased": {
      "type": "boolean",
      "title": "Is Purchased"
    }
  },
  "type": "object",
  "required": [
    "is_purchased"
  ],
  "title": "PurchaseUpdate"
}
```

### `SavedMealSlot`
```json
{
  "properties": {
    "slot": {
      "$ref": "#/components/schemas/MealType"
    },
    "dish_ids": {
      "items": {
        "type": "integer"
      },
      "type": "array",
      "maxItems": 3,
      "minItems": 1,
      "title": "Dish Ids"
    }
  },
  "type": "object",
  "required": [
    "slot",
    "dish_ids"
  ],
  "title": "SavedMealSlot",
  "description": "Client chỉ gửi slot và lựa chọn dish; role luôn lấy từ database."
}
```

### `SavedPlanDay`
```json
{
  "properties": {
    "day": {
      "type": "integer",
      "maximum": 7.0,
      "minimum": 1.0,
      "title": "Day"
    },
    "meals": {
      "items": {
        "$ref": "#/components/schemas/SavedMealSlot"
      },
      "type": "array",
      "maxItems": 3,
      "minItems": 2,
      "title": "Meals"
    }
  },
  "type": "object",
  "required": [
    "day",
    "meals"
  ],
  "title": "SavedPlanDay"
}
```

### `ShoppingListItem`
```json
{
  "properties": {
    "id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Id"
    },
    "ingredient_id": {
      "type": "integer",
      "title": "Ingredient Id"
    },
    "name": {
      "type": "string",
      "title": "Name"
    },
    "quantity": {
      "type": "number",
      "title": "Quantity"
    },
    "unit": {
      "type": "string",
      "title": "Unit"
    },
    "estimated_cost": {
      "type": "number",
      "title": "Estimated Cost"
    },
    "is_purchased": {
      "type": "boolean",
      "title": "Is Purchased",
      "default": false
    }
  },
  "type": "object",
  "required": [
    "ingredient_id",
    "name",
    "quantity",
    "unit",
    "estimated_cost"
  ],
  "title": "ShoppingListItem"
}
```

### `ShoppingListResponse`
```json
{
  "properties": {
    "plan_id": {
      "type": "integer",
      "title": "Plan Id"
    },
    "plan_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Plan Name"
    },
    "day": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Day"
    },
    "date": {
      "anyOf": [
        {
          "type": "string",
          "format": "date"
        },
        {
          "type": "null"
        }
      ],
      "title": "Date"
    },
    "schema_version": {
      "type": "integer",
      "title": "Schema Version"
    },
    "items": {
      "items": {
        "$ref": "#/components/schemas/ShoppingListItem"
      },
      "type": "array",
      "title": "Items"
    },
    "total_estimated_cost": {
      "type": "number",
      "title": "Total Estimated Cost"
    },
    "warnings": {
      "items": {
        "$ref": "#/components/schemas/ShoppingListWarning"
      },
      "type": "array",
      "title": "Warnings"
    }
  },
  "type": "object",
  "required": [
    "plan_id",
    "schema_version",
    "total_estimated_cost"
  ],
  "title": "ShoppingListResponse"
}
```

### `ShoppingListWarning`
```json
{
  "properties": {
    "code": {
      "type": "string",
      "title": "Code"
    },
    "message": {
      "type": "string",
      "title": "Message"
    }
  },
  "type": "object",
  "required": [
    "code",
    "message"
  ],
  "title": "ShoppingListWarning"
}
```

### `ShoppingShareResponse`
```json
{
  "properties": {
    "token": {
      "type": "string",
      "title": "Token"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time",
      "title": "Expires At"
    },
    "day": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Day"
    }
  },
  "type": "object",
  "required": [
    "token",
    "expires_at"
  ],
  "title": "ShoppingShareResponse"
}
```

### `ValidationError`
```json
{
  "properties": {
    "loc": {
      "items": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "integer"
          }
        ]
      },
      "type": "array",
      "title": "Location"
    },
    "msg": {
      "type": "string",
      "title": "Message"
    },
    "type": {
      "type": "string",
      "title": "Error Type"
    },
    "input": {
      "title": "Input"
    },
    "ctx": {
      "type": "object",
      "title": "Context"
    }
  },
  "type": "object",
  "required": [
    "loc",
    "msg",
    "type"
  ],
  "title": "ValidationError"
}
```

## Kiểm tra mức độ hiểu

### Câu 1 (trắc nghiệm)

Generate plan success schema là gì?

A. `GeneratedMealPlanResponse` hoặc `InfeasiblePlanResponse` theo result  
B. `TokenResponse`  
C. `ProviderItem`

### Câu 2 (trắc nghiệm)

Public share request có dùng Bearer token không?

A. Không; token capability nằm ở path  
B. Luôn dùng admin Bearer  
C. Chỉ dùng cookie DB

### Câu 3 (trắc nghiệm)

HTTP 204 có body JSON không?

A. Có  
B. Không  
C. Chỉ với shopping list

### Câu 4 (tình huống)

Hãy xác định schema và parameter để update trạng thái purchased qua public link.

### Câu 5 (tình huống)

Planner trả infeasible. Hãy nêu schema cần đọc thay vì cố parse generated plan.

## Đáp án, giải thích và bằng chứng mong đợi

1. **A.** Generator có outcome hợp lệ hoặc infeasible có cấu trúc.
2. **A.** Share token là capability scope/expiry riêng.
3. **B.** Client không gọi `.json()` cho 204.
4. `PATCH /api/public/shopping-lists/{token}/items/{item_id}`, path token/item ID và body `PurchaseUpdate`.
5. `InfeasiblePlanResponse` và nested `InfeasibleReasonResponse`; hiển thị reason/warning, không tự chế day/meal data.


Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
