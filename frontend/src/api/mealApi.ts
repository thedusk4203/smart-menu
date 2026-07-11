import { api, qs } from "../lib/apiClient";
import type {
  ListParams, MealCreate, MealDetail, MealSummary, MealType, MealUpdate,
} from "../types";

interface MealListParams extends ListParams {
  meal_type?: MealType;
}

export const mealApi = {
  list: (params: MealListParams = {}) =>
    api.get<MealSummary[]>(`/api/meals${qs({ active_only: true, limit: 100, ...params })}`),

  get: (id: number) => api.get<MealDetail>(`/api/meals/${id}`),

  create: (data: MealCreate) => api.post<MealDetail>("/api/meals", data),

  update: (id: number, data: MealUpdate) => api.put<MealDetail>(`/api/meals/${id}`, data),

  remove: (id: number) => api.del<void>(`/api/meals/${id}`),
};
