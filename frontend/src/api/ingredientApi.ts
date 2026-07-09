import { api, qs } from "../lib/apiClient";
import type {
  FoodGroup, Ingredient, IngredientCreate, IngredientUpdate, ListParams,
} from "../types";

interface IngredientListParams extends ListParams {
  food_group?: FoodGroup;
}

export const ingredientApi = {
  list: (params: IngredientListParams = {}) =>
    api.get<Ingredient[]>(`/api/ingredients${qs({ active_only: true, limit: 100, ...params })}`),

  get: (id: number) => api.get<Ingredient>(`/api/ingredients/${id}`),

  create: (data: IngredientCreate) => api.post<Ingredient>("/api/ingredients", data),

  update: (id: number, data: IngredientUpdate) =>
    api.put<Ingredient>(`/api/ingredients/${id}`, data),

  remove: (id: number) => api.del<void>(`/api/ingredients/${id}`),
};
