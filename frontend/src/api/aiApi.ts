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
  created_at: string;
  updated_at: string;
}
export interface ConversationChatResponse extends ChatResponse {
  conversation_id: number;
  turn: ConversationTurn;
}
export type ChatStreamEvent =
  | { event: "start"; data: { conversation_id: number; turn: ConversationTurn } }
  | { event: "delta"; data: { content: string } }
  | { event: "done"; data: ConversationChatResponse }
  | { event: "error"; data: { detail: string; conversation_id: number; turn_id: number; retryable: true } };
export interface ConversationSummary {
  id: number;
  title: string;
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
  needs_clarification: boolean;
  clarification_question: string | null;
}
export interface ExplainPlanPayload {
  plan_data: unknown;
  total_cost?: number | null;
  total_calories?: number | null;
  budget_limit?: number | null;
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
    onEvent: (event: ChatStreamEvent) => void,
    signal?: AbortSignal,
    context?: unknown,
  ) => consumeChatStream(
    "/api/ai/chat",
    { message, conversation_id: conversationId, context },
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
    api.post<ChatResponse>("/api/ai/explain-plan", payload),

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
      throw new ApiError(503, event.data.detail);
    }
    onEvent(event);
    if (event.event === "done") completed = event.data;
  }, signal);
  if (!completed) {
    throw new ApiError(0, "Luồng trả lời kết thúc trước khi hoàn tất.");
  }
  return completed;
}
