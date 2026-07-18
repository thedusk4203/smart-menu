import { api, qs } from "../lib/apiClient";
import type { UserRole } from "../types";
import type {
  AdminDashboardSummary, AdminDish, AdminDishWrite, AdminIngredient,
  AdminIngredientWrite, AdminUser,
  ImportJob, ImportPreview, Page, QualityIssue,
  AIRequestLog, AISystemPrompt, AISystemPromptFeature, LLMProvider, LLMProviderWrite,
} from "../types/admin";

export const adminApi = {
  dashboard: () => api.get<AdminDashboardSummary>("/api/admin/dashboard/summary"),

  users: (params: Record<string, unknown>) =>
    api.get<Page<AdminUser>>(`/api/admin/users${qs(params)}`),
  createUser: (data: { email: string; password: string; full_name?: string; role: UserRole }) =>
    api.post<AdminUser>("/api/admin/users", data),
  updateUserRole: (id: number, role: UserRole) =>
    api.patch<AdminUser>(`/api/admin/users/${id}/role`, { role }),
  updateUserStatus: (id: number, is_active: boolean) =>
    api.patch<AdminUser>(`/api/admin/users/${id}/status`, { is_active }),

  ingredients: (params: Record<string, unknown>) =>
    api.get<Page<AdminIngredient>>(`/api/admin/ingredients${qs(params)}`),
  ingredient: (id: number) => api.get<AdminIngredient>(`/api/admin/ingredients/${id}`),
  createIngredient: (data: AdminIngredientWrite) =>
    api.post<AdminIngredient>("/api/admin/ingredients", data),
  updateIngredient: (id: number, data: AdminIngredientWrite) =>
    api.put<AdminIngredient>(`/api/admin/ingredients/${id}`, data),
  setIngredientActive: (id: number, is_active: boolean) =>
    api.patch<AdminIngredient>(`/api/admin/ingredients/${id}/active`, { is_active }),
  deleteIngredient: (id: number) => api.del<void>(`/api/admin/ingredients/${id}`),
  exportIngredients: (format: "csv" | "xlsx", params: Record<string, unknown> = {}) =>
    api.getDownload(`/api/admin/ingredients/export${qs({ format, ...params })}`),

  dishes: (params: Record<string, unknown>) =>
    api.get<Page<AdminDish>>(`/api/admin/dishes${qs(params)}`),
  dish: (id: number) => api.get<AdminDish>(`/api/admin/dishes/${id}`),
  createDish: (data: AdminDishWrite) => api.post<AdminDish>("/api/admin/dishes", data),
  updateDish: (id: number, data: AdminDishWrite) =>
    api.put<AdminDish>(`/api/admin/dishes/${id}`, data),
  setDishActive: (id: number, is_active: boolean) =>
    api.patch<AdminDish>(`/api/admin/dishes/${id}/active`, { is_active }),
  deleteDish: (id: number) => api.del<void>(`/api/admin/dishes/${id}`),
  exportDishes: (format: "csv" | "xlsx", params: Record<string, unknown> = {}) =>
    api.getDownload(`/api/admin/dishes/export${qs({ format, ...params })}`),

  quality: (params: Record<string, unknown>) =>
    api.get<Page<QualityIssue>>(`/api/admin/quality/issues${qs(params)}`),

  previewImport: (entityType: "ingredients" | "dishes", file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<ImportPreview>(`/api/admin/imports/preview${qs({ entity_type: entityType })}`, form);
  },
  downloadTemplate: (entityType: "ingredients" | "dishes", format: "csv" | "xlsx") =>
    api.getBlob(`/api/admin/imports/template${qs({ entity_type: entityType, format })}`),
  commitImport: (jobId: number, replace_rows: number[]) =>
    api.post<{ job_id: number; status: string; created: number; updated: number; skipped: number }>(
      `/api/admin/imports/${jobId}/commit`, { replace_rows },
    ),
  importJobs: (params: Record<string, unknown> = {}) =>
    api.get<Page<ImportJob>>(`/api/admin/imports${qs(params)}`),

  aiProviders: () => api.get<LLMProvider[]>("/api/admin/ai/providers"),
  createAIProvider: (data: LLMProviderWrite) =>
    api.post<LLMProvider>("/api/admin/ai/providers", data),
  updateAIProvider: (id: number, data: LLMProviderWrite) =>
    api.put<LLMProvider>(`/api/admin/ai/providers/${id}`, data),
  cloneAIProvider: (id: number) =>
    api.post<LLMProvider>(`/api/admin/ai/providers/${id}/clone`),
  testAIProvider: (id: number) =>
    api.post<{ provider: LLMProvider; models: string[] }>(`/api/admin/ai/providers/${id}/test`),
  discoverAIModels: (id: number) =>
    api.post<string[]>(`/api/admin/ai/providers/${id}/discover-models`),
  activateAIProvider: (id: number) =>
    api.post<LLMProvider>(`/api/admin/ai/providers/${id}/activate`),
  deactivateAIProvider: (id: number) =>
    api.post<LLMProvider>(`/api/admin/ai/providers/${id}/deactivate`),
  deleteAIProvider: (id: number) => api.del<void>(`/api/admin/ai/providers/${id}`),
  aiSystemPrompts: () => api.get<AISystemPrompt[]>("/api/admin/ai/prompts"),
  updateAISystemPrompt: (feature: AISystemPromptFeature, content: string) =>
    api.put<AISystemPrompt>(`/api/admin/ai/prompts/${feature}`, { content }),
  resetAISystemPrompt: (feature: AISystemPromptFeature) =>
    api.del<AISystemPrompt>(`/api/admin/ai/prompts/${feature}`),
  aiLogs: (params: Record<string, unknown> = {}) =>
    api.get<Page<AIRequestLog>>(`/api/admin/ai/logs${qs(params)}`),
  aiLog: (id: number) => api.get<AIRequestLog>(`/api/admin/ai/logs/${id}`),
  purgeAILogs: (before: string) =>
    api.post<{ deleted: number }>("/api/admin/ai/logs/purge", { before }),
};
