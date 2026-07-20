import { api } from "../lib/apiClient";

export type InventoryStatus = "projected" | "available" | "consumed" | "expired" | "discarded";

export interface InventoryLot {
  id: number;
  ingredient_id: number;
  name: string;
  quantity_remaining: number;
  reserved_quantity: number;
  unit: string;
  available_from: string;
  expires_on: string;
  storage_mode: "room" | "fridge" | "freezer" | "same_day";
  cost_basis_per_unit: number;
  source_plan_id?: number | null;
  source_plan_name?: string | null;
  status: InventoryStatus;
  created_at: string;
}

export const inventoryApi = {
  list: () => api.get<InventoryLot[]>("/api/inventory-lots"),
  update: (id: number, data: Partial<Pick<InventoryLot, "quantity_remaining" | "expires_on" | "storage_mode" | "status">>) =>
    api.patch<InventoryLot>(`/api/inventory-lots/${id}`, data),
};
