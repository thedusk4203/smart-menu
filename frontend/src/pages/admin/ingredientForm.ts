import type { AdminIngredient, AdminIngredientWrite, IngredientPurchaseMode } from "../../types/admin";
import type { FoodGroup } from "../../types";


export type IngredientForm = {
  name: string; food_group: FoodGroup; default_unit: string; grams_per_unit: string; is_active: boolean;
  calories: string; protein_g: string; carbs_g: string; fat_g: string; fiber_g: string;
  price: string; price_unit: string; price_per_default_unit: string; price_source: string;
  purchase_mode: IngredientPurchaseMode; purchase_increment: string;
  room_shelf_life_days: string; fridge_shelf_life_days: string; freezer_shelf_life_days: string;
  shelf_life_source: string; shelf_life_reviewed_at: string;
};

export const EMPTY_FORM: IngredientForm = {
  name: "", food_group: "protein", default_unit: "g", grams_per_unit: "1", is_active: true,
  calories: "", protein_g: "", carbs_g: "", fat_g: "", fiber_g: "",
  price: "", price_unit: "kg", price_per_default_unit: "", price_source: "",
  purchase_mode: "regular", purchase_increment: "", room_shelf_life_days: "",
  fridge_shelf_life_days: "", freezer_shelf_life_days: "",
  shelf_life_source: "", shelf_life_reviewed_at: "",
};

export function ingredientToForm(item: AdminIngredient): IngredientForm {
  return {
    name: item.name, food_group: item.food_group, default_unit: item.default_unit,
    grams_per_unit: String(item.grams_per_unit), is_active: item.is_active,
    calories: item.calories == null ? "" : String(item.calories),
    protein_g: item.protein_g == null ? "" : String(item.protein_g),
    carbs_g: item.carbs_g == null ? "" : String(item.carbs_g),
    fat_g: item.fat_g == null ? "" : String(item.fat_g),
    fiber_g: item.fiber_g == null ? "" : String(item.fiber_g),
    price: item.latest_price == null ? "" : String(item.latest_price),
    price_unit: item.price_unit || "kg",
    price_per_default_unit: item.latest_price_per_unit == null ? "" : String(item.latest_price_per_unit),
    price_source: item.price_source || "",
    purchase_mode: item.purchase_mode,
    purchase_increment: item.purchase_increment == null ? "" : String(item.purchase_increment),
    room_shelf_life_days: item.room_shelf_life_days == null ? "" : String(item.room_shelf_life_days),
    fridge_shelf_life_days: item.fridge_shelf_life_days == null ? "" : String(item.fridge_shelf_life_days),
    freezer_shelf_life_days: item.freezer_shelf_life_days == null ? "" : String(item.freezer_shelf_life_days),
    shelf_life_source: item.shelf_life_source || "",
    shelf_life_reviewed_at: item.shelf_life_reviewed_at || "",
  };
}

export function ingredientToPayload(form: IngredientForm): AdminIngredientWrite {
  const nutritionValues = [form.calories, form.protein_g, form.carbs_g, form.fat_g, form.fiber_g];
  const hasNutrition = nutritionValues.some((value) => value.trim() !== "");
  const hasPrice = form.price.trim() !== "" || form.price_per_default_unit.trim() !== "";
  return {
    name: form.name.trim(), food_group: form.food_group, default_unit: form.default_unit.trim(),
    grams_per_unit: Number(form.grams_per_unit), is_active: form.is_active,
    purchase_mode: form.purchase_mode,
    purchase_increment: form.purchase_mode === "regular" && form.purchase_increment ? Number(form.purchase_increment) : null,
    room_shelf_life_days: form.purchase_mode === "regular" && form.room_shelf_life_days !== "" ? Number(form.room_shelf_life_days) : null,
    fridge_shelf_life_days: form.purchase_mode === "regular" && form.fridge_shelf_life_days !== "" ? Number(form.fridge_shelf_life_days) : null,
    freezer_shelf_life_days: form.purchase_mode === "regular" && form.freezer_shelf_life_days !== "" ? Number(form.freezer_shelf_life_days) : null,
    shelf_life_source: form.purchase_mode === "regular" ? form.shelf_life_source.trim() || null : null,
    shelf_life_reviewed_at: form.purchase_mode === "regular" ? form.shelf_life_reviewed_at || null : null,
    nutrition: hasNutrition ? {
      calories: Number(form.calories || 0), protein_g: Number(form.protein_g || 0),
      carbs_g: Number(form.carbs_g || 0), fat_g: Number(form.fat_g || 0), fiber_g: Number(form.fiber_g || 0),
    } : null,
    price: hasPrice ? {
      price: Number(form.price), unit: form.price_unit.trim(),
      price_per_default_unit: Number(form.price_per_default_unit), source: form.price_source.trim() || null,
    } : null,
  };
}

