import { api } from "../lib/apiClient";

export type TagEntityType = "ingredient" | "dish";

export interface Tag {
  id: number;
  name: string;
  entity_type: TagEntityType;
  is_active: boolean;
}

export const tagApi = {
  active: () => api.get<Tag[]>("/api/tags"),
  listAdmin: (search = "", entityType?: TagEntityType) => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (entityType) params.set("entity_type", entityType);
    const query = params.toString();
    return api.get<Tag[]>(`/api/admin/tags${query ? `?${query}` : ""}`);
  },
  create: (name: string, entity_type: TagEntityType) => api.post<Tag>("/api/admin/tags", { name, entity_type }),
  rename: (id: number, name: string) => api.put<Tag>(`/api/admin/tags/${id}`, { name }),
  setActive: (id: number, is_active: boolean) => api.patch<Tag>(`/api/admin/tags/${id}/active`, { is_active }),
};
