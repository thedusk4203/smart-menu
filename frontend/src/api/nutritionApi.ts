import { api } from "../lib/apiClient";
import type { NutritionInput, NutritionTarget } from "../types";

export const nutritionApi = {
  // Thuan tinh toan, khong can dang nhap.
  calculateTarget: (input: NutritionInput) =>
    api.post<NutritionTarget>("/api/nutrition/target", input, { auth: false }),
};
