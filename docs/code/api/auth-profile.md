# API — System, Auth, User, Profile và Nutrition

> Operation index và phần contract thay đổi được đối chiếu với code ngày 22/07/2026. Schema catalog phía dưới là snapshot cũ ngày 13/07/2026; OpenAPI runtime vẫn là nguồn máy đọc đầy đủ nhất.

## Operation index

| Method | Path | Request | Success response |
| --- | --- | --- | --- |
| POST | `/api/auth/google` | GoogleLoginRequest | 200: TokenResponse<br>422: HTTPValidationError |
| POST | `/api/auth/login` | Body_login_api_auth_login_post | 200: TokenResponse<br>422: HTTPValidationError |
| POST | `/api/auth/logout` |  | 200:  |
| GET | `/api/auth/me` |  | 200: UserResponse |
| POST | `/api/auth/register` | RegisterRequest | 201: UserResponse<br>422: HTTPValidationError |
| POST | `/api/nutrition/target` | NutritionProfileInput | 200: NutritionTargetResponse<br>422: HTTPValidationError |
| GET | `/api/profiles/{user_id}` |  | 200: ProfileResponse<br>422: HTTPValidationError |
| PUT | `/api/profiles/{user_id}` | ProfileUpdate | 200: ProfileResponse<br>422: HTTPValidationError |
| GET | `/api/profiles/{user_id}/exclusions` |  | 200: array<ExclusionResponse><br>422: HTTPValidationError |
| POST | `/api/profiles/{user_id}/exclusions` | ExclusionCreate | 201: ExclusionResponse<br>422: HTTPValidationError |
| DELETE | `/api/profiles/{user_id}/exclusions/{ingredient_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/profiles/me` |  | 200: ProfileResponse |
| PUT | `/api/profiles/me` | ProfileUpdate | 200: ProfileResponse<br>422: HTTPValidationError |
| GET | `/api/profiles/me/ai-preferences` |  | 200: AIPreferencesResponse |
| PUT | `/api/profiles/me/ai-preferences` | AIPreferencesUpdate | 200: AIPreferencesResponse<br>422: HTTPValidationError |
| GET | `/api/profiles/me/exclusions` |  | 200: array<ExclusionResponse> |
| POST | `/api/profiles/me/exclusions` | ExclusionCreate | 201: ExclusionResponse<br>422: HTTPValidationError |
| DELETE | `/api/profiles/me/exclusions/{ingredient_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/users` |  | 200: array<UserResponse><br>422: HTTPValidationError |
| POST | `/api/users` | UserCreate | 201: UserResponse<br>422: HTTPValidationError |
| DELETE | `/api/users/{user_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/users/{user_id}` |  | 200: UserResponse<br>422: HTTPValidationError |
| PUT | `/api/users/{user_id}` | UserUpdate | 200: UserResponse<br>422: HTTPValidationError |
| GET | `/health` |  | 200:  |
| GET | `/health/live` |  | 200:  |
| GET | `/health/ready` |  | 200:  |

## Parameters and content type
### `POST /api/auth/google`
No path/query parameter.
Request content type: `application/json`

### `POST /api/auth/login`
No path/query parameter.
Request content type: `application/x-www-form-urlencoded`

### `POST /api/auth/logout`
No path/query parameter.

### `GET /api/auth/me`
No path/query parameter.

### `POST /api/auth/register`
No path/query parameter.
Request content type: `application/json`

### `POST /api/nutrition/target`
No path/query parameter.
Request content type: `application/json`

### `GET /api/profiles/{user_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |

### `PUT /api/profiles/{user_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |
Request content type: `application/json`

### `GET /api/profiles/{user_id}/exclusions`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |

### `POST /api/profiles/{user_id}/exclusions`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |
Request content type: `application/json`

### `DELETE /api/profiles/{user_id}/exclusions/{ingredient_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |
| `ingredient_id` | path | True | integer |

### `GET /api/profiles/me`
No path/query parameter.

### `PUT /api/profiles/me`
No path/query parameter.
Request content type: `application/json`

### `GET /api/profiles/me/ai-preferences`

Không có path/query parameter. Identity luôn lấy từ access token. Khi chưa có row hoặc notice cũ, response an toàn là `personalization_enabled=false` với notice hiện hành.

### `PUT /api/profiles/me/ai-preferences`

Không có path/query parameter. Request content type: `application/json`.

```json
{
  "personalization_enabled": true,
  "notice_version": "2026-07-22"
}
```

`notice_version` phải đúng phiên bản backend hiện hành; bản cũ trả lỗi `AI_NOTICE_VERSION_STALE`. Mỗi lần bật/tắt đều ghi một consent event. Endpoint chỉ sửa quyền AI, không sửa profile, menu hay inventory.

Response:

```json
{
  "personalization_enabled": true,
  "notice_version": "2026-07-22",
  "consented_at": "2026-07-22T10:30:00Z",
  "updated_at": "2026-07-22T10:30:00Z"
}
```

### `GET /api/profiles/me/exclusions`
No path/query parameter.

### `POST /api/profiles/me/exclusions`
No path/query parameter.
Request content type: `application/json`

### `DELETE /api/profiles/me/exclusions/{ingredient_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `ingredient_id` | path | True | integer |

### `GET /api/users`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `POST /api/users`
No path/query parameter.
Request content type: `application/json`

### `DELETE /api/users/{user_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |

### `GET /api/users/{user_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |

### `PUT /api/users/{user_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `user_id` | path | True | integer |
Request content type: `application/json`

### `GET /health`
No path/query parameter.

### `GET /health/live`
No path/query parameter.

### `GET /health/ready`
No path/query parameter.

## Schema catalog
### `ActivityLevel`
```json
{
  "type": "string",
  "enum": [
    "sedentary",
    "light",
    "moderate",
    "active"
  ],
  "title": "ActivityLevel",
  "description": "Mức độ hoạt động thể chất với hệ số TDEE tương ứng"
}
```

### `Body_login_api_auth_login_post`
```json
{
  "properties": {
    "grant_type": {
      "anyOf": [
        {
          "type": "string",
          "pattern": "^password$"
        },
        {
          "type": "null"
        }
      ],
      "title": "Grant Type"
    },
    "username": {
      "type": "string",
      "title": "Username"
    },
    "password": {
      "type": "string",
      "format": "password",
      "title": "Password"
    },
    "scope": {
      "type": "string",
      "title": "Scope",
      "default": ""
    },
    "client_id": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Client Id"
    },
    "client_secret": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "format": "password",
      "title": "Client Secret"
    }
  },
  "type": "object",
  "required": [
    "username",
    "password"
  ],
  "title": "Body_login_api_auth_login_post"
}
```

### `ExclusionCreate`
```json
{
  "properties": {
    "ingredient_id": {
      "type": "integer",
      "title": "Ingredient Id"
    },
    "reason": {
      "$ref": "#/components/schemas/ExclusionReason",
      "default": "dislike"
    }
  },
  "type": "object",
  "required": [
    "ingredient_id"
  ],
  "title": "ExclusionCreate"
}
```

### `ExclusionReason`
```json
{
  "type": "string",
  "enum": [
    "allergy",
    "dislike"
  ],
  "title": "ExclusionReason",
  "description": "Lý do loại trừ nguyên liệu khỏi thực đơn của một người dùng."
}
```

### `ExclusionResponse`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "ingredient_id": {
      "type": "integer",
      "title": "Ingredient Id"
    },
    "reason": {
      "$ref": "#/components/schemas/ExclusionReason"
    }
  },
  "type": "object",
  "required": [
    "id",
    "ingredient_id",
    "reason"
  ],
  "title": "ExclusionResponse"
}
```

### `FitnessGoal`
```json
{
  "type": "string",
  "enum": [
    "maintain",
    "lose_weight",
    "gain_muscle",
    "gain_weight"
  ],
  "title": "FitnessGoal",
  "description": "Mục tiêu tập luyện của người dùng với việc điều chỉnh lượng calo tương ứng."
}
```

### `Gender`
```json
{
  "type": "string",
  "enum": [
    "male",
    "female"
  ],
  "title": "Gender",
  "description": "Giới tính sinh học được sử dụng để tính BMR"
}
```

### `GoogleLoginRequest`
```json
{
  "properties": {
    "credential": {
      "type": "string",
      "minLength": 1,
      "title": "Credential"
    }
  },
  "type": "object",
  "required": [
    "credential"
  ],
  "title": "GoogleLoginRequest"
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

### `NutritionProfileInput`
```json
{
  "properties": {
    "gender": {
      "$ref": "#/components/schemas/Gender",
      "description": "Biological sex: 'male' or 'female'."
    },
    "age": {
      "type": "integer",
      "maximum": 100.0,
      "minimum": 15.0,
      "title": "Age",
      "description": "Age in years (15–100)."
    },
    "weight_kg": {
      "type": "number",
      "maximum": 300.0,
      "minimum": 30.0,
      "title": "Weight Kg",
      "description": "Body weight in kilograms (30–300)."
    },
    "height_cm": {
      "type": "number",
      "maximum": 250.0,
      "minimum": 100.0,
      "title": "Height Cm",
      "description": "Height in centimeters (100–250)."
    },
    "activity_level": {
      "$ref": "#/components/schemas/ActivityLevel",
      "description": "Physical activity level: sedentary, light, moderate, or active."
    },
    "fitness_goal": {
      "$ref": "#/components/schemas/FitnessGoal",
      "description": "Fitness objective: maintain, lose_weight, gain_muscle, or gain_weight."
    }
  },
  "type": "object",
  "required": [
    "gender",
    "age",
    "weight_kg",
    "height_cm",
    "activity_level",
    "fitness_goal"
  ],
  "title": "NutritionProfileInput",
  "examples": [
    {
      "activity_level": "moderate",
      "age": 25,
      "fitness_goal": "maintain",
      "gender": "male",
      "height_cm": 175.0,
      "weight_kg": 70.0
    }
  ]
}
```

### `NutritionTargetResponse`
```json
{
  "properties": {
    "bmr": {
      "type": "number",
      "title": "Bmr",
      "description": "Basal Metabolic Rate (kcal), rounded to 1 decimal."
    },
    "tdee": {
      "type": "number",
      "title": "Tdee",
      "description": "Total Daily Energy Expenditure (kcal), rounded to 1 decimal."
    },
    "target_calories": {
      "type": "integer",
      "title": "Target Calories",
      "description": "Daily calorie target (kcal), rounded to integer."
    },
    "daily_protein_g": {
      "type": "number",
      "title": "Daily Protein G",
      "description": "Daily protein target (grams), rounded to 1 decimal."
    },
    "daily_fat_g": {
      "type": "number",
      "title": "Daily Fat G",
      "description": "Daily fat target (grams), rounded to 1 decimal."
    },
    "daily_carb_g": {
      "type": "number",
      "title": "Daily Carb G",
      "description": "Daily carbohydrate target (grams), rounded to 1 decimal."
    },
    "bmi": {
      "type": "number",
      "title": "Bmi",
      "description": "Body Mass Index, rounded to 1 decimal."
    },
    "is_feasible": {
      "type": "boolean",
      "title": "Is Feasible",
      "description": "False when target_calories is below the safe minimum (800 kcal). Planner should not proceed with an infeasible target.",
      "default": true
    },
    "warnings": {
      "items": {
        "$ref": "#/components/schemas/NutritionWarningResponse"
      },
      "type": "array",
      "title": "Warnings",
      "description": "Structured safety warnings with code and message."
    }
  },
  "type": "object",
  "required": [
    "bmr",
    "tdee",
    "target_calories",
    "daily_protein_g",
    "daily_fat_g",
    "daily_carb_g",
    "bmi"
  ],
  "title": "NutritionTargetResponse",
  "description": "Output DTO representing the calculated daily nutrition target."
}
```

### `NutritionWarningCode`
```json
{
  "type": "string",
  "enum": [
    "BMI_UNDERWEIGHT",
    "BMI_OBESE",
    "LOW_CALORIE_TARGET",
    "HIGH_CALORIE_TARGET",
    "INFEASIBLE_CALORIE_TARGET"
  ],
  "title": "NutritionWarningCode"
}
```

### `NutritionWarningResponse`
```json
{
  "properties": {
    "code": {
      "$ref": "#/components/schemas/NutritionWarningCode",
      "description": "Machine-readable warning code."
    },
    "message": {
      "type": "string",
      "title": "Message",
      "description": "Human-readable warning message in Vietnamese."
    }
  },
  "type": "object",
  "required": [
    "code",
    "message"
  ],
  "title": "NutritionWarningResponse"
}
```

### `ProfileResponse`
```json
{
  "properties": {
    "user_id": {
      "type": "integer",
      "title": "User Id"
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
    "gender": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/Gender"
        },
        {
          "type": "null"
        }
      ]
    },
    "age": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Age"
    },
    "height_cm": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Height Cm"
    },
    "weight_kg": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Weight Kg"
    },
    "activity_level": {
      "$ref": "#/components/schemas/ActivityLevel"
    },
    "goal": {
      "$ref": "#/components/schemas/FitnessGoal"
    },
    "meals_per_day": {
      "type": "integer",
      "title": "Meals Per Day"
    },
    "daily_calorie_target": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Daily Calorie Target"
    },
    "daily_budget": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Daily Budget"
    }
  },
  "type": "object",
  "required": [
    "user_id",
    "full_name",
    "gender",
    "age",
    "height_cm",
    "weight_kg",
    "activity_level",
    "goal",
    "meals_per_day",
    "daily_calorie_target",
    "daily_budget"
  ],
  "title": "ProfileResponse"
}
```

### `ProfileUpdate`
```json
{
  "properties": {
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
    "gender": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/Gender"
        },
        {
          "type": "null"
        }
      ]
    },
    "age": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Age"
    },
    "height_cm": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Height Cm"
    },
    "weight_kg": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Weight Kg"
    },
    "activity_level": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/ActivityLevel"
        },
        {
          "type": "null"
        }
      ]
    },
    "goal": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/FitnessGoal"
        },
        {
          "type": "null"
        }
      ]
    },
    "meals_per_day": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Meals Per Day"
    },
    "daily_calorie_target": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Daily Calorie Target"
    },
    "daily_budget": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Daily Budget"
    }
  },
  "type": "object",
  "title": "ProfileUpdate"
}
```

### `RegisterRequest`
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
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Full Name"
    }
  },
  "type": "object",
  "required": [
    "email",
    "password"
  ],
  "title": "RegisterRequest"
}
```

### `TokenResponse`
```json
{
  "properties": {
    "access_token": {
      "type": "string",
      "title": "Access Token"
    },
    "token_type": {
      "type": "string",
      "title": "Token Type",
      "default": "bearer"
    }
  },
  "type": "object",
  "required": [
    "access_token"
  ],
  "title": "TokenResponse"
}
```

### `UserCreate`
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
    "role": {
      "$ref": "#/components/schemas/UserRole",
      "default": "user"
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
    }
  },
  "type": "object",
  "required": [
    "email",
    "password"
  ],
  "title": "UserCreate"
}
```

### `UserResponse`
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
    "role": {
      "$ref": "#/components/schemas/UserRole"
    },
    "is_active": {
      "type": "boolean",
      "title": "Is Active"
    }
  },
  "type": "object",
  "required": [
    "id",
    "email",
    "role",
    "is_active"
  ],
  "title": "UserResponse"
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

### `UserUpdate`
```json
{
  "properties": {
    "email": {
      "anyOf": [
        {
          "type": "string",
          "format": "email"
        },
        {
          "type": "null"
        }
      ],
      "title": "Email"
    },
    "password": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128,
          "minLength": 8
        },
        {
          "type": "null"
        }
      ],
      "title": "Password"
    },
    "role": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/UserRole"
        },
        {
          "type": "null"
        }
      ]
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
  "title": "UserUpdate"
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

Login dùng content type nào?

A. `application/x-www-form-urlencoded`  
B. `text/event-stream`  
C. `multipart/mixed`

### Câu 2 (trắc nghiệm)

Body lỗi validation chuẩn là schema nào?

A. `HTTPValidationError`  
B. `TokenResponse`  
C. `ProfileResponse`

### Câu 3 (trắc nghiệm)

`/health/ready` khác `/health/live` vì gì?

A. Ready kiểm database  
B. Live đổi role  
C. Ready tạo token

### Câu 4 (tình huống)

Hãy trace request thêm exclusion của User và nêu parameter/body schema cần xem.

### Câu 5 (tình huống)

Nếu thêm field profile, hãy nêu hai endpoint profile và schema phải đối chiếu.

## Đáp án, giải thích và bằng chứng mong đợi

1. **A.** OAuth2 password form body dùng form-urlencoded.
2. **A.** Xem JSON Schema `HTTPValidationError` và `ValidationError`.
3. **A.** Ready chạy kiểm tra kết nối database.
4. `POST /api/profiles/me/exclusions`, body `ExclusionCreate`; với admin/user-id route còn có path `user_id`.
5. `GET`/`PUT /api/profiles/me` và biến thể `{user_id}`; kiểm `ProfileResponse`, `ProfileUpdate`, OpenAPI required/nullable và frontend profile type.

Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
