import { api } from "../lib/apiClient";
import type {
  GeneratedMealPlan, GenerateParams, InfeasibleResult, MealPlan,
} from "../types";

type GenerateResult = GeneratedMealPlan | InfeasibleResult;

// Phan biet ket qua bat kha thi voi thuc don da sinh.
export const isInfeasible = (r: GenerateResult): r is InfeasibleResult =>
  (r as InfeasibleResult).status === "infeasible";

// Client chỉ gửi dish selection; backend suy ra role từ dish_type, kiểm tra
// cấu trúc bữa và lưu lại snapshot totals/ingredients.
export interface SaveSlotInput {
  slot: string;
  dish_ids: number[];
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
      previous_plan_signature: params.previous_plan_signature ?? null,
    }),

  save: (input: SavePlanInput) => api.post<MealPlan>("/api/meal-plans", input),

  // Danh sach thuc don cua nguoi dung hien tai (JWT).
  list: () => api.get<MealPlan[]>("/api/meal-plans"),

  get: (id: number) => api.get<MealPlan>(`/api/meal-plans/${id}`),

  shoppingList: (id: number) => api.get<ShoppingListResponse>(`/api/meal-plans/${id}/shopping-list`),

  updateShoppingItem: (planId: number, itemId: number, is_purchased: boolean) =>
    api.patch<ShoppingListResponse>(`/api/meal-plans/${planId}/shopping-list/items/${itemId}`, { is_purchased }),
  shareShoppingList: (planId: number) =>
    api.post<ShoppingShareResponse>(`/api/meal-plans/${planId}/shopping-list/share`),
  revokeShoppingShare: (planId: number) => api.del<void>(`/api/meal-plans/${planId}/shopping-list/share`),

  remove: (id: number) => api.del<void>(`/api/meal-plans/${id}`),
};

export interface ShoppingListItem {
  id?: number | null;
  ingredient_id: number;
  name: string;
  quantity: number;
  unit: string;
  estimated_cost: number;
  is_purchased: boolean;
}

export interface ShoppingListResponse {
    plan_id: number;
  plan_name?: string | null;
  schema_version: number;
  items: ShoppingListItem[];
  total_estimated_cost: number;
  warnings: Array<{ code: string; message: string }>;
}

export interface ShoppingShareResponse {
  token: string;
  expires_at: string;
}

export const publicShoppingListApi = {
  get: (token: string) => api.publicGet<PublicShoppingListResponse>(`/api/public/shopping-lists/${token}`),
  updateItem: (token: string, itemId: number, is_purchased: boolean) =>
    api.publicPatch<PublicShoppingListResponse>(`/api/public/shopping-lists/${token}/items/${itemId}`, { is_purchased }),
};

export interface PublicShoppingListResponse extends ShoppingListResponse { expires_at: string; }
