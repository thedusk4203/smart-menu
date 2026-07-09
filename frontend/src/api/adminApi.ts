// File: frontend/src/api/adminApi.ts
import { apiRequest } from "./httpClient";

export interface AdminStats {
  total_users: number;
  total_ingredients: number;
  total_meals: number;
  ingredients_missing_nutrition: number;
  ingredients_missing_price: number;
  meals_missing_ingredients: number;
}

export async function getAdminStats(): Promise<AdminStats> {
  return apiRequest<AdminStats>("/api/admin/stats");
}