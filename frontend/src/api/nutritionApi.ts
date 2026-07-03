// File: frontend/src/api/nutritionApi.ts
// Gọi endpoint tính nhu cầu dinh dưỡng (POST /api/nutrition/target).
// Thuần tính toán, không cần đăng nhập — dùng để trang Hồ sơ hiển thị BMR/TDEE,
// calo mục tiêu và macro ngay khi người dùng nhập chiều cao/cân nặng/mục tiêu.
import { apiRequest } from "./httpClient";

export type Gender = "male" | "female";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "active";
export type FitnessGoal = "maintain" | "lose_weight" | "gain_muscle" | "gain_weight";

// Đầu vào — khớp NutritionProfileInput ở backend.
export interface NutritionProfileInput {
  gender: Gender;
  age: number;
  weight_kg: number;
  height_cm: number;
  activity_level: ActivityLevel;
  fitness_goal: FitnessGoal;
}

export interface NutritionWarning {
  code: string;
  message: string;
}

// Kết quả — khớp NutritionTargetResponse ở backend.
export interface NutritionTarget {
  bmr: number;
  tdee: number;
  target_calories: number;
  daily_protein_g: number;
  daily_fat_g: number;
  daily_carb_g: number;
  bmi: number;
  is_feasible: boolean;
  warnings: NutritionWarning[];
}

// Tính nhu cầu dinh dưỡng/ngày từ thông tin hồ sơ.
export async function calculateNutritionTarget(
  input: NutritionProfileInput
): Promise<NutritionTarget> {
  return apiRequest<NutritionTarget>("/api/nutrition/target", {
    method: "POST",
    body: input,
  });
}
