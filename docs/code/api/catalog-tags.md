# API — Catalog, Dish, Meal và Tag

> Full schema catalog được sao chép từ OpenAPI runtime ngày 13/07/2026. `401`, `403`, `404`, `422` và `{ "detail": string }` áp dụng theo authentication, quyền, ownership, target và validation.

## Operation index

| Method | Path | Request | Success response |
| --- | --- | --- | --- |
| GET | `/api/admin/tags` |  | 200: array<TagResponse><br>422: HTTPValidationError |
| POST | `/api/admin/tags` | TagCreate | 201: TagResponse<br>422: HTTPValidationError |
| PUT | `/api/admin/tags/{tag_id}` | TagNameWrite | 200: TagResponse<br>422: HTTPValidationError |
| PATCH | `/api/admin/tags/{tag_id}/active` | TagActiveUpdate | 200: TagResponse<br>422: HTTPValidationError |
| GET | `/api/dishes` |  | 200: array<DishSummaryResponse><br>422: HTTPValidationError |
| GET | `/api/dishes/{dish_id}` |  | 200: DishDetailResponse<br>422: HTTPValidationError |
| GET | `/api/ingredients` |  | 200: array<IngredientResponse><br>422: HTTPValidationError |
| POST | `/api/ingredients` | IngredientCreate | 201: IngredientResponse<br>422: HTTPValidationError |
| DELETE | `/api/ingredients/{ingredient_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/ingredients/{ingredient_id}` |  | 200: IngredientResponse<br>422: HTTPValidationError |
| PUT | `/api/ingredients/{ingredient_id}` | IngredientUpdate | 200: IngredientResponse<br>422: HTTPValidationError |
| GET | `/api/meals` |  | 200: array<MealSummary><br>422: HTTPValidationError |
| POST | `/api/meals` | MealCreate | 201: MealDetail<br>422: HTTPValidationError |
| DELETE | `/api/meals/{meal_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/meals/{meal_id}` |  | 200: MealDetail<br>422: HTTPValidationError |
| PUT | `/api/meals/{meal_id}` | MealUpdate | 200: MealDetail<br>422: HTTPValidationError |
| GET | `/api/tags` |  | 200: array<TagResponse> |

## Parameters and content type
### `GET /api/admin/tags`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `search` | query | False |  |
| `entity_type` | query | False |  |

### `POST /api/admin/tags`
No path/query parameter.
Request content type: `application/json`

### `PUT /api/admin/tags/{tag_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `tag_id` | path | True | integer |
Request content type: `application/json`

### `PATCH /api/admin/tags/{tag_id}/active`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `tag_id` | path | True | integer |
Request content type: `application/json`

### `GET /api/dishes`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `search` | query | False |  |
| `dish_type` | query | False |  |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `GET /api/dishes/{dish_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `dish_id` | path | True | integer |

### `GET /api/ingredients`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `food_group` | query | False |  |
| `search` | query | False |  |
| `active_only` | query | False | boolean |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `POST /api/ingredients`
No path/query parameter.
Request content type: `application/json`

### `DELETE /api/ingredients/{ingredient_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `ingredient_id` | path | True | integer |

### `GET /api/ingredients/{ingredient_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `ingredient_id` | path | True | integer |

### `PUT /api/ingredients/{ingredient_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `ingredient_id` | path | True | integer |
Request content type: `application/json`

### `GET /api/meals`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `meal_type` | query | False |  |
| `search` | query | False |  |
| `active_only` | query | False | boolean |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `POST /api/meals`
No path/query parameter.
Request content type: `application/json`

### `DELETE /api/meals/{meal_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `meal_id` | path | True | integer |

### `GET /api/meals/{meal_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `meal_id` | path | True | integer |

### `PUT /api/meals/{meal_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `meal_id` | path | True | integer |
Request content type: `application/json`

### `GET /api/tags`
No path/query parameter.

## Schema catalog
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

### `DishDetailResponse`
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
    "tags": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Tags"
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
    "ingredients": {
      "items": {
        "$ref": "#/components/schemas/DishIngredientResponse"
      },
      "type": "array",
      "title": "Ingredients"
    }
  },
  "type": "object",
  "required": [
    "id",
    "name",
    "dish_type",
    "total_calories",
    "total_protein_g",
    "total_carbs_g",
    "total_fat_g",
    "estimated_cost"
  ],
  "title": "DishDetailResponse"
}
```

### `DishIngredientResponse`
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
    "estimated_cost": {
      "type": "number",
      "title": "Estimated Cost",
      "default": 0
    }
  },
  "type": "object",
  "required": [
    "ingredient_id",
    "name",
    "quantity",
    "unit"
  ],
  "title": "DishIngredientResponse"
}
```

### `DishSummaryResponse`
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
    "tags": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Tags"
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
    }
  },
  "type": "object",
  "required": [
    "id",
    "name",
    "dish_type",
    "total_calories",
    "total_protein_g",
    "total_carbs_g",
    "total_fat_g",
    "estimated_cost"
  ],
  "title": "DishSummaryResponse"
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

### `IngredientCreate`
```json
{
  "properties": {
    "name": {
      "type": "string",
      "title": "Name"
    },
    "food_group": {
      "$ref": "#/components/schemas/FoodGroup"
    },
    "default_unit": {
      "type": "string",
      "title": "Default Unit",
      "default": "g"
    },
    "grams_per_unit": {
      "type": "number",
      "title": "Grams Per Unit",
      "default": 1
    },
    "nutrition": {
      "$ref": "#/components/schemas/NutritionInput",
      "default": {
        "calories": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "fiber_g": 0.0
      }
    }
  },
  "type": "object",
  "required": [
    "name",
    "food_group"
  ],
  "title": "IngredientCreate"
}
```

### `IngredientResponse`
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
    }
  },
  "type": "object",
  "required": [
    "id",
    "name",
    "food_group",
    "default_unit",
    "grams_per_unit",
    "is_active"
  ],
  "title": "IngredientResponse"
}
```

### `IngredientUpdate`
```json
{
  "properties": {
    "name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Name"
    },
    "food_group": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/FoodGroup"
        },
        {
          "type": "null"
        }
      ]
    },
    "default_unit": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Default Unit"
    },
    "grams_per_unit": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Grams Per Unit"
    },
    "is_active": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Is Active"
    }
  },
  "type": "object",
  "title": "IngredientUpdate"
}
```

### `MealCreate`
```json
{
  "properties": {
    "name": {
      "type": "string",
      "title": "Name"
    },
    "meal_type": {
      "$ref": "#/components/schemas/MealType"
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
    "servings": {
      "type": "integer",
      "title": "Servings",
      "default": 1
    },
    "tags": {
      "items": {},
      "type": "array",
      "title": "Tags",
      "default": []
    },
    "components": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Components",
      "default": []
    },
    "ingredients": {
      "items": {
        "$ref": "#/components/schemas/MealIngredientInput"
      },
      "type": "array",
      "title": "Ingredients",
      "default": []
    }
  },
  "type": "object",
  "required": [
    "name",
    "meal_type"
  ],
  "title": "MealCreate"
}
```

### `MealDetail`
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
    "meal_type": {
      "$ref": "#/components/schemas/MealType"
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
    "servings": {
      "type": "integer",
      "title": "Servings"
    },
    "tags": {
      "items": {},
      "type": "array",
      "title": "Tags",
      "default": []
    },
    "components": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Components",
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
    "ingredients": {
      "items": {
        "$ref": "#/components/schemas/MealIngredientResponse"
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
    "meal_type",
    "servings",
    "is_active",
    "total_calories",
    "total_protein_g",
    "total_carbs_g",
    "total_fat_g",
    "estimated_cost"
  ],
  "title": "MealDetail"
}
```

### `MealIngredientInput`
```json
{
  "properties": {
    "ingredient_id": {
      "type": "integer",
      "title": "Ingredient Id"
    },
    "quantity": {
      "type": "number",
      "title": "Quantity"
    },
    "unit": {
      "type": "string",
      "title": "Unit",
      "default": "g"
    }
  },
  "type": "object",
  "required": [
    "ingredient_id",
    "quantity"
  ],
  "title": "MealIngredientInput"
}
```

### `MealIngredientResponse`
```json
{
  "properties": {
    "ingredient_id": {
      "type": "integer",
      "title": "Ingredient Id"
    },
    "name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Name"
    },
    "quantity": {
      "type": "number",
      "title": "Quantity"
    },
    "unit": {
      "type": "string",
      "title": "Unit"
    }
  },
  "type": "object",
  "required": [
    "ingredient_id",
    "quantity",
    "unit"
  ],
  "title": "MealIngredientResponse"
}
```

### `MealSummary`
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
    "meal_type": {
      "$ref": "#/components/schemas/MealType"
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
    "servings": {
      "type": "integer",
      "title": "Servings"
    },
    "tags": {
      "items": {},
      "type": "array",
      "title": "Tags",
      "default": []
    },
    "components": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Components",
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
    }
  },
  "type": "object",
  "required": [
    "id",
    "name",
    "meal_type",
    "servings",
    "is_active",
    "total_calories",
    "total_protein_g",
    "total_carbs_g",
    "total_fat_g",
    "estimated_cost"
  ],
  "title": "MealSummary"
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

### `MealUpdate`
```json
{
  "properties": {
    "name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Name"
    },
    "meal_type": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/MealType"
        },
        {
          "type": "null"
        }
      ]
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
    "servings": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Servings"
    },
    "tags": {
      "anyOf": [
        {
          "items": {},
          "type": "array"
        },
        {
          "type": "null"
        }
      ],
      "title": "Tags"
    },
    "components": {
      "anyOf": [
        {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        {
          "type": "null"
        }
      ],
      "title": "Components"
    },
    "is_active": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Is Active"
    }
  },
  "type": "object",
  "title": "MealUpdate"
}
```

### `NutritionInput`
```json
{
  "properties": {
    "calories": {
      "type": "number",
      "title": "Calories",
      "default": 0
    },
    "protein_g": {
      "type": "number",
      "title": "Protein G",
      "default": 0
    },
    "carbs_g": {
      "type": "number",
      "title": "Carbs G",
      "default": 0
    },
    "fat_g": {
      "type": "number",
      "title": "Fat G",
      "default": 0
    },
    "fiber_g": {
      "type": "number",
      "title": "Fiber G",
      "default": 0
    }
  },
  "type": "object",
  "title": "NutritionInput"
}
```

### `TagActiveUpdate`
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
  "title": "TagActiveUpdate"
}
```

### `TagCreate`
```json
{
  "properties": {
    "name": {
      "type": "string",
      "maxLength": 64,
      "minLength": 1,
      "title": "Name"
    },
    "entity_type": {
      "type": "string",
      "enum": [
        "ingredient",
        "dish"
      ],
      "title": "Entity Type"
    }
  },
  "type": "object",
  "required": [
    "name",
    "entity_type"
  ],
  "title": "TagCreate"
}
```

### `TagNameWrite`
```json
{
  "properties": {
    "name": {
      "type": "string",
      "maxLength": 64,
      "minLength": 1,
      "title": "Name"
    }
  },
  "type": "object",
  "required": [
    "name"
  ],
  "title": "TagNameWrite"
}
```

### `TagResponse`
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
    "entity_type": {
      "type": "string",
      "enum": [
        "ingredient",
        "dish"
      ],
      "title": "Entity Type"
    },
    "is_active": {
      "type": "boolean",
      "title": "Is Active"
    }
  },
  "type": "object",
  "required": [
    "id",
    "name",
    "entity_type",
    "is_active"
  ],
  "title": "TagResponse"
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

Catalog User dishes đọc từ đâu?

A. `v_dish_candidates`  
B. Raw `meals`  
C. AI response

### Câu 2 (trắc nghiệm)

Tag `dish` và `ingredient` có thể trùng tên không?

A. Có, nếu entity type khác  
B. Không  
C. Chỉ với Super Admin

### Câu 3 (trắc nghiệm)

Operation deactivate thường trả gì?

A. Schema item cập nhật hoặc 204 theo endpoint  
B. Access token mới  
C. SSE stream

### Câu 4 (tình huống)

Hãy xác định request/response schema khi tạo ingredient Admin so với endpoint ingredient cũ.

### Câu 5 (tình huống)

Một dish detail trả 404 cho User. Hãy nêu contract/data condition cần kiểm tra.

## Đáp án, giải thích và bằng chứng mong đợi

1. **A.** View bảo vệ readiness của planner.
2. **A.** Typed tag catalog tách namespace.
3. **A.** Đọc từng row operation thay vì suy đoán mọi deactivate cùng response.
4. So `POST /api/admin/ingredients` (`AdminIngredientWrite`/`AdminIngredientItem`) với `/api/ingredients` (`IngredientCreate`/`IngredientResponse`) và role requirement.
5. `GET /api/dishes/{dish_id}` chỉ trả dish qua candidate view; kiểm active/recipe/ingredient/nutrition/price và schema `DishDetailResponse`.


Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
