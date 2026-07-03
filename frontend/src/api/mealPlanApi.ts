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
  // Nới lỏng: backend lưu dict bất kỳ. Thực đơn vừa sinh có dạng giàu dữ liệu
  // ({ days, warnings, meals_per_day }) nên không ép về date→slot→ids.
  plan_data?: Record<string, unknown>;
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

// ── Sinh thực đơn tự động (POST /api/meal-plans/generate) ──────────────────
// Backend trả về thực đơn ĐÃ tính sẵn tên món/calo/chi phí trong plan_data.days,
// nên frontend không cần gọi thêm API món ăn để hiển thị.

// Một món đã xếp vào 1 bữa (khớp PlannedMeal ở backend).
export interface PlannedMeal {
  meal_id: number;
  name: string;
  meal_type: string; // breakfast | lunch | dinner
  calories: number;
  protein_g: number;
  fat_g: number;
  carb_g: number;
  cost: number;
}

// Một ngày trong thực đơn (khớp PlannedDay ở backend).
export interface PlannedDay {
  day: number; // 1-based
  date: string | null;
  meals: PlannedMeal[];
  day_calories: number;
  day_cost: number;
}

// Thực đơn vừa sinh (chưa lưu). plan_data giàu dữ liệu để render trực tiếp.
export interface GeneratedMealPlan {
  user_id: number;
  name: string;
  start_date: string | null;
  end_date: string | null;
  budget_limit: number | null;
  total_cost: number;
  total_calories: number;
  plan_data: {
    days: PlannedDay[];
    warnings: string[];
    meals_per_day: number;
  };
}

// Khi không thể lập thực đơn (hết ngân sách, thiếu món hợp lệ...).
export interface InfeasibleResult {
  status: "infeasible";
  reasons: string[];
}

// Tham số gửi lên endpoint generate. Giữ lại để MenuResult "tạo lại" với cùng
// ràng buộc nhưng seed khác.
export interface GenerateParams {
  days?: number;
  meals_per_day?: number;
  budget_limit?: number;
  preferred_tags?: string[];
  seed?: number; // đổi seed -> ra phương án khác (FR-PLAN-05)
}

// Type guard: phân biệt kết quả bất khả thi với thực đơn hợp lệ.
export function isInfeasible(
  r: GeneratedMealPlan | InfeasibleResult
): r is InfeasibleResult {
  return (r as InfeasibleResult).status === "infeasible";
}

// Gọi endpoint sinh thực đơn. KHÔNG tự lưu — người dùng bấm "Lưu" nếu ưng.
export async function generateMealPlan(
  params: GenerateParams = {}
): Promise<GeneratedMealPlan | InfeasibleResult> {
  const me = await getMe();
  return apiRequest<GeneratedMealPlan | InfeasibleResult>(
    "/api/meal-plans/generate",
    { method: "POST", body: { ...params, user_id: me.id } }
  );
}