# API — Admin User, Data, Quality và Import

> Full schema catalog được sao chép từ OpenAPI runtime ngày 13/07/2026. `401`, `403`, `404`, `422` và `{ "detail": string }` áp dụng theo authentication, quyền, ownership, target và validation.

## Operation index

| Method | Path | Request | Success response |
| --- | --- | --- | --- |
| GET | `/api/admin/dashboard/summary` |  | 200: DashboardSummary |
| GET | `/api/admin/dishes` |  | 200: AdminDishPage<br>422: HTTPValidationError |
| POST | `/api/admin/dishes` | AdminDishWrite | 201: AdminDishItem<br>422: HTTPValidationError |
| DELETE | `/api/admin/dishes/{dish_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/admin/dishes/{dish_id}` |  | 200: AdminDishItem<br>422: HTTPValidationError |
| PUT | `/api/admin/dishes/{dish_id}` | AdminDishWrite | 200: AdminDishItem<br>422: HTTPValidationError |
| PATCH | `/api/admin/dishes/{dish_id}/active` | ActiveUpdate | 200: AdminDishItem<br>422: HTTPValidationError |
| GET | `/api/admin/dishes/export` |  | 200: <br>422: HTTPValidationError |
| GET | `/api/admin/imports` |  | 200: ImportJobPage<br>422: HTTPValidationError |
| POST | `/api/admin/imports/{job_id}/commit` | ImportCommitRequest | 200: <br>422: HTTPValidationError |
| POST | `/api/admin/imports/preview` | Body_preview_import_api_admin_imports_preview_post | 200: ImportPreviewResponse<br>422: HTTPValidationError |
| GET | `/api/admin/imports/template` |  | 200: <br>422: HTTPValidationError |
| GET | `/api/admin/ingredients` |  | 200: AdminIngredientPage<br>422: HTTPValidationError |
| POST | `/api/admin/ingredients` | AdminIngredientWrite | 201: AdminIngredientItem<br>422: HTTPValidationError |
| DELETE | `/api/admin/ingredients/{ingredient_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/admin/ingredients/{ingredient_id}` |  | 200: AdminIngredientItem<br>422: HTTPValidationError |
| PUT | `/api/admin/ingredients/{ingredient_id}` | AdminIngredientWrite | 200: AdminIngredientItem<br>422: HTTPValidationError |
| PATCH | `/api/admin/ingredients/{ingredient_id}/active` | ActiveUpdate | 200: AdminIngredientItem<br>422: HTTPValidationError |
| GET | `/api/admin/ingredients/export` |  | 200: <br>422: HTTPValidationError |
| GET | `/api/admin/quality/issues` |  | 200: QualityIssuePage<br>422: HTTPValidationError |
| GET | `/api/admin/users` |  | 200: AdminUserPage<br>422: HTTPValidationError |
| POST | `/api/admin/users` | AdminUserCreate | 201: AdminUserItem<br>422: HTTPValidationError |
| PATCH | `/api/admin/users/{user_id}/role` | AdminUserRoleUpdate | 200: AdminUserItem<br>422: HTTPValidationError |
| PATCH | `/api/admin/users/{user_id}/status` | AdminUserStatusUpdate | 200: AdminUserItem<br>422: HTTPValidationError |

## Parameters and content type
### `GET /api/admin/dashboard/summary`
No path/query parameter.

### `GET /api/admin/dishes`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `search` | query | False |  |
| `dish_type` | query | False |  |
| `status` | query | False |  |
| `quality` | query | False |  |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `POST /api/admin/dishes`
No path/query parameter.
Request content type: `application/json`

### `DELETE /api/admin/dishes/{dish_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `dish_id` | path | True | integer |

### `GET /api/admin/dishes/{dish_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `dish_id` | path | True | integer |

### `PUT /api/admin/dishes/{dish_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `dish_id` | path | True | integer |
Request content type: `application/json`

### `PATCH /api/admin/dishes/{dish_id}/active`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `dish_id` | path | True | integer |
Request content type: `application/json`

### `GET /api/admin/dishes/export`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `format` | query | False | string |
| `search` | query | False |  |
| `dish_type` | query | False |  |
| `status` | query | False |  |
| `quality` | query | False |  |

### `GET /api/admin/imports`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `POST /api/admin/imports/{job_id}/commit`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `job_id` | path | True | integer |
Request content type: `application/json`

### `POST /api/admin/imports/preview`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `entity_type` | query | True | string |
Request content type: `multipart/form-data`

### `GET /api/admin/imports/template`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `entity_type` | query | True | string |
| `format` | query | False | string |

### `GET /api/admin/ingredients`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `search` | query | False |  |
| `food_group` | query | False |  |
| `status` | query | False |  |
| `quality` | query | False |  |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `POST /api/admin/ingredients`
No path/query parameter.
Request content type: `application/json`

### `DELETE /api/admin/ingredients/{ingredient_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `ingredient_id` | path | True | integer |

### `GET /api/admin/ingredients/{ingredient_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `ingredient_id` | path | True | integer |

### `PUT /api/admin/ingredients/{ingredient_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `ingredient_id` | path | True | integer |
Request content type: `application/json`

### `PATCH /api/admin/ingredients/{ingredient_id}/active`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `ingredient_id` | path | True | integer |
Request content type: `application/json`

### `GET /api/admin/ingredients/export`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `format` | query | False | string |
| `search` | query | False |  |
| `food_group` | query | False |  |
| `status` | query | False |  |
| `quality` | query | False |  |

### `GET /api/admin/quality/issues`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `entity_type` | query | False |  |
| `severity` | query | False |  |
| `code` | query | False |  |
| `search` | query | False |  |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `GET /api/admin/users`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `search` | query | False |  |
| `role` | query | False |  |
| `is_active` | query | False |  |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `POST /api/admin/users`
No path/query parameter.
Request content type: `application/json`

### `PATCH /api/admin/users/{user_id}/role`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |
Request content type: `application/json`

### `PATCH /api/admin/users/{user_id}/status`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |
Request content type: `application/json`

## Schema catalog
### `ActiveUpdate`
```json
{
  "properties": {
    "is_active": {
      "type": "boolean",
      "title": "Is Active"
    }
  },
  "type": "object",
  "required": [
    "is_active"
  ],
  "title": "ActiveUpdate"
}
```

### `AdminDishIngredient`
```json
{
  "properties": {
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
    "missing_price": {
      "type": "boolean",
      "title": "Missing Price"
    },
    "missing_nutrition": {
      "type": "boolean",
      "title": "Missing Nutrition"
    }
  },
  "type": "object",
  "required": [
    "ingredient_id",
    "name",
    "quantity",
    "unit",
    "missing_price",
    "missing_nutrition"
  ],
  "title": "AdminDishIngredient"
}
```

### `AdminDishItem`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "name": {
      "type": "string",
      "title": "Name"
    },
    "dish_type": {
      "$ref": "#/components/schemas/DishType"
    },
    "cooking_method": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/CookingMethod"
        },
        {
          "type": "null"
        }
      ]
    },
    "description": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Description"
    },
    "instructions": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Instructions"
    },
    "tags": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Tags",
      "default": []
    },
    "is_active": {
      "type": "boolean",
      "title": "Is Active"
    },
    "total_calories": {
      "type": "number",
      "title": "Total Calories"
    },
    "total_protein_g": {
      "type": "number",
      "title": "Total Protein G"
    },
    "total_carbs_g": {
      "type": "number",
      "title": "Total Carbs G"
    },
    "total_fat_g": {
      "type": "number",
      "title": "Total Fat G"
    },
    "estimated_cost": {
      "type": "number",
      "title": "Estimated Cost"
    },
    "ingredient_count": {
      "type": "integer",
      "title": "Ingredient Count"
    },
    "missing_recipe": {
      "type": "boolean",
      "title": "Missing Recipe"
    },
    "missing_price": {
      "type": "boolean",
      "title": "Missing Price"
    },
    "missing_nutrition": {
      "type": "boolean",
      "title": "Missing Nutrition"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "title": "Created At"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "title": "Updated At"
    },
    "ingredients": {
      "items": {
        "$ref": "#/components/schemas/AdminDishIngredient"
      },
      "type": "array",
      "title": "Ingredients",
      "default": []
    }
  },
  "type": "object",
  "required": [
    "id",
    "name",
    "dish_type",
    "is_active",
    "total_calories",
    "total_protein_g",
    "total_carbs_g",
    "total_fat_g",
    "estimated_cost",
    "ingredient_count",
    "missing_recipe",
    "missing_price",
    "missing_nutrition",
    "created_at",
    "updated_at"
  ],
  "title": "AdminDishItem"
}
```

### `AdminDishPage`
```json
{
  "properties": {
    "items": {
      "items": {
        "$ref": "#/components/schemas/AdminDishItem"
      },
      "type": "array",
      "title": "Items"
    },
    "total": {
      "type": "integer",
      "title": "Total"
    },
    "limit": {
      "type": "integer",
      "title": "Limit"
    },
    "offset": {
      "type": "integer",
      "title": "Offset"
    }
  },
  "type": "object",
  "required": [
    "items",
    "total",
    "limit",
    "offset"
  ],
  "title": "AdminDishPage"
}
```

### `AdminDishWrite`
```json
{
  "properties": {
    "name": {
      "type": "string",
      "maxLength": 255,
      "minLength": 1,
      "title": "Name"
    },
    "dish_type": {
      "$ref": "#/components/schemas/DishType"
    },
    "cooking_method": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/CookingMethod"
        },
        {
          "type": "null"
        }
      ]
    },
    "description": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Description"
    },
    "instructions": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Instructions"
    },
    "tags": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Tags",
      "default": []
    },
    "is_active": {
      "type": "boolean",
      "title": "Is Active",
      "default": true
    },
    "ingredients": {
      "items": {
        "$ref": "#/components/schemas/DishIngredientPayload"
      },
      "type": "array",
      "title": "Ingredients",
      "default": []
    }
  },
  "type": "object",
  "required": [
    "name",
    "dish_type"
  ],
  "title": "AdminDishWrite"
}
```

### `AdminIngredientItem`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "name": {
      "type": "string",
      "title": "Name"
    },
    "food_group": {
      "$ref": "#/components/schemas/FoodGroup"
    },
    "default_unit": {
      "type": "string",
      "title": "Default Unit"
    },
    "grams_per_unit": {
      "type": "number",
      "title": "Grams Per Unit"
    },
    "tags": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Tags",
      "default": []
    },
    "is_active": {
      "type": "boolean",
      "title": "Is Active"
    },
    "calories": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Calories"
    },
    "protein_g": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Protein G"
    },
    "carbs_g": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Carbs G"
    },
    "fat_g": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Fat G"
    },
    "fiber_g": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Fiber G"
    },
    "latest_price": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Latest Price"
    },
    "price_unit": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Price Unit"
    },
    "latest_price_per_unit": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Latest Price Per Unit"
    },
    "price_source": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Price Source"
    },
    "price_recorded_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Price Recorded At"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "title": "Created At"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "title": "Updated At"
    },
    "missing_price": {
      "type": "boolean",
      "title": "Missing Price"
    },
    "missing_nutrition": {
      "type": "boolean",
      "title": "Missing Nutrition"
    },
    "missing_conversion": {
      "type": "boolean",
      "title": "Missing Conversion"
    }
  },
  "type": "object",
  "required": [
    "id",
    "name",
    "food_group",
    "default_unit",
    "grams_per_unit",
    "is_active",
    "created_at",
    "updated_at",
    "missing_price",
    "missing_nutrition",
    "missing_conversion"
  ],
  "title": "AdminIngredientItem"
}
```

### `AdminIngredientPage`
```json
{
  "properties": {
    "items": {
      "items": {
        "$ref": "#/components/schemas/AdminIngredientItem"
      },
      "type": "array",
      "title": "Items"
    },
    "total": {
      "type": "integer",
      "title": "Total"
    },
    "limit": {
      "type": "integer",
      "title": "Limit"
    },
    "offset": {
      "type": "integer",
      "title": "Offset"
    }
  },
  "type": "object",
  "required": [
    "items",
    "total",
    "limit",
    "offset"
  ],
  "title": "AdminIngredientPage"
}
```

### `AdminIngredientWrite`
```json
{
  "properties": {
    "name": {
      "type": "string",
      "maxLength": 255,
      "minLength": 1,
      "title": "Name"
    },
    "food_group": {
      "$ref": "#/components/schemas/FoodGroup"
    },
    "default_unit": {
      "type": "string",
      "maxLength": 20,
      "minLength": 1,
      "title": "Default Unit",
      "default": "g"
    },
    "grams_per_unit": {
      "type": "number",
      "exclusiveMinimum": 0.0,
      "title": "Grams Per Unit",
      "default": 1
    },
    "is_active": {
      "type": "boolean",
      "title": "Is Active",
      "default": true
    },
    "nutrition": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/NutritionPayload"
        },
        {
          "type": "null"
        }
      ]
    },
    "price": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/PricePayload"
        },
        {
          "type": "null"
        }
      ]
    }
  },
  "type": "object",
  "required": [
    "name",
    "food_group"
  ],
  "title": "AdminIngredientWrite"
}
```

### `AdminUserCreate`
```json
{
  "properties": {
    "email": {
      "type": "string",
      "format": "email",
      "title": "Email"
    },
    "password": {
      "type": "string",
      "maxLength": 128,
      "minLength": 8,
      "title": "Password"
    },
    "full_name": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 255
        },
        {
          "type": "null"
        }
      ],
      "title": "Full Name"
    },
    "role": {
      "$ref": "#/components/schemas/UserRole",
      "default": "user"
    }
  },
  "type": "object",
  "required": [
    "email",
    "password"
  ],
  "title": "AdminUserCreate"
}
```

### `AdminUserItem`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "email": {
      "type": "string",
      "format": "email",
      "title": "Email"
    },
    "full_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Full Name"
    },
    "role": {
      "$ref": "#/components/schemas/UserRole"
    },
    "is_active": {
      "type": "boolean",
      "title": "Is Active"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "title": "Created At"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "title": "Updated At"
    }
  },
  "type": "object",
  "required": [
    "id",
    "email",
    "role",
    "is_active",
    "created_at",
    "updated_at"
  ],
  "title": "AdminUserItem"
}
```

### `AdminUserPage`
```json
{
  "properties": {
    "items": {
      "items": {
        "$ref": "#/components/schemas/AdminUserItem"
      },
      "type": "array",
      "title": "Items"
    },
    "total": {
      "type": "integer",
      "title": "Total"
    },
    "limit": {
      "type": "integer",
      "title": "Limit"
    },
    "offset": {
      "type": "integer",
      "title": "Offset"
    }
  },
  "type": "object",
  "required": [
    "items",
    "total",
    "limit",
    "offset"
  ],
  "title": "AdminUserPage"
}
```

### `AdminUserRoleUpdate`
```json
{
  "properties": {
    "role": {
      "$ref": "#/components/schemas/UserRole"
    }
  },
  "type": "object",
  "required": [
    "role"
  ],
  "title": "AdminUserRoleUpdate"
}
```

### `AdminUserStatusUpdate`
```json
{
  "properties": {
    "is_active": {
      "type": "boolean",
      "title": "Is Active"
    }
  },
  "type": "object",
  "required": [
    "is_active"
  ],
  "title": "AdminUserStatusUpdate"
}
```

### `Body_preview_import_api_admin_imports_preview_post`
```json
{
  "properties": {
    "file": {
      "type": "string",
      "contentMediaType": "application/octet-stream",
      "title": "File"
    }
  },
  "type": "object",
  "required": [
    "file"
  ],
  "title": "Body_preview_import_api_admin_imports_preview_post"
}
```

### `CookingMethod`
```json
{
  "type": "string",
  "enum": [
    "stir_fry",
    "boil",
    "soup",
    "braise",
    "steam"
  ],
  "title": "CookingMethod",
  "description": "Cách chế biến món ăn."
}
```

### `DashboardSummary`
```json
{
  "properties": {
    "users_total": {
      "type": "integer",
      "title": "Users Total"
    },
    "users_active": {
      "type": "integer",
      "title": "Users Active"
    },
    "users_locked": {
      "type": "integer",
      "title": "Users Locked"
    },
    "ingredients_total": {
      "type": "integer",
      "title": "Ingredients Total"
    },
    "ingredients_active": {
      "type": "integer",
      "title": "Ingredients Active"
    },
    "dishes_total": {
      "type": "integer",
      "title": "Dishes Total"
    },
    "planner_ready_dishes": {
      "type": "integer",
      "title": "Planner Ready Dishes"
    },
    "breakfast_count": {
      "type": "integer",
      "title": "Breakfast Count"
    },
    "staple_count": {
      "type": "integer",
      "title": "Staple Count"
    },
    "savory_count": {
      "type": "integer",
      "title": "Savory Count"
    },
    "vegetable_count": {
      "type": "integer",
      "title": "Vegetable Count"
    },
    "soup_count": {
      "type": "integer",
      "title": "Soup Count"
    },
    "missing_price": {
      "type": "integer",
      "title": "Missing Price"
    },
    "missing_nutrition": {
      "type": "integer",
      "title": "Missing Nutrition"
    },
    "missing_conversion": {
      "type": "integer",
      "title": "Missing Conversion"
    },
    "incomplete_dishes": {
      "type": "integer",
      "title": "Incomplete Dishes"
    },
    "duplicate_names": {
      "type": "integer",
      "title": "Duplicate Names"
    },
    "open_quality_issues": {
      "type": "integer",
      "title": "Open Quality Issues"
    },
    "last_import_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Last Import At"
    }
  },
  "type": "object",
  "required": [
    "users_total",
    "users_active",
    "users_locked",
    "ingredients_total",
    "ingredients_active",
    "dishes_total",
    "planner_ready_dishes",
    "breakfast_count",
    "staple_count",
    "savory_count",
    "vegetable_count",
    "soup_count",
    "missing_price",
    "missing_nutrition",
    "missing_conversion",
    "incomplete_dishes",
    "duplicate_names",
    "open_quality_issues"
  ],
  "title": "DashboardSummary"
}
```

### `DishIngredientPayload`
```json
{
  "properties": {
    "ingredient_id": {
      "type": "integer",
      "title": "Ingredient Id"
    },
    "quantity": {
      "type": "number",
      "exclusiveMinimum": 0.0,
      "title": "Quantity"
    },
    "unit": {
      "type": "string",
      "maxLength": 20,
      "minLength": 1,
      "title": "Unit"
    }
  },
  "type": "object",
  "required": [
    "ingredient_id",
    "quantity",
    "unit"
  ],
  "title": "DishIngredientPayload"
}
```

### `DishType`
```json
{
  "type": "string",
  "enum": [
    "staple",
    "savory",
    "soup",
    "vegetable_side",
    "side",
    "breakfast"
  ],
  "title": "DishType",
  "description": "Phân loại món thành phần mà planner dùng để ghép thành bữa."
}
```

### `FoodGroup`
```json
{
  "type": "string",
  "enum": [
    "protein",
    "vegetable",
    "grain",
    "dairy",
    "fat",
    "fruit",
    "other"
  ],
  "title": "FoodGroup",
  "description": "Nhóm thực phẩm của nguyên liệu."
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

### `ImportCommitRequest`
```json
{
  "properties": {
    "replace_rows": {
      "items": {
        "type": "integer"
      },
      "type": "array",
      "title": "Replace Rows"
    }
  },
  "type": "object",
  "title": "ImportCommitRequest"
}
```

### `ImportJobItem`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "entity_type": {
      "type": "string",
      "title": "Entity Type"
    },
    "filename": {
      "type": "string",
      "title": "Filename"
    },
    "status": {
      "type": "string",
      "title": "Status"
    },
    "total_rows": {
      "type": "integer",
      "title": "Total Rows"
    },
    "valid_rows": {
      "type": "integer",
      "title": "Valid Rows"
    },
    "error_count": {
      "type": "integer",
      "title": "Error Count"
    },
    "created_by": {
      "type": "integer",
      "title": "Created By"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "title": "Created At"
    },
    "completed_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Completed At"
    }
  },
  "type": "object",
  "required": [
    "id",
    "entity_type",
    "filename",
    "status",
    "total_rows",
    "valid_rows",
    "error_count",
    "created_by",
    "created_at"
  ],
  "title": "ImportJobItem"
}
```

### `ImportJobPage`
```json
{
  "properties": {
    "items": {
      "items": {
        "$ref": "#/components/schemas/ImportJobItem"
      },
      "type": "array",
      "title": "Items"
    },
    "total": {
      "type": "integer",
      "title": "Total"
    },
    "limit": {
      "type": "integer",
      "title": "Limit"
    },
    "offset": {
      "type": "integer",
      "title": "Offset"
    }
  },
  "type": "object",
  "required": [
    "items",
    "total",
    "limit",
    "offset"
  ],
  "title": "ImportJobPage"
}
```

### `ImportPreviewResponse`
```json
{
  "properties": {
    "job_id": {
      "type": "integer",
      "title": "Job Id"
    },
    "entity_type": {
      "type": "string",
      "enum": [
        "ingredients",
        "dishes"
      ],
      "title": "Entity Type"
    },
    "filename": {
      "type": "string",
      "title": "Filename"
    },
    "total_rows": {
      "type": "integer",
      "title": "Total Rows"
    },
    "valid_rows": {
      "type": "integer",
      "title": "Valid Rows"
    },
    "errors": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array",
      "title": "Errors"
    },
    "warnings": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array",
      "title": "Warnings"
    },
    "conflicts": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array",
      "title": "Conflicts"
    },
    "preview": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array",
      "title": "Preview"
    },
    "can_commit": {
      "type": "boolean",
      "title": "Can Commit"
    }
  },
  "type": "object",
  "required": [
    "job_id",
    "entity_type",
    "filename",
    "total_rows",
    "valid_rows",
    "errors",
    "warnings",
    "conflicts",
    "preview",
    "can_commit"
  ],
  "title": "ImportPreviewResponse"
}
```

### `NutritionPayload`
```json
{
  "properties": {
    "calories": {
      "type": "number",
      "minimum": 0.0,
      "title": "Calories",
      "default": 0
    },
    "protein_g": {
      "type": "number",
      "minimum": 0.0,
      "title": "Protein G",
      "default": 0
    },
    "carbs_g": {
      "type": "number",
      "minimum": 0.0,
      "title": "Carbs G",
      "default": 0
    },
    "fat_g": {
      "type": "number",
      "minimum": 0.0,
      "title": "Fat G",
      "default": 0
    },
    "fiber_g": {
      "type": "number",
      "minimum": 0.0,
      "title": "Fiber G",
      "default": 0
    }
  },
  "type": "object",
  "title": "NutritionPayload"
}
```

### `PricePayload`
```json
{
  "properties": {
    "price": {
      "type": "number",
      "minimum": 0.0,
      "title": "Price"
    },
    "unit": {
      "type": "string",
      "maxLength": 20,
      "minLength": 1,
      "title": "Unit"
    },
    "price_per_default_unit": {
      "type": "number",
      "minimum": 0.0,
      "title": "Price Per Default Unit"
    },
    "source": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 255
        },
        {
          "type": "null"
        }
      ],
      "title": "Source"
    },
    "recorded_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Recorded At"
    }
  },
  "type": "object",
  "required": [
    "price",
    "unit",
    "price_per_default_unit"
  ],
  "title": "PricePayload"
}
```

### `QualityIssue`
```json
{
  "properties": {
    "entity_type": {
      "type": "string",
      "enum": [
        "ingredient",
        "dish"
      ],
      "title": "Entity Type"
    },
    "entity_id": {
      "type": "integer",
      "title": "Entity Id"
    },
    "entity_name": {
      "type": "string",
      "title": "Entity Name"
    },
    "code": {
      "type": "string",
      "title": "Code"
    },
    "severity": {
      "type": "string",
      "enum": [
        "error",
        "warning"
      ],
      "title": "Severity"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "detail": {
      "type": "string",
      "title": "Detail"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "title": "Updated At"
    }
  },
  "type": "object",
  "required": [
    "entity_type",
    "entity_id",
    "entity_name",
    "code",
    "severity",
    "title",
    "detail",
    "updated_at"
  ],
  "title": "QualityIssue"
}
```

### `QualityIssuePage`
```json
{
  "properties": {
    "items": {
      "items": {
        "$ref": "#/components/schemas/QualityIssue"
      },
      "type": "array",
      "title": "Items"
    },
    "total": {
      "type": "integer",
      "title": "Total"
    },
    "limit": {
      "type": "integer",
      "title": "Limit"
    },
    "offset": {
      "type": "integer",
      "title": "Offset"
    }
  },
  "type": "object",
  "required": [
    "items",
    "total",
    "limit",
    "offset"
  ],
  "title": "QualityIssuePage"
}
```

### `UserRole`
```json
{
  "type": "string",
  "enum": [
    "user",
    "data_editor",
    "admin",
    "super_admin"
  ],
  "title": "UserRole",
  "description": "Vai trò tài khoản."
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

Import preview và commit khác nhau thế nào?

A. Preview validate/conflict, commit mutation theo job đã preview  
B. Cả hai đều ghi catalog ngay  
C. Commit chỉ tải template

### Câu 2 (trắc nghiệm)

Endpoint update role user cần authority nào?

A. Admin/Super Admin backend dependency  
B. Bất kỳ User có menu Admin  
C. Public token

### Câu 3 (trắc nghiệm)

Export response có thể là gì?

A. File response theo format, không nhất thiết JSON schema  
B. SSE  
C. Token response

### Câu 4 (tình huống)

Hãy trace import CSV từ template tới commit và nêu schema/job ID cần lưu ý.

### Câu 5 (tình huống)

Một call quality issues trả 403 cho data editor. Hãy nêu nơi xác minh trước khi coi là bug API.

## Đáp án, giải thích và bằng chứng mong đợi

1. **A.** Commit không nhận arbitrary raw catalog rows thay preview.
2. **A.** UI role không thay backend role dependency.
3. **A.** Đọc operation content type/format query.
4. Tải template → `POST /api/admin/imports/preview` → `ImportPreviewResponse`/job id/conflicts → `POST /api/admin/imports/{job_id}/commit` với `ImportCommitRequest`.
5. Đối chiếu role token/account active, frontend guard và router dependency; data editor phải có quyền data operation theo current role matrix.


Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
