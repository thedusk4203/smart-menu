import { api } from "../lib/apiClient";

export interface Tag { id: number; name: string; is_active: boolean; }

export const tagApi = {
  active: () => api.get<Tag[]>("/api/tags"),
  listAdmin: (search = "") => api.get<Tag[]>(`/api/admin/tags${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  create: (name: string) => api.post<Tag>("/api/admin/tags", { name }),
  rename: (id: number, name: string) => api.put<Tag>(`/api/admin/tags/${id}`, { name }),
  setActive: (id: number, is_active: boolean) => api.patch<Tag>(`/api/admin/tags/${id}/active`, { is_active }),
};
