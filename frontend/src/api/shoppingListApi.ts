// Shopping list: backend con stub. Truoc mat gom nguyen lieu PHIA CLIENT tu
// chi tiet mon an (/api/meals/{id} co that). Phan luu server de stub, noi sau.
import { api } from "../lib/apiClient";
import type { MealDetail } from "../types";

export interface ShoppingItem {
  ingredient_id: number;
  name: string;
  unit: string;
  quantity: number;
  checked?: boolean;
}

// Gom nguyen lieu theo (ingredient_id + unit), cong don so luong.
export function aggregateIngredients(meals: MealDetail[]): ShoppingItem[] {
  const map = new Map<string, ShoppingItem>();
  for (const meal of meals) {
    for (const ing of meal.ingredients ?? []) {
      const key = `${ing.ingredient_id}__${ing.unit}`;
      const existing = map.get(key);
      if (existing) {
        existing.quantity += ing.quantity;
      } else {
        map.set(key, {
          ingredient_id: ing.ingredient_id,
          name: ing.name ?? `Nguyên liệu #${ing.ingredient_id}`,
          unit: ing.unit,
          quantity: ing.quantity,
        });
      }
    }
  }
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name, "vi"));
}

// SCAFFOLD server-side (du kien) — chua bat, goi se 404.
export const shoppingListApi = {
  listByUser: (userId: number) =>
    api.get<unknown[]>(`/api/shopping-lists?user_id=${userId}`),
  createFromPlan: (planId: number) =>
    api.post<unknown>("/api/shopping-lists", { plan_id: planId }),
};
