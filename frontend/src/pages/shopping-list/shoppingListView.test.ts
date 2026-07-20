import { describe, expect, it } from "vitest";
import type { ShoppingListItem, ShoppingPurchaseItem } from "../../api/mealPlanApi";
import { buildShoppingRows } from "./shoppingListView";

const purchases: ShoppingPurchaseItem[] = [
  {
    id: 11, ingredient_id: 1, name: "Thịt gà", unit: "g", quantity: 200,
    estimated_cost: 40_000, is_purchased: true, item_key: "purchase:1:1",
    item_kind: "purchase", scheduled_day: 1, required_quantity: 180,
    purchase_quantity: 200, purchase_cost: 40_000, purchase_increment: 100,
    block_count: 2, remaining_quantity: 20, expired_waste_quantity: 0,
    carryover_quantity: 20, storage_splits: [],
  },
  {
    id: 12, ingredient_id: 1, name: "Thịt gà", unit: "g", quantity: 100,
    estimated_cost: 20_000, is_purchased: false, item_key: "purchase:1:4",
    item_kind: "purchase", scheduled_day: 4, required_quantity: 90,
    purchase_quantity: 100, purchase_cost: 20_000, purchase_increment: 100,
    block_count: 1, remaining_quantity: 10, expired_waste_quantity: 0,
    carryover_quantity: 10, storage_splits: [],
  },
];

const pantry: ShoppingListItem = {
  id: 13, ingredient_id: 2, name: "Hạt tiêu", unit: "g", quantity: 2,
  estimated_cost: 0, is_purchased: false, item_key: "pantry:2", item_kind: "pantry",
};

describe("buildShoppingRows", () => {
  it("gộp các lần mua cùng nguyên liệu trong toàn kế hoạch", () => {
    const rows = buildShoppingRows([...purchases, pantry], purchases, true);

    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({
      requiredQuantity: 270,
      purchaseQuantity: 300,
      estimatedCost: 60_000,
      sourceItemIds: [11, 12],
      isPurchased: false,
      isPartiallyPurchased: true,
    });
    expect(rows[1]).toMatchObject({ name: "Hạt tiêu", itemKind: "pantry" });
  });

  it("giữ từng lần mua khi người dùng chọn một ngày", () => {
    const rows = buildShoppingRows(purchases, purchases, false);

    expect(rows).toHaveLength(2);
    expect(rows.map((row) => row.sourceItemIds)).toEqual([[11], [12]]);
  });

  it("không gộp cùng nguyên liệu nếu khác đơn vị", () => {
    const itemInKg = { ...purchases[1], id: 14, unit: "kg", item_key: "purchase:1:5" };
    const rows = buildShoppingRows([purchases[0], itemInKg], [purchases[0], itemInKg], true);

    expect(rows).toHaveLength(2);
  });
});

