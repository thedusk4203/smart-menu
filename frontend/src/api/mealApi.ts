// File: frontend/src/api/mealApi.ts
import { apiRequest } from "./httpClient";

export interface MealSummary {
  id: number;
  name: string;
  meal_type: "breakfast" | "lunch" | "dinner";
  cooking_method: string | null;
  servings: number;
  tags: string[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  estimated_cost: number;
}

export interface MealIngredient {
  ingredient_id: number;
  name: string | null;
  quantity: number;
  unit: string;
}

export interface MealDetail extends MealSummary {
  description: string | null;
  instructions: string | null;
  ingredients: MealIngredient[];
}

// Lấy danh sách món ăn
export async function getMeals(params?: {
  meal_type?: string;
  search?: string;
}): Promise<MealSummary[]> {
  const query = new URLSearchParams();
  if (params?.meal_type) query.set("meal_type", params.meal_type);
  if (params?.search) query.set("search", params.search);
  const qs = query.toString();
  return apiRequest<MealSummary[]>(`/api/meals${qs ? `?${qs}` : ""}`);
}

// Lấy chi tiết một món ăn (kèm nguyên liệu)
export async function getMealDetail(mealId: number): Promise<MealDetail> {
  return apiRequest<MealDetail>(`/api/meals/${mealId}`);
}