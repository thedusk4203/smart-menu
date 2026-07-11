import { api, qs } from "../lib/apiClient";
import type { RegisterInput, User, UserUpdateInput } from "../types";

// Cac endpoint /api/users/* yeu cau quyen admin.
export const userApi = {
  list: (limit = 100, offset = 0) =>
    api.get<User[]>(`/api/users${qs({ limit, offset })}`),

  get: (id: number) => api.get<User>(`/api/users/${id}`),

  create: (input: RegisterInput) =>
    api.post<User>("/api/users", {
      email: input.email,
      password: input.password,
      full_name: input.full_name ?? null,
      role: input.role ?? "user",
    }),

  update: (id: number, input: UserUpdateInput) =>
    api.put<User>(`/api/users/${id}`, input),

  remove: (id: number) => api.del<void>(`/api/users/${id}`),
};
