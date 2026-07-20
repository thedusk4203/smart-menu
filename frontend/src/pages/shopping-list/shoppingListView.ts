import type { ShoppingListItem, ShoppingPurchaseItem } from "../../api/mealPlanApi";

export interface ShoppingDisplayRow {
  key: string;
  ingredientId: number;
  name: string;
  unit: string;
  itemKind: "purchase" | "pantry";
  requiredQuantity: number;
  purchaseQuantity: number;
  estimatedCost: number;
  sourceItemIds: number[];
  sourceItemKeys: string[];
  isPurchased: boolean;
  isPartiallyPurchased: boolean;
}

function itemKey(item: ShoppingListItem): string {
  return item.item_key ?? `${item.ingredient_id}__${item.unit}`;
}

function rowFromItem(
  item: ShoppingListItem,
  purchase: ShoppingPurchaseItem | undefined,
): ShoppingDisplayRow {
  return {
    key: itemKey(item),
    ingredientId: item.ingredient_id,
    name: item.name,
    unit: item.unit,
    itemKind: item.item_kind ?? "purchase",
    requiredQuantity: purchase?.required_quantity ?? item.quantity,
    purchaseQuantity: purchase?.purchase_quantity ?? item.quantity,
    estimatedCost: purchase?.purchase_cost ?? item.estimated_cost,
    sourceItemIds: item.id == null ? [] : [item.id],
    sourceItemKeys: [itemKey(item)],
    isPurchased: item.is_purchased,
    isPartiallyPurchased: false,
  };
}

export function buildShoppingRows(
  items: ShoppingListItem[],
  purchaseItems: ShoppingPurchaseItem[],
  aggregateWholePlan: boolean,
): ShoppingDisplayRow[] {
  const purchasesByKey = new Map(
    purchaseItems.map((item) => [itemKey(item), item]),
  );
  const rows = items.map((item) => rowFromItem(item, purchasesByKey.get(itemKey(item))));
  if (!aggregateWholePlan) return rows;

  const grouped = new Map<string, ShoppingDisplayRow & { purchasedSources: number }>();
  for (const row of rows) {
    const groupKey = `${row.itemKind}:${row.ingredientId}:${row.unit}`;
    const existing = grouped.get(groupKey);
    if (!existing) {
      grouped.set(groupKey, {
        ...row,
        key: groupKey,
        purchasedSources: row.isPurchased ? 1 : 0,
      });
      continue;
    }
    existing.requiredQuantity += row.requiredQuantity;
    existing.purchaseQuantity += row.purchaseQuantity;
    existing.estimatedCost += row.estimatedCost;
    existing.sourceItemIds.push(...row.sourceItemIds);
    existing.sourceItemKeys.push(...row.sourceItemKeys);
    existing.purchasedSources += row.isPurchased ? 1 : 0;
  }

  return [...grouped.values()].map(({ purchasedSources, ...row }) => {
    const sourceCount = row.sourceItemKeys.length;
    return {
      ...row,
      isPurchased: sourceCount > 0 && purchasedSources === sourceCount,
      isPartiallyPurchased: purchasedSources > 0 && purchasedSources < sourceCount,
    };
  });
}

