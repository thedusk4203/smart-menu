import { api } from "../lib/apiClient";
import type {
  GeneratedMealPlan, GenerateParams, InfeasibleResult, MealPlan,
} from "../types";

type GenerateResult = GeneratedMealPlan | InfeasibleResult;

export type ShoppingScope = "all" | "purchase_day" | "usage_day";
const shoppingQuery = (day?: number, scope?: ShoppingScope): string => {
  const query = new URLSearchParams();
  if (day) query.set("day", String(day));
  if (scope) query.set("scope", scope);
  const encoded = query.toString();
  return encoded ? `?${encoded}` : "";
};

// Phan biet ket qua bat kha thi voi thuc don da sinh.
export const isInfeasible = (r: GenerateResult): r is InfeasibleResult =>
  (r as InfeasibleResult).status === "infeasible";

// Client chỉ gửi dish selection; backend suy ra role từ dish_type, kiểm tra
// cấu trúc bữa và lưu lại snapshot totals/ingredients.
export interface SaveSlotInput {
  slot: string;
  dish_ids: number[];
  adjustments?: Array<{ dish_id: number; ingredient_id: number; extra_quantity: number }>;
}
export interface SaveDayInput {
  day: number;
  meals: SaveSlotInput[];
}
export interface SavePlanInput {
  name: string;
  start_date: string;
  budget_limit?: number | null;
  source_fingerprint?: string;
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
      start_date: params.start_date ?? null,
    }),

  save: (input: SavePlanInput) => api.post<MealPlan>("/api/meal-plans", input),

  // Danh sach thuc don cua nguoi dung hien tai (JWT).
  list: () => api.get<MealPlan[]>("/api/meal-plans"),

  get: (id: number) => api.get<MealPlan>(`/api/meal-plans/${id}`),

  shoppingList: (id: number, day?: number, scope?: ShoppingScope) =>
    api.get<ShoppingListResponse>(`/api/meal-plans/${id}/shopping-list${shoppingQuery(day, scope)}`),

  updateShoppingItem: (planId: number, itemId: number, is_purchased: boolean, day?: number, scope?: ShoppingScope) =>
    api.patch<ShoppingListResponse>(`/api/meal-plans/${planId}/shopping-list/items/${itemId}${shoppingQuery(day, scope)}`, { is_purchased }),
  updateShoppingItems: (planId: number, itemIds: number[], is_purchased: boolean, day?: number, scope?: ShoppingScope) =>
    api.patch<ShoppingListResponse>(`/api/meal-plans/${planId}/shopping-list/items${shoppingQuery(day, scope)}`, { item_ids: itemIds, is_purchased }),
  shareShoppingList: (planId: number, day?: number, scope?: ShoppingScope) =>
    api.post<ShoppingShareResponse>(`/api/meal-plans/${planId}/shopping-list/share${shoppingQuery(day, scope)}`),
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
  item_key?: string | null;
  item_kind?: "purchase" | "pantry";
  scheduled_day?: number | null;
}

export interface ShoppingPurchaseItem extends ShoppingListItem {
  required_quantity: number;
  purchase_quantity: number;
  purchase_cost: number;
  purchase_increment: number;
  block_count: number;
  remaining_quantity: number;
  expired_waste_quantity: number;
  carryover_quantity: number;
  storage_splits: Array<{ mode: string; quantity: number; expiry_day: number }>;
}

export interface CarryoverUsage {
  ingredient_id: number;
  name: string;
  quantity: number;
  unit: string;
  purchase_day: number;
  use_day: number;
  storage_mode: string;
  expiry_day: number;
  dish_name?: string | null;
}

export interface DailyLedgerItem {
  item_key: string;
  source_kind: "inventory" | "purchase";
  inventory_lot_id?: number | null;
  ingredient_id: number;
  name: string;
  unit: string;
  opening_quantity: number;
  purchase_quantity: number;
  usage_quantity: number;
  expired_quantity: number;
  closing_quantity: number;
  unit_value: number;
  purchase_cost: number;
  allocations: Array<{
    dish_name?: string | null;
    quantity: number;
    storage_mode?: string;
    expiry_day?: number;
  }>;
}

export interface DailyLedgerDay {
  day: number;
  items: DailyLedgerItem[];
  totals: Record<string, number>;
}

export interface ShoppingListResponse {
  plan_id: number;
  plan_name?: string | null;
  day?: number | null;
  date?: string | null;
  schema_version: 3;
  shopping_schema_version: 3;
  scope: ShoppingScope;
  items: ShoppingListItem[];
  total_estimated_cost: number;
  purchase_items: ShoppingPurchaseItem[];
  pantry_checks: ShoppingListItem[];
  carryover_usage: CarryoverUsage[];
  leftovers: Array<{
    ingredient_id: number; name: string; quantity: number; unit: string;
    purchase_day: number; status: "carryover" | "closing_stock" | "expired_waste";
  }>;
  daily_ledger: DailyLedgerDay[];
  summary: Record<string, number>;
  warnings: Array<{ code: string; message: string }>;
}

export interface ShoppingShareResponse {
  token: string;
  expires_at: string;
  day?: number | null;
  scope: ShoppingScope;
}

export const publicShoppingListApi = {
  get: (token: string) => api.publicGet<PublicShoppingListResponse>(`/api/public/shopping-lists/${token}`),
  updateItem: (token: string, itemId: number, is_purchased: boolean) =>
    api.publicPatch<PublicShoppingListResponse>(`/api/public/shopping-lists/${token}/items/${itemId}`, { is_purchased }),
  updateItems: (token: string, itemIds: number[], is_purchased: boolean) =>
    api.publicPatch<PublicShoppingListResponse>(`/api/public/shopping-lists/${token}/items`, { item_ids: itemIds, is_purchased }),
};

export interface PublicShoppingListResponse extends ShoppingListResponse { expires_at: string; }
