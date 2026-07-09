import { api } from "../lib/apiClient";
import type { Exclusion, ExclusionReason, Profile, ProfileUpdate } from "../types";

export const profileApi = {
  getMyProfile: () => api.get<Profile>("/api/profiles/me"),

  updateMyProfile: (update: ProfileUpdate) =>
    api.put<Profile>("/api/profiles/me", update),

  listMyExclusions: () => api.get<Exclusion[]>("/api/profiles/me/exclusions"),

  addMyExclusion: (ingredient_id: number, reason: ExclusionReason) =>
    api.post<Exclusion>("/api/profiles/me/exclusions", { ingredient_id, reason }),

  removeMyExclusion: (ingredient_id: number) =>
    api.del<void>(`/api/profiles/me/exclusions/${ingredient_id}`),
};
