import { api } from "../lib/apiClient";
import type {
  GeneratedMealPlan, GenerateParams, InfeasibleResult, MealPlan,
} from "../types";

type GenerateResult = GeneratedMealPlan | InfeasibleResult;

// Phan biet ket qua bat kha thi voi thuc don da sinh.
export const isInfeasible = (r: GenerateResult): r is InfeasibleResult =>
  (r as InfeasibleResult).status === "infeasible";

// Gate 0: khi luu chi gui id mam com theo ngay/slot; backend recompute totals
// va gan user tu JWT. Khong gui user_id/total_cost/total_calories/plan_data.
export interface SaveSlotInput {
  slot: string;
  meal_set_id: number;
}
export interface SaveDayInput {
  day: number;
  meals: SaveSlotInput[];
}
export interface SavePlanInput {
  name: string;
  start_date: string;
  budget_limit?: number | null;
  days: SaveDayInput[];
}

export const mealPlanApi = {
  // Sinh thuc don (khong tu luu). User lay tu JWT.
  generate: (params: GenerateParams = {}) =>
    api.post<GenerateResult>("/api/meal-plans/generate", {
      days: params.days ?? null,
      meals_per_day: params.meals_per_day ?? null,
      budget_limit: params.budget_limit ?? null,
      preferred_tags: params.preferred_tags ?? null,
      seed: params.seed ?? null,
    }),

  save: (input: SavePlanInput) => api.post<MealPlan>("/api/meal-plans", input),

  // Danh sach thuc don cua nguoi dung hien tai (JWT).
  list: () => api.get<MealPlan[]>("/api/meal-plans"),

  get: (id: number) => api.get<MealPlan>(`/api/meal-plans/${id}`),

  remove: (id: number) => api.del<void>(`/api/meal-plans/${id}`),
};
