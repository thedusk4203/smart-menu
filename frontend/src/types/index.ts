// Kieu du lieu dung chung — mirror schema/enum cua backend.

// ── Enums (khop gia tri backend) ────────────────────────────────────────
export type Gender = "male" | "female";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "active";
export type FitnessGoal = "maintain" | "lose_weight" | "gain_muscle" | "gain_weight";
export type UserRole = "user" | "data_editor" | "admin" | "super_admin";
export type FoodGroup =
  | "protein" | "vegetable" | "grain" | "dairy" | "fat" | "fruit" | "other";
export type MealType = "breakfast" | "lunch" | "dinner";
export type CookingMethod = "stir_fry" | "boil" | "soup" | "braise" | "steam";
export type DishType =
  | "staple" | "savory" | "soup" | "vegetable_side" | "side" | "breakfast";
export type ExclusionReason = "allergy" | "dislike";

// ── Auth / User ─────────────────────────────────────────────────────────
export interface User {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
}
export interface TokenResponse {
  access_token: string;
  token_type: string;
}
export interface RegisterInput {
  email: string;
  password: string;
  full_name?: string;
  role?: UserRole;
}
export interface UserUpdateInput {
  email?: string;
  password?: string;
  role?: UserRole;
  is_active?: boolean;
}

// ── Profile ─────────────────────────────────────────────────────────────
export interface Profile {
  user_id: number;
  full_name: string | null;
  gender: Gender | null;
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  activity_level: ActivityLevel;
  goal: FitnessGoal;
  meals_per_day: number;
  daily_calorie_target: number | null;
  daily_budget: number | null;
}
export type ProfileUpdate = Partial<Omit<Profile, "user_id">>;

export interface Exclusion {
  id: number;
  ingredient_id: number;
  reason: ExclusionReason;
}

// ── Nutrition ───────────────────────────────────────────────────────────
export interface NutritionInput {
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

// ── Ingredients ─────────────────────────────────────────────────────────
export interface Ingredient {
  id: number;
  name: string;
  food_group: FoodGroup;
  default_unit: string;
  grams_per_unit: number;
  is_active: boolean;
  calories?: number | null;
  protein_g?: number | null;
  carbs_g?: number | null;
  fat_g?: number | null;
  fiber_g?: number | null;
  latest_price?: number | null;
  price_unit?: string | null;
  latest_price_per_unit?: number | null;
}
export interface IngredientNutritionInput {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
}
export interface IngredientCreate {
  name: string;
  food_group: FoodGroup;
  default_unit: string;
  grams_per_unit: number;
  nutrition: IngredientNutritionInput;
}
export interface IngredientUpdate {
  name?: string;
  food_group?: FoodGroup;
  default_unit?: string;
  grams_per_unit?: number;
  is_active?: boolean;
}

// ── Meals ───────────────────────────────────────────────────────────────
export interface MealSummary {
  id: number;
  name: string;
  meal_type: MealType;
  cooking_method?: CookingMethod | null;
  servings: number;
  tags: string[];
  components: string[];
  is_active: boolean;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  estimated_cost: number;
}
export interface MealIngredient {
  ingredient_id: number;
  name?: string | null;
  quantity: number;
  unit: string;
}
export interface MealDetail extends MealSummary {
  description?: string | null;
  instructions?: string | null;
  ingredients: MealIngredient[];
}
export interface MealIngredientInput {
  ingredient_id: number;
  quantity: number;
  unit: string;
}
export interface MealCreate {
  name: string;
  meal_type: MealType;
  cooking_method?: CookingMethod | null;
  description?: string | null;
  instructions?: string | null;
  servings: number;
  tags: string[];
  components?: string[];
  ingredients: MealIngredientInput[];
}
export interface MealUpdate {
  name?: string;
  meal_type?: MealType;
  cooking_method?: CookingMethod | null;
  description?: string | null;
  instructions?: string | null;
  servings?: number;
  tags?: string[];
  components?: string[];
  is_active?: boolean;
}

// ── Planner-ready dish catalog ──────────────────────────────────────────
export interface DishSummary {
  id: number;
  name: string;
  dish_type: DishType;
  cooking_method?: CookingMethod | null;
  tags: string[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  estimated_cost: number;
}
export interface DishIngredient {
  ingredient_id: number;
  name: string;
  quantity: number;
  unit: string;
  estimated_cost: number;
}
export interface DishDetail extends DishSummary {
  description?: string | null;
  instructions?: string | null;
  ingredients: DishIngredient[];
}

// ── Meal plans ──────────────────────────────────────────────────────────
export interface PlanIngredientSnapshot {
  ingredient_id: number;
  name: string;
  quantity: number;
  unit: string;
  estimated_cost: number;
  purchase_mode?: "regular" | "pantry" | "ignored";
  purchase_increment?: number | null;
  base_quantity?: number;
  extra_quantity?: number;
  actual_quantity?: number;
  adjustment_reason?: "leftover_absorption" | null;
  nutrition_delta?: { calories: number; protein_g: number; fat_g: number; carb_g: number };
}
export interface PlanDish {
  dish_id: number;
  name: string;
  dish_type: DishType;
  cooking_method?: CookingMethod | null;
  calories?: number;
  protein_g?: number;
  fat_g?: number;
  carb_g?: number;
  cost?: number;
  tags?: string[];
  ingredients?: PlanIngredientSnapshot[];
}
export interface PlannedMeal {
  name: string;
  meal_type: MealType;
  components?: string[];
  dishes?: PlanDish[];
  calories: number;
  protein_g: number;
  fat_g: number;
  carb_g: number;
  cost: number;
}
export interface PlannedDay {
  day: number;
  date: string | null;
  meals: PlannedMeal[];
  day_calories: number;
  day_cost: number;
}
export interface PlanCostSummary {
  purchase_cost: number;
  consumption_value: number;
  expired_waste_value: number;
  ending_carryover_value: number;
}
export interface PlanPurchaseItem {
  item_key: string;
  ingredient_id: number;
  name: string;
  unit: string;
  purchase_day: number;
  purchase_increment: number;
  block_count: number;
  purchase_quantity: number;
  required_quantity: number;
  purchase_cost: number;
  remaining_quantity: number;
  expired_waste_quantity: number;
  carryover_quantity: number;
  storage_splits: Array<{ mode: string; quantity: number; expiry_day: number }>;
}
export interface PlanData {
  schema_version: 3;
  algorithm_version?: string;
  plan_signature?: string;
  source_fingerprint?: string;
  days: PlannedDay[];
  nutrition_target?: { calories: number; protein_g: number; fat_g: number; carb_g: number };
  cost_summary?: PlanCostSummary;
  procurement?: {
    purchase_items: PlanPurchaseItem[];
    pantry_checks: Array<{ item_key: string; ingredient_id: number; name: string; quantity: number; unit: string }>;
    shopping_days: number[];
  };
  adjustments?: Array<{
    day: number;
    slot: MealType;
    dish_id: number;
    ingredient_id: number;
    base_quantity: number;
    extra_quantity: number;
    actual_quantity: number;
    unit: string;
    nutrition_delta: { calories: number; protein_g: number; fat_g: number; carb_g: number };
  }>;
  base_nutrition?: Array<{ calories: number; protein_g: number; fat_g: number; carb_g: number }>;
  final_nutrition?: Array<{ calories: number; protein_g: number; fat_g: number; carb_g: number }>;
  metrics?: {
    average_calorie_deviation_pct: number;
    maximum_calorie_deviation_pct: number;
    protein_shortage_pct: number;
    repeat_counts: Record<string, number>;
    solver_time_ms: number;
    nutrition_score: number;
  };
  warnings: Array<string | { code: string; message: string; details?: Record<string, number | string> }>;
  meals_per_day: number;
}
export interface GeneratedMealPlan {
  user_id: number;
  name: string;
  start_date: string | null;
  end_date: string | null;
  budget_limit: number | null;
  total_cost: number;
  total_calories: number;
  plan_data: PlanData;
}
export interface InfeasibleResult {
  status: "infeasible";
  reasons: Array<{ code: string; message: string; details?: Record<string, number | string> }>;
  warnings?: Array<{ code: string; message: string; details?: Record<string, number | string> }>;
}
export interface MealPlan {
  id: number;
  user_id: number;
  name: string;
  start_date: string;
  end_date: string | null;
  budget_limit: number | null;
  total_cost: number;
  total_calories: number;
  plan_data: PlanData;
  created_at?: string | null;
}
export interface GenerateParams {
  days?: number;
  meals_per_day?: number;
  budget_limit?: number | null;
  preferred_tags?: string[];
  seed?: number;
  previous_plan_signature?: string;
  start_date?: string;
}

export interface ListParams {
  search?: string;
  active_only?: boolean;
  limit?: number;
  offset?: number;
}
