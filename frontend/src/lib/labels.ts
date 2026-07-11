// Nhan tieng Viet cho cac enum + tien ich mau sac.
import type {
  ActivityLevel, CookingMethod, DishType, ExclusionReason, FitnessGoal,
  FoodGroup, Gender, MealType, UserRole,
} from "../types";

export const GENDER_LABELS: Record<Gender, string> = {
  male: "Nam",
  female: "Nữ",
};

export const ACTIVITY_LABELS: Record<ActivityLevel, string> = {
  sedentary: "Ít vận động",
  light: "Vận động nhẹ",
  moderate: "Vận động vừa",
  active: "Vận động nhiều",
};

export const GOAL_LABELS: Record<FitnessGoal, string> = {
  maintain: "Giữ cân",
  lose_weight: "Giảm cân",
  gain_muscle: "Tăng cơ",
  gain_weight: "Tăng cân",
};

export const ROLE_LABELS: Record<UserRole, string> = {
  user: "Người dùng",
  admin: "Quản trị",
  data_editor: "Biên tập dữ liệu",
  super_admin: "Quản trị hệ thống",
};

export const FOOD_GROUP_LABELS: Record<FoodGroup, string> = {
  protein: "Đạm",
  vegetable: "Rau củ",
  grain: "Tinh bột",
  dairy: "Sữa",
  fat: "Chất béo",
  fruit: "Trái cây",
  other: "Khác",
};

export const MEAL_TYPE_LABELS: Record<MealType, string> = {
  breakfast: "Bữa sáng",
  lunch: "Bữa trưa",
  dinner: "Bữa tối",
};

export const DISH_TYPE_LABELS: Record<DishType, string> = {
  staple: "Tinh bột",
  savory: "Món mặn",
  soup: "Canh",
  vegetable_side: "Rau/Món phụ",
  side: "Món phụ",
  breakfast: "Món sáng",
};

export const COOKING_METHOD_LABELS: Record<CookingMethod, string> = {
  stir_fry: "Xào",
  boil: "Luộc",
  soup: "Canh",
  braise: "Kho",
  steam: "Hấp",
};

export const EXCLUSION_REASON_LABELS: Record<ExclusionReason, string> = {
  allergy: "Dị ứng",
  dislike: "Không thích",
};

// Mau badge theo loai bua (dung class Tailwind).
export const MEAL_TYPE_STYLES: Record<MealType, string> = {
  breakfast: "bg-accent-100 text-accent-700",
  lunch: "bg-brand-100 text-brand-700",
  dinner: "bg-indigo-100 text-indigo-700",
};

export const FOOD_GROUP_STYLES: Record<FoodGroup, string> = {
  protein: "bg-rose-100 text-rose-700",
  vegetable: "bg-brand-100 text-brand-700",
  grain: "bg-amber-100 text-amber-700",
  dairy: "bg-sky-100 text-sky-700",
  fat: "bg-orange-100 text-orange-700",
  fruit: "bg-pink-100 text-pink-700",
  other: "bg-sand-200 text-gray-700",
};
