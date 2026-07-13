import { api, qs } from "../lib/apiClient";
import type { DishDetail, DishSummary, DishType, ListParams } from "../types";

interface DishListParams extends ListParams {
  dish_type?: DishType;
}

export const dishApi = {
  list: (params: DishListParams = {}) =>
    api.get<DishSummary[]>(`/api/dishes${qs({ limit: 24, ...params })}`),

  get: (id: number) => api.get<DishDetail>(`/api/dishes/${id}`),
};
