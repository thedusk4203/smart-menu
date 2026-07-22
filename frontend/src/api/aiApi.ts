import { api, ApiError, streamSse } from "../lib/apiClient";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
export interface ChatResponse {
  reply: string;
}
export type ConversationTurnStatus = "pending" | "completed" | "failed";
export interface ConversationTurn {
  id: number;
  turn_number: number;
  user_content: string;
  assistant_content: string | null;
  status: ConversationTurnStatus;
  personalization_used: boolean;
  grounding_mode: "none" | "native_web_search" | "model_fallback";
  citations: { title: string; url: string }[];
  created_at: string;
  updated_at: string;
}
export interface ConversationChatResponse extends ChatResponse {
  conversation_id: number;
  turn: ConversationTurn;
  personalization_used: boolean;
  grounding_mode: "none" | "native_web_search" | "model_fallback";
  citations: { title: string; url: string }[];
}
export type ChatMode = "general" | "meal_advice" | "health_reference";
export type ChatStreamEvent =
  | { event: "start"; data: { conversation_id: number; turn: ConversationTurn } }
  | { event: "delta"; data: { content: string } }
  | { event: "done"; data: ConversationChatResponse }
  | {
      event: "error";
      data: {
        detail: string;
        error?: { code: string; message: string; details?: Record<string, unknown> };
        conversation_id: number;
        turn_id: number;
        retryable: true;
      };
    };
export interface ConversationSummary {
  id: number;
  title: string;
  mode: ChatMode;
  turn_count: number;
  last_message_preview: string | null;
  created_at: string;
  updated_at: string;
}
export interface ConversationDetail extends ConversationSummary {
  turns: ConversationTurn[];
}
export interface AIStatus {
  enabled: boolean;
  source: string | null;
  provider_name: string | null;
  provider_type: string | null;
  model: string | null;
  features: string[];
}
export interface ParsedMenuRequest {
  days: number | null;
  meals_per_day: number | null;
  budget_limit: number | null;
  preferred_tags: string[];
  unresolved_tags: string[];
  needs_clarification: boolean;
  clarification_question: string | null;
}
export interface ExplainPlanPayload {
  plan_data: unknown;
  total_cost?: number | null;
  total_calories?: number | null;
  budget_limit?: number | null;
}
export interface PlanExplanation extends ChatResponse {
  summary: string;
  budget_assessment: string;
  nutrition_assessment: string;
  highlights: string[];
  cautions: string[];
  recommendations: string[];
}
export interface SwapSuggestion {
  dish_id: number;
  name: string;
  reason?: string;
  plan: import("../types").GeneratedMealPlan;
}

export const aiApi = {
  status: () => api.get<AIStatus>("/api/ai/status"),

  chatStream: (
    message: string,
    conversationId: number | undefined,
    mode: ChatMode,
    onEvent: (event: ChatStreamEvent) => void,
    signal?: AbortSignal,
  ) => consumeChatStream(
    "/api/ai/chat",
    { message, conversation_id: conversationId, mode },
    onEvent,
    signal,
  ),

  listConversations: () =>
    api.get<ConversationSummary[]>("/api/ai/conversations"),

  getConversation: (conversationId: number) =>
    api.get<ConversationDetail>(`/api/ai/conversations/${conversationId}`),

  deleteConversation: (conversationId: number) =>
    api.del<void>(`/api/ai/conversations/${conversationId}`),

  retryTurnStream: (
    conversationId: number,
    turnId: number,
    onEvent: (event: ChatStreamEvent) => void,
    signal?: AbortSignal,
  ) => consumeChatStream(
    `/api/ai/conversations/${conversationId}/turns/${turnId}/retry`,
    {},
    onEvent,
    signal,
  ),

  parseMenuRequest: (message: string) =>
    api.post<ParsedMenuRequest>("/api/ai/parse-menu-request", { message }),

  explainPlan: (payload: ExplainPlanPayload) =>
    api.post<PlanExplanation>("/api/ai/explain-plan", payload),

  // Goi y doi mon se chi bat khi backend co candidate hop le va validate lai.
  suggestSwap: (payload: { day: number; meal_type: string; target_dish_id: number;
    plan: import("../types").GeneratedMealPlan; note?: string }) =>
    api.post<SwapSuggestion[]>("/api/ai/suggest-swap", payload),
};

async function consumeChatStream(
  path: string,
  body: unknown,
  onEvent: (event: ChatStreamEvent) => void,
  signal?: AbortSignal,
): Promise<ConversationChatResponse> {
  let completed: ConversationChatResponse | null = null;
  await streamSse(path, body, (raw) => {
    const event = raw as ChatStreamEvent;
    if (event.event === "error") {
      throw new ApiError(503, event.data.error?.message ?? "Menuto chưa thể hoàn tất câu trả lời. Hãy thử lại.", {
        code: event.data.error?.code ?? "AI_STREAM_FAILED",
        technicalMessage: event.data.detail,
        details: event.data.error?.details,
        retryable: event.data.retryable,
      });
    }
    onEvent(event);
    if (event.event === "done") completed = event.data;
  }, signal);
  if (!completed) {
    throw new ApiError(0, "Câu trả lời bị gián đoạn. Hãy thử lại.", {
      code: "AI_STREAM_INTERRUPTED",
      technicalMessage: "Luồng trả lời kết thúc trước khi hoàn tất.",
      retryable: true,
    });
  }
  return completed;
}
