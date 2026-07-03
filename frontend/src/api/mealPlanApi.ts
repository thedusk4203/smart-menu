// File: frontend/src/api/mealPlanApi.ts
import { apiRequest } from "./httpClient";
import { getMe } from "./authApi";

export interface MealPlan {
  id: number;
  user_id: number;
  name: string;
  start_date: string;
  end_date: string | null;
  budget_limit: number | null;
  total_cost: number;
  total_calories: number;
  // {"2026-06-16": {"breakfast": [1], "lunch": [2], "dinner": [3]}}
  plan_data: Record<string, Record<string, number[]>>;
}

export interface MealPlanCreate {
  name?: string;
  start_date: string;
  end_date?: string;
  budget_limit?: number;
  total_cost?: number;
  total_calories?: number;
  plan_data?: Record<string, Record<string, number[]>>;
}

// Lấy danh sách thực đơn của tài khoản đang đăng nhập
export async function getMyMealPlans(): Promise<MealPlan[]> {
  const me = await getMe();
  return apiRequest<MealPlan[]>(`/api/meal-plans?user_id=${me.id}`);
}

// Lưu thực đơn mới
export async function saveMealPlan(data: MealPlanCreate): Promise<MealPlan> {
  const me = await getMe();
  return apiRequest<MealPlan>("/api/meal-plans", {
    method: "POST",
    body: { ...data, user_id: me.id },
  });
}

// Xoá thực đơn
export async function deleteMealPlan(planId: number): Promise<void> {
  return apiRequest(`/api/meal-plans/${planId}`, { method: "DELETE" });
}