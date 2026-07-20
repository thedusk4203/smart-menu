import { describe, expect, it } from "vitest";

import { dishToPayload } from "./dishForm";
import { EMPTY_FORM as EMPTY_INGREDIENT, ingredientToPayload } from "./ingredientForm";


describe("admin form mappers", () => {
  it("omits optional ingredient snapshots when their fields are empty", () => {
    const payload = ingredientToPayload({
      ...EMPTY_INGREDIENT,
      name: "  Đậu hũ  ",
      default_unit: " miếng ",
      grams_per_unit: "100",
      purchase_mode: "pantry",
    });

    expect(payload.name).toBe("Đậu hũ");
    expect(payload.default_unit).toBe("miếng");
    expect(payload.purchase_increment).toBeNull();
    expect(payload.nutrition).toBeNull();
    expect(payload.price).toBeNull();
  });

  it("normalizes dish tags and flexible ingredient quantities", () => {
    const payload = dishToPayload({
      name: "  Gà xào  ",
      dish_type: "savory",
      cooking_method: "stir_fry",
      description: "",
      instructions: " Xào chín ",
      tags: " giàu đạm, nhanh, ",
      is_active: true,
      ingredients: [{
        ingredient_id: 3,
        name: "Gà",
        quantity: "120",
        unit: " g ",
        max_extra_quantity: "20",
        extra_step_quantity: "5",
      }],
    });

    expect(payload.name).toBe("Gà xào");
    expect(payload.tags).toEqual(["giàu đạm", "nhanh"]);
    expect(payload.ingredients[0]).toMatchObject({
      quantity: 120,
      unit: "g",
      max_extra_quantity: 20,
      extra_step_quantity: 5,
    });
  });
});
