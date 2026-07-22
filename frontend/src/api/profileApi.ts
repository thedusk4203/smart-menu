import { api } from "../lib/apiClient";
import type { Exclusion, ExclusionReason, Profile, ProfileUpdate } from "../types";

export interface AIPreferences {
  personalization_enabled: boolean;
  notice_version: string;
  consented_at: string | null;
  updated_at: string | null;
}

export const profileApi = {
  getMyProfile: () => api.get<Profile>("/api/profiles/me"),

  updateMyProfile: (update: ProfileUpdate) =>
    api.put<Profile>("/api/profiles/me", update),

  getMyAIPreferences: () =>
    api.get<AIPreferences>("/api/profiles/me/ai-preferences"),

  updateMyAIPreferences: (personalization_enabled: boolean, notice_version: string) =>
    api.put<AIPreferences>("/api/profiles/me/ai-preferences", {
      personalization_enabled,
      notice_version,
    }),

  listMyExclusions: () => api.get<Exclusion[]>("/api/profiles/me/exclusions"),

  addMyExclusion: (ingredient_id: number, reason: ExclusionReason) =>
    api.post<Exclusion>("/api/profiles/me/exclusions", { ingredient_id, reason }),

  removeMyExclusion: (ingredient_id: number) =>
    api.del<void>(`/api/profiles/me/exclusions/${ingredient_id}`),
};
