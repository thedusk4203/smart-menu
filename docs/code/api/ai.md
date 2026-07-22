# API — AI User và Admin Provider

> Operation index và phần contract thay đổi được đối chiếu với code ngày 22/07/2026. Schema catalog phía dưới là snapshot cũ ngày 13/07/2026; khi có khác biệt, phần “Contract AI hiện tại” và OpenAPI runtime là nguồn đúng.

## Operation index

| Method | Path | Request | Success response |
| --- | --- | --- | --- |
| GET | `/api/admin/ai/logs` |  | 200: AILogPage<br>422: HTTPValidationError |
| GET | `/api/admin/ai/logs/{log_id}` |  | 200: AILogDetail<br>422: HTTPValidationError |
| POST | `/api/admin/ai/logs/purge` | PurgeLogsRequest | 200: PurgeLogsResponse<br>422: HTTPValidationError |
| GET | `/api/admin/ai/prompts` |  | 200: array<SystemPromptItem> |
| PUT | `/api/admin/ai/prompts/{feature}` | SystemPromptWrite | 200: SystemPromptItem<br>422: HTTPValidationError |
| DELETE | `/api/admin/ai/prompts/{feature}` |  | 200: SystemPromptItem<br>422: HTTPValidationError |
| GET | `/api/admin/ai/providers` |  | 200: array<ProviderItem> |
| POST | `/api/admin/ai/providers` | ProviderWrite | 201: ProviderItem<br>422: HTTPValidationError |
| DELETE | `/api/admin/ai/providers/{config_id}` |  | 204: no body<br>422: HTTPValidationError |
| PUT | `/api/admin/ai/providers/{config_id}` | ProviderWrite | 200: ProviderItem<br>422: HTTPValidationError |
| POST | `/api/admin/ai/providers/{config_id}/activate` |  | 200: ProviderItem<br>422: HTTPValidationError |
| POST | `/api/admin/ai/providers/{config_id}/clone` |  | 200: ProviderItem<br>422: HTTPValidationError |
| POST | `/api/admin/ai/providers/{config_id}/deactivate` |  | 200: ProviderItem<br>422: HTTPValidationError |
| POST | `/api/admin/ai/providers/{config_id}/discover-models` |  | 200: array<br>422: HTTPValidationError |
| POST | `/api/admin/ai/providers/{config_id}/test` |  | 200: ProviderTestResult<br>422: HTTPValidationError |
| POST | `/api/ai/chat` | ChatRequest | 200: <br>422: HTTPValidationError |
| GET | `/api/ai/conversations` |  | 200: array<ConversationSummary> |
| DELETE | `/api/ai/conversations/{conversation_id}` |  | 204: no body<br>422: HTTPValidationError |
| GET | `/api/ai/conversations/{conversation_id}` |  | 200: ConversationDetail<br>422: HTTPValidationError |
| POST | `/api/ai/conversations/{conversation_id}/turns/{turn_id}/retry` |  | 200: <br>422: HTTPValidationError |
| POST | `/api/ai/explain-plan` | ExplainPlanRequest | 200: ExplainPlanResponse<br>422: HTTPValidationError |
| POST | `/api/ai/parse-menu-request` | ParseMenuRequest | 200: ParsedMenuRequest<br>422: HTTPValidationError |
| GET | `/api/ai/status` |  | 200: AIStatus |
| POST | `/api/ai/suggest-swap` | SwapSuggestionRequest | 200: array<SwapSuggestion><br>422: HTTPValidationError |

## Contract AI hiện tại (22/07/2026)

### Chat, mode và dữ liệu cá nhân

`ChatRequest` có `message`, `conversation_id` và `mode`. `mode` mặc định là `general` và chỉ nhận một trong ba giá trị:

| Mode | Có đọc hồ sơ? | Dữ liệu được phép dùng | Grounding |
| --- | --- | --- | --- |
| `general` | Không | Chỉ nội dung hội thoại | `none` |
| `meal_advice` | Có, nếu đã consent | Mục tiêu, mức vận động, số bữa, calorie, ngân sách, exclusions | `none` |
| `health_reference` | Có, nếu đã consent và tuổi ≥ 18 | Như meal advice, thêm tuổi, giới tính, chiều cao, cân nặng | Web search native hoặc fallback có nhãn |

Một conversation giữ nguyên mode từ lúc tạo; client không được đổi mode giữa chừng bằng cách gửi lại cùng `conversation_id`. `ConversationSummary` có thêm `mode`. Mỗi `ConversationTurn` và event SSE `done` có:

- `personalization_used`: có thực sự đưa context cá nhân vào prompt hay không;
- `grounding_mode`: `none`, `native_web_search` hoặc `model_fallback`;
- `citations`: tối đa 10 phần tử `{title, url}`, URL chỉ nhận `http`/`https`.

Các lỗi nghiệp vụ quan trọng: `AI_PERSONALIZATION_CONSENT_REQUIRED`, `AI_PROFILE_REQUIRED`, `AI_HEALTH_AGE_RESTRICTED`. UI nên dùng message thân thiện từ lỗi, không tự suy diễn rằng mọi lỗi đều do provider.

### Parse tag và provider grounding

`ParsedMenuRequest` có thêm `unresolved_tags`. Backend chỉ giữ tag khớp chính xác với `tag_catalog` đang active trong `preferred_tags`; tag AI đoán nhưng không tồn tại được chuyển sang `unresolved_tags`, không truyền thẳng vào optimizer.

`ProviderWrite`/`ProviderItem` có `native_web_search_enabled`; `ProviderItem` còn có `capability_checked_at`. Khi bật capability, thao tác test provider chỉ pass nếu nhận được citation hợp lệ. Log thay đoạn message chứa marker `[PERSONAL_CONTEXT]` bằng `[PERSONAL_CONTEXT_REDACTED]`; đây là redaction có mục tiêu, không phải bộ lọc PII tổng quát cho mọi nội dung người dùng gõ.

## Parameters and content type
### `GET /api/admin/ai/logs`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `feature` | query | False |  |
| `status` | query | False |  |
| `user_id` | query | False |  |
| `limit` | query | False | integer |
| `offset` | query | False | integer |

### `GET /api/admin/ai/logs/{log_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `log_id` | path | True | integer |

### `POST /api/admin/ai/logs/purge`
No path/query parameter.
Request content type: `application/json`

### `GET /api/admin/ai/prompts`
No path/query parameter. Chỉ Super Admin; trả đủ bốn feature theo thứ tự ổn định.

### `PUT /api/admin/ai/prompts/{feature}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `feature` | path | True | `chat`, `parse_menu`, `explain_plan`, `suggest_swap` |

Request content type: `application/json`; `content` sau trim dài từ 1 đến 20.000 ký tự. Override áp dụng từ request kế tiếp và không thay đổi provider version/test status.

### `DELETE /api/admin/ai/prompts/{feature}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `feature` | path | True | `chat`, `parse_menu`, `explain_plan`, `suggest_swap` |

Xóa override và trả prompt mặc định đang có hiệu lực.

### `GET /api/admin/ai/providers`
No path/query parameter.

### `POST /api/admin/ai/providers`
No path/query parameter.
Request content type: `application/json`

### `DELETE /api/admin/ai/providers/{config_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `config_id` | path | True | integer |

### `PUT /api/admin/ai/providers/{config_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `config_id` | path | True | integer |
Request content type: `application/json`

### `POST /api/admin/ai/providers/{config_id}/activate`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `config_id` | path | True | integer |

### `POST /api/admin/ai/providers/{config_id}/clone`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `config_id` | path | True | integer |

### `POST /api/admin/ai/providers/{config_id}/deactivate`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `config_id` | path | True | integer |

### `POST /api/admin/ai/providers/{config_id}/discover-models`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `config_id` | path | True | integer |

### `POST /api/admin/ai/providers/{config_id}/test`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `config_id` | path | True | integer |

### `POST /api/ai/chat`
No path/query parameter.
Request content type: `application/json`

### `GET /api/ai/conversations`
No path/query parameter.

### `DELETE /api/ai/conversations/{conversation_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `conversation_id` | path | True | integer |

### `GET /api/ai/conversations/{conversation_id}`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `conversation_id` | path | True | integer |

### `POST /api/ai/conversations/{conversation_id}/turns/{turn_id}/retry`
| Parameter | In | Required | Schema |
| --- | --- | --- | --- |
| `conversation_id` | path | True | integer |
| `turn_id` | path | True | integer |

### `POST /api/ai/explain-plan`
No path/query parameter.
Request content type: `application/json`

### `POST /api/ai/parse-menu-request`
No path/query parameter.
Request content type: `application/json`

### `GET /api/ai/status`
No path/query parameter.

### `POST /api/ai/suggest-swap`
No path/query parameter.
Request content type: `application/json`

## System prompt contracts

`SystemPromptItem` gồm `feature`, `content`, `is_custom`, `updated_at`. `SystemPromptWrite` chỉ gồm `content`.

Prompt được quản lý toàn cục, tách khỏi provider. Backend vẫn giữ JSON schema, deterministic parser/fallback và constraint checker làm nguồn kiểm chứng; chỉnh prompt không được phép thay thế các rào chắn này.

## Schema catalog
### `AILogDetail`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "user_id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "User Id"
    },
    "provider_config_id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Provider Config Id"
    },
    "feature": {
      "type": "string",
      "title": "Feature"
    },
    "provider_type": {
      "type": "string",
      "title": "Provider Type"
    },
    "model": {
      "type": "string",
      "title": "Model"
    },
    "status": {
      "type": "string",
      "title": "Status"
    },
    "latency_ms": {
      "type": "integer",
      "title": "Latency Ms"
    },
    "prompt_tokens": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Prompt Tokens"
    },
    "completion_tokens": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Completion Tokens"
    },
    "total_tokens": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Total Tokens"
    },
    "error_message": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Error Message"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "title": "Created At"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time",
      "title": "Expires At"
    },
    "request_data": {
      "additionalProperties": true,
      "type": "object",
      "title": "Request Data"
    },
    "response_data": {
      "anyOf": [
        {},
        {
          "type": "null"
        }
      ],
      "title": "Response Data"
    }
  },
  "type": "object",
  "required": [
    "id",
    "user_id",
    "provider_config_id",
    "feature",
    "provider_type",
    "model",
    "status",
    "latency_ms",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "error_message",
    "created_at",
    "expires_at",
    "request_data",
    "response_data"
  ],
  "title": "AILogDetail"
}
```

### `AILogItem`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "user_id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "User Id"
    },
    "provider_config_id": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Provider Config Id"
    },
    "feature": {
      "type": "string",
      "title": "Feature"
    },
    "provider_type": {
      "type": "string",
      "title": "Provider Type"
    },
    "model": {
      "type": "string",
      "title": "Model"
    },
    "status": {
      "type": "string",
      "title": "Status"
    },
    "latency_ms": {
      "type": "integer",
      "title": "Latency Ms"
    },
    "prompt_tokens": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Prompt Tokens"
    },
    "completion_tokens": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Completion Tokens"
    },
    "total_tokens": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Total Tokens"
    },
    "error_message": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Error Message"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "title": "Created At"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time",
      "title": "Expires At"
    }
  },
  "type": "object",
  "required": [
    "id",
    "user_id",
    "provider_config_id",
    "feature",
    "provider_type",
    "model",
    "status",
    "latency_ms",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "error_message",
    "created_at",
    "expires_at"
  ],
  "title": "AILogItem"
}
```

### `AILogPage`
```json
{
  "properties": {
    "items": {
      "items": {
        "$ref": "#/components/schemas/AILogItem"
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
  "title": "AILogPage"
}
```

### `AIStatus`
```json
{
  "properties": {
    "enabled": {
      "type": "boolean",
      "title": "Enabled"
    },
    "source": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Source"
    },
    "provider_name": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Provider Name"
    },
    "provider_type": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Provider Type"
    },
    "model": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Model"
    },
    "features": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Features"
    }
  },
  "type": "object",
  "required": [
    "enabled"
  ],
  "title": "AIStatus"
}
```

### `ChatMessage`
```json
{
  "properties": {
    "role": {
      "type": "string",
      "enum": [
        "user",
        "assistant"
      ],
      "title": "Role"
    },
    "content": {
      "type": "string",
      "maxLength": 4000,
      "minLength": 1,
      "title": "Content"
    }
  },
  "type": "object",
  "required": [
    "role",
    "content"
  ],
  "title": "ChatMessage"
}
```

### `ChatRequest`
```json
{
  "properties": {
    "message": {
      "type": "string",
      "maxLength": 4000,
      "minLength": 1,
      "title": "Message"
    },
    "conversation_id": {
      "anyOf": [
        {
          "type": "integer",
          "exclusiveMinimum": 0.0
        },
        {
          "type": "null"
        }
      ],
      "title": "Conversation Id"
    },
    "context": {
      "anyOf": [
        {},
        {
          "type": "null"
        }
      ],
      "title": "Context"
    },
    "history": {
      "items": {
        "$ref": "#/components/schemas/ChatMessage"
      },
      "type": "array",
      "maxItems": 10,
      "title": "History"
    }
  },
  "type": "object",
  "required": [
    "message"
  ],
  "title": "ChatRequest"
}
```

### `ConversationDetail`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "turn_count": {
      "type": "integer",
      "maximum": 20.0,
      "minimum": 0.0,
      "title": "Turn Count"
    },
    "last_message_preview": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Last Message Preview"
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
    "turns": {
      "items": {
        "$ref": "#/components/schemas/ConversationTurn"
      },
      "type": "array",
      "title": "Turns"
    }
  },
  "type": "object",
  "required": [
    "id",
    "title",
    "turn_count",
    "created_at",
    "updated_at",
    "turns"
  ],
  "title": "ConversationDetail"
}
```

### `ConversationSummary`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "title": {
      "type": "string",
      "title": "Title"
    },
    "turn_count": {
      "type": "integer",
      "maximum": 20.0,
      "minimum": 0.0,
      "title": "Turn Count"
    },
    "last_message_preview": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Last Message Preview"
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
    "title",
    "turn_count",
    "created_at",
    "updated_at"
  ],
  "title": "ConversationSummary"
}
```

### `ConversationTurn`
```json
{
  "properties": {
    "id": {
      "type": "integer",
      "title": "Id"
    },
    "turn_number": {
      "type": "integer",
      "maximum": 20.0,
      "minimum": 1.0,
      "title": "Turn Number"
    },
    "user_content": {
      "type": "string",
      "title": "User Content"
    },
    "assistant_content": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Assistant Content"
    },
    "status": {
      "type": "string",
      "enum": [
        "pending",
        "completed",
        "failed"
      ],
      "title": "Status"
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
    "turn_number",
    "user_content",
    "status",
    "created_at",
    "updated_at"
  ],
  "title": "ConversationTurn"
}
```

### `ExplainPlanRequest`
```json
{
  "properties": {
    "plan_data": {
      "additionalProperties": true,
      "type": "object",
      "title": "Plan Data"
    },
    "total_cost": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Total Cost"
    },
    "total_calories": {
      "anyOf": [
        {
          "type": "number"
        },
        {
          "type": "null"
        }
      ],
      "title": "Total Calories"
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
    }
  },
  "type": "object",
  "required": [
    "plan_data"
  ],
  "title": "ExplainPlanRequest"
}
```

### `ExplainPlanResponse`
```json
{
  "properties": {
    "summary": {
      "type": "string",
      "maxLength": 500,
      "minLength": 20,
      "title": "Summary"
    },
    "budget_assessment": {
      "type": "string",
      "maxLength": 400,
      "minLength": 10,
      "title": "Budget Assessment"
    },
    "nutrition_assessment": {
      "type": "string",
      "maxLength": 400,
      "minLength": 10,
      "title": "Nutrition Assessment"
    },
    "highlights": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "maxItems": 3,
      "minItems": 1,
      "title": "Highlights"
    },
    "cautions": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "maxItems": 3,
      "title": "Cautions"
    },
    "recommendations": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "maxItems": 3,
      "minItems": 1,
      "title": "Recommendations"
    },
    "reply": {
      "type": "string",
      "title": "Reply"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "summary",
    "budget_assessment",
    "nutrition_assessment",
    "highlights",
    "recommendations",
    "reply"
  ],
  "title": "ExplainPlanResponse"
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

### `ParsedMenuRequest`
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
          "maximum": 3.0,
          "minimum": 2.0
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
          "minimum": 0.0
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
      "title": "Preferred Tags"
    },
    "needs_clarification": {
      "type": "boolean",
      "title": "Needs Clarification",
      "default": false
    },
    "clarification_question": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Clarification Question"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "title": "ParsedMenuRequest"
}
```

### `ParseMenuRequest`
```json
{
  "properties": {
    "message": {
      "type": "string",
      "maxLength": 4000,
      "minLength": 1,
      "title": "Message"
    }
  },
  "type": "object",
  "required": [
    "message"
  ],
  "title": "ParseMenuRequest"
}
```

### `ProviderItem`
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
    "provider_type": {
      "type": "string",
      "enum": [
        "openai",
        "deepseek",
        "lmstudio",
        "google",
        "custom"
      ],
      "title": "Provider Type"
    },
    "base_url": {
      "type": "string",
      "title": "Base Url"
    },
    "model": {
      "type": "string",
      "title": "Model"
    },
    "has_api_key": {
      "type": "boolean",
      "title": "Has Api Key"
    },
    "masked_api_key": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Masked Api Key"
    },
    "timeout_seconds": {
      "type": "number",
      "title": "Timeout Seconds"
    },
    "structured_output_mode": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Structured Output Mode"
    },
    "config_version": {
      "type": "integer",
      "title": "Config Version"
    },
    "tested_version": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Tested Version"
    },
    "test_status": {
      "type": "string",
      "title": "Test Status"
    },
    "last_tested_at": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Last Tested At"
    },
    "last_test_error": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Last Test Error"
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
    "name",
    "provider_type",
    "base_url",
    "model",
    "has_api_key",
    "timeout_seconds",
    "config_version",
    "test_status",
    "is_active",
    "created_at",
    "updated_at"
  ],
  "title": "ProviderItem"
}
```

### `ProviderTestResult`
```json
{
  "properties": {
    "provider": {
      "$ref": "#/components/schemas/ProviderItem"
    },
    "models": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Models"
    }
  },
  "type": "object",
  "required": [
    "provider"
  ],
  "title": "ProviderTestResult"
}
```

### `ProviderWrite`
```json
{
  "properties": {
    "name": {
      "type": "string",
      "maxLength": 100,
      "minLength": 1,
      "title": "Name"
    },
    "provider_type": {
      "type": "string",
      "enum": [
        "openai",
        "deepseek",
        "lmstudio",
        "google",
        "custom"
      ],
      "title": "Provider Type"
    },
    "base_url": {
      "type": "string",
      "maxLength": 500,
      "minLength": 1,
      "title": "Base Url"
    },
    "model": {
      "type": "string",
      "maxLength": 200,
      "minLength": 1,
      "title": "Model"
    },
    "api_key": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 1000
        },
        {
          "type": "null"
        }
      ],
      "title": "Api Key"
    },
    "clear_api_key": {
      "type": "boolean",
      "title": "Clear Api Key",
      "default": false
    },
    "timeout_seconds": {
      "type": "number",
      "maximum": 300.0,
      "minimum": 1.0,
      "title": "Timeout Seconds",
      "default": 60
    }
  },
  "type": "object",
  "required": [
    "name",
    "provider_type",
    "base_url",
    "model"
  ],
  "title": "ProviderWrite"
}
```

### `PurgeLogsRequest`
```json
{
  "properties": {
    "before": {
      "type": "string",
      "format": "date-time",
      "title": "Before"
    }
  },
  "type": "object",
  "required": [
    "before"
  ],
  "title": "PurgeLogsRequest"
}
```

### `PurgeLogsResponse`
```json
{
  "properties": {
    "deleted": {
      "type": "integer",
      "title": "Deleted"
    }
  },
  "type": "object",
  "required": [
    "deleted"
  ],
  "title": "PurgeLogsResponse"
}
```

### `SwapSuggestion`
```json
{
  "properties": {
    "dish_id": {
      "type": "integer",
      "title": "Dish Id"
    },
    "name": {
      "type": "string",
      "title": "Name"
    },
    "reason": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Reason"
    },
    "plan": {
      "additionalProperties": true,
      "type": "object",
      "title": "Plan"
    }
  },
  "type": "object",
  "required": [
    "dish_id",
    "name",
    "plan"
  ],
  "title": "SwapSuggestion"
}
```

### `SwapSuggestionRequest`
```json
{
  "properties": {
    "day": {
      "type": "integer",
      "maximum": 7.0,
      "minimum": 1.0,
      "title": "Day"
    },
    "meal_type": {
      "type": "string",
      "enum": [
        "breakfast",
        "lunch",
        "dinner"
      ],
      "title": "Meal Type"
    },
    "target_dish_id": {
      "type": "integer",
      "exclusiveMinimum": 0.0,
      "title": "Target Dish Id"
    },
    "plan": {
      "additionalProperties": true,
      "type": "object",
      "title": "Plan"
    },
    "note": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 1000
        },
        {
          "type": "null"
        }
      ],
      "title": "Note"
    }
  },
  "type": "object",
  "required": [
    "day",
    "meal_type",
    "target_dish_id",
    "plan"
  ],
  "title": "SwapSuggestionRequest"
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

Chat/retry content type là gì?

A. `text/event-stream`  
B. `image/png`  
C. `application/pdf`

### Câu 2 (trắc nghiệm)

Provider secret có xuất hiện trong `ProviderItem` không?

A. Không được lộ raw secret  
B. Luôn trả nguyên văn  
C. Chỉ khi test provider

### Câu 3 (trắc nghiệm)

Lịch sử chat và request log có cùng endpoint không?

A. Không, user conversation và admin log tách domain  
B. Có  
C. Chỉ trên mobile

### Câu 4 (tình huống)

Hãy xác định endpoint/schema để retry turn gần nhất và cách frontend phải đọc response.

### Câu 5 (tình huống)

Provider active nhưng request explain-plan lỗi. Hãy nêu contract/error và dữ liệu không được lộ.

## Đáp án, giải thích và bằng chứng mong đợi

1. **A.** Consumer phải parse event stream, không JSON một lần.
2. **A.** Secret được mã hóa server-side và API chỉ trả masked metadata; nội dung request/response hiện không có cơ chế redaction tổng quát.
3. **A.** Product history khác operational audit.
4. `POST /api/ai/conversations/{conversation_id}/turns/{turn_id}/retry`; đọc SSE events qua `aiApi` centralized consumer.
5. Trả AI unavailable/validation/business detail theo status; log không được chứa provider secret/header nhưng hiện có thể chứa prompt, context và response. API không trả API key, encrypted secret hay raw provider internals.


Tự chấm mỗi câu đúng/hoàn thành là 1 điểm: **5/5 = hiểu tốt; 4/5 = đạt; 3/5 = xem lại; 0–2/5 = đọc lại tài liệu và thực hành lại.**
