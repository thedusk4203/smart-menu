import { api } from "../lib/apiClient";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
export interface ChatResponse {
  reply: string;
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
  meal_id: number;
  name: string;
  reason?: string;
}

export const aiApi = {
  chat: (message: string, context?: unknown) =>
    api.post<ChatResponse>("/api/ai/chat", { message, context }),

  parseMenuRequest: (message: string) =>
    api.post<ParsedMenuRequest>("/api/ai/parse-menu-request", { message }),

  explainPlan: (payload: ExplainPlanPayload) =>
    api.post<ChatResponse>("/api/ai/explain-plan", payload),

  // Goi y doi mon se chi bat khi backend co candidate hop le va validate lai.
  suggestSwap: (payload: { meal_id: number; meal_type: string; note?: string }) =>
    api.post<SwapSuggestion[]>("/api/ai/suggest-swap", payload),
};
