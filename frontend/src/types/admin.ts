import type {
  CookingMethod, DishRole, DishType, FoodGroup, MealType, UserRole,
} from "./index";

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminDashboardSummary {
  users_total: number;
  users_active: number;
  users_locked: number;
  ingredients_total: number;
  ingredients_active: number;
  dishes_total: number;
  meal_sets_total: number;
  missing_price: number;
  missing_nutrition: number;
  missing_conversion: number;
  incomplete_dishes: number;
  duplicate_names: number;
  open_quality_issues: number;
  last_import_at: string | null;
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface NutritionPayload {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
}

export interface PricePayload {
  price: number;
  unit: string;
  price_per_default_unit: number;
  source?: string | null;
  recorded_at?: string | null;
}

export interface AdminIngredient {
  id: number;
  name: string;
  food_group: FoodGroup;
  default_unit: string;
  grams_per_unit: number;
  is_active: boolean;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  fiber_g: number | null;
  latest_price: number | null;
  price_unit: string | null;
  latest_price_per_unit: number | null;
  price_source: string | null;
  price_recorded_at: string | null;
  created_at: string;
  updated_at: string;
  missing_price: boolean;
  missing_nutrition: boolean;
  missing_conversion: boolean;
}

export interface AdminIngredientWrite {
  name: string;
  food_group: FoodGroup;
  default_unit: string;
  grams_per_unit: number;
  is_active: boolean;
  nutrition: NutritionPayload | null;
  price: PricePayload | null;
}

export interface AdminDishIngredient {
  ingredient_id: number;
  name: string;
  quantity: number;
  unit: string;
  missing_price: boolean;
  missing_nutrition: boolean;
}

export interface AdminDish {
  id: number;
  name: string;
  dish_type: DishType;
  cooking_method: CookingMethod | null;
  description: string | null;
  instructions: string | null;
  tags: string[];
  is_active: boolean;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  estimated_cost: number;
  ingredient_count: number;
  missing_recipe: boolean;
  missing_price: boolean;
  missing_nutrition: boolean;
  created_at: string;
  updated_at: string;
  ingredients: AdminDishIngredient[];
}

export interface AdminDishWrite {
  name: string;
  dish_type: DishType;
  cooking_method: CookingMethod | null;
  description: string | null;
  instructions: string | null;
  tags: string[];
  is_active: boolean;
  ingredients: Array<{ ingredient_id: number; quantity: number; unit: string }>;
}

export interface AdminMealSet {
  id: number;
  name: string;
  meal_type: MealType;
  description: string | null;
  tags: string[];
  is_active: boolean;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  estimated_cost: number;
  dish_count: number;
  all_dishes_active: boolean;
  missing_recipe: boolean;
  created_at: string;
  updated_at: string;
  dishes: Array<{ dish_id: number; role: DishRole; name: string; sort_order: number }>;
}

export interface AdminMealSetWrite {
  name: string;
  meal_type: MealType;
  description: string | null;
  tags: string[];
  is_active: boolean;
  dishes: Array<{ dish_id: number; role: DishRole; sort_order: number }>;
}

export interface QualityIssue {
  entity_type: "ingredient" | "dish" | "meal_set";
  entity_id: number;
  entity_name: string;
  code: string;
  severity: "error" | "warning";
  title: string;
  detail: string;
  updated_at: string;
}

export interface ImportPreview {
  job_id: number;
  entity_type: "ingredients" | "dishes";
  filename: string;
  total_rows: number;
  valid_rows: number;
  errors: Array<{ row: number; field?: string; message: string }>;
  warnings: Array<{ row: number; field?: string; message: string }>;
  conflicts: ImportConflict[];
  preview: Record<string, unknown>[];
  can_commit: boolean;
}

export interface ImportConflict {
  row: number;
  match_by: "id" | "code" | "name";
  incoming: { id: number | null; code: string | null; name: string };
  existing: { id: number; code: string | null; name: string };
}

export interface ImportJob {
  id: number;
  entity_type: string;
  filename: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  error_count: number;
  created_by: number;
  created_at: string;
  completed_at: string | null;
}
