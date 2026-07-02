// File: frontend/src/api/ingredientApi.ts
import { apiRequest } from "./httpClient";

export interface Ingredient {
  id: number;
  name: string;
  food_group: string;
  default_unit: string;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  latest_price: number | null;
  latest_price_per_unit: number | null;
}

// Lấy danh sách nguyên liệu (có thể lọc theo nhóm hoặc tìm theo tên)
export async function getIngredients(params?: {
  food_group?: string;
  search?: string;
  limit?: number;
}): Promise<Ingredient[]> {
  const query = new URLSearchParams();
  if (params?.food_group) query.set("food_group", params.food_group);
  if (params?.search) query.set("search", params.search);
  if (params?.limit) query.set("limit", String(params.limit));
  const qs = query.toString();
  return apiRequest<Ingredient[]>(`/api/ingredients${qs ? `?${qs}` : ""}`);
}