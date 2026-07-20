import type { CookingMethod, DishType, FoodGroup, UserRole } from "./index";

export type IngredientPurchaseMode = "regular" | "pantry" | "ignored";

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
  planner_ready_dishes: number;
  breakfast_count: number;
  staple_count: number;
  savory_count: number;
  vegetable_count: number;
  soup_count: number;
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
  purchase_mode: IngredientPurchaseMode;
  purchase_increment: number | null;
  room_shelf_life_days: number | null;
  fridge_shelf_life_days: number | null;
  freezer_shelf_life_days: number | null;
  shelf_life_source: string | null;
  shelf_life_reviewed_at: string | null;
  purchase_block_cost: number | null;
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
  missing_purchase_rule: boolean;
  missing_storage_rule: boolean;
}

export interface AdminIngredientWrite {
  name: string;
  food_group: FoodGroup;
  default_unit: string;
  grams_per_unit: number;
  purchase_mode: IngredientPurchaseMode;
  purchase_increment: number | null;
  room_shelf_life_days: number | null;
  fridge_shelf_life_days: number | null;
  freezer_shelf_life_days: number | null;
  shelf_life_source: string | null;
  shelf_life_reviewed_at: string | null;
  is_active: boolean;
  nutrition: NutritionPayload | null;
  price: PricePayload | null;
}

export interface AdminDishIngredient {
  ingredient_id: number;
  name: string;
  quantity: number;
  unit: string;
  max_extra_quantity: number;
  extra_step_quantity: number | null;
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
  ingredients: Array<{
    ingredient_id: number;
    quantity: number;
    unit: string;
    max_extra_quantity: number;
    extra_step_quantity: number | null;
  }>;
}

export interface QualityIssue {
  entity_type: "ingredient" | "dish";
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

export type LLMProviderType = "openai" | "deepseek" | "lmstudio" | "google" | "custom";

export interface LLMProvider {
  id: number;
  name: string;
  provider_type: LLMProviderType;
  base_url: string;
  model: string;
  has_api_key: boolean;
  masked_api_key: string | null;
  timeout_seconds: number;
  structured_output_mode: "json_schema" | "json_object" | null;
  config_version: number;
  tested_version: number | null;
  test_status: "untested" | "success" | "failed";
  last_tested_at: string | null;
  last_test_error: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LLMProviderWrite {
  name: string;
  provider_type: LLMProviderType;
  base_url: string;
  model: string;
  api_key?: string | null;
  clear_api_key?: boolean;
  timeout_seconds: number;
}

export type AISystemPromptFeature = "chat" | "parse_menu" | "explain_plan" | "suggest_swap";

export interface AISystemPrompt {
  feature: AISystemPromptFeature;
  content: string;
  is_custom: boolean;
  updated_at: string | null;
}

export interface AIRequestLog {
  id: number;
  user_id: number | null;
  provider_config_id: number | null;
  feature: string;
  provider_type: string;
  model: string;
  status: "success" | "error";
  latency_ms: number;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  error_message: string | null;
  created_at: string;
  expires_at: string;
  request_data?: Record<string, unknown>;
  response_data?: unknown;
}
