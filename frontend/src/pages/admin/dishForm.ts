import type { AdminDish, AdminDishWrite } from "../../types/admin";
import type { CookingMethod, DishType } from "../../types";


export interface FormIngredient {
  ingredient_id: number;
  name: string;
  quantity: string;
  unit: string;
  max_extra_quantity: string;
  extra_step_quantity: string;
}
export interface DishForm { name: string; dish_type: DishType; cooking_method: CookingMethod | ""; description: string; instructions: string; tags: string; is_active: boolean; ingredients: FormIngredient[]; }
export const EMPTY_FORM: DishForm = { name: "", dish_type: "savory", cooking_method: "", description: "", instructions: "", tags: "", is_active: true, ingredients: [] };

export function dishToForm(item: AdminDish): DishForm {
  return { name: item.name, dish_type: item.dish_type, cooking_method: item.cooking_method || "", description: item.description || "", instructions: item.instructions || "", tags: item.tags.join(", "), is_active: item.is_active, ingredients: item.ingredients.map((ingredient) => ({ ingredient_id: ingredient.ingredient_id, name: ingredient.name, quantity: String(ingredient.quantity), unit: ingredient.unit, max_extra_quantity: String(ingredient.max_extra_quantity || 0), extra_step_quantity: ingredient.extra_step_quantity == null ? "" : String(ingredient.extra_step_quantity) })) };
}

export function dishToPayload(form: DishForm): AdminDishWrite {
  return { name: form.name.trim(), dish_type: form.dish_type, cooking_method: form.cooking_method || null, description: form.description.trim() || null, instructions: form.instructions.trim() || null, tags: form.tags.split(",").map((tag) => tag.trim()).filter(Boolean), is_active: form.is_active, ingredients: form.ingredients.map((ingredient) => ({ ingredient_id: ingredient.ingredient_id, quantity: Number(ingredient.quantity), unit: ingredient.unit.trim(), max_extra_quantity: Number(ingredient.max_extra_quantity || 0), extra_step_quantity: ingredient.max_extra_quantity && ingredient.extra_step_quantity ? Number(ingredient.extra_step_quantity) : null })) };
}

