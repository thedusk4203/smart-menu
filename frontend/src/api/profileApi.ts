// File: frontend/src/api/profileApi.ts
import { apiRequest } from "./httpClient";

export interface Profile {
  user_id: number;
  full_name: string | null;
  gender: "male" | "female" | "other" | null;
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  activity_level: string;
  goal: string;
  meals_per_day: number;
  daily_calorie_target: number | null;
  daily_budget: number | null;
}

export interface ProfileUpdate {
  full_name?: string;
  gender?: string;
  age?: number;
  height_cm?: number;
  weight_kg?: number;
  activity_level?: string;
  goal?: string;
  meals_per_day?: number;
  daily_calorie_target?: number;
  daily_budget?: number;
}

// Lấy hồ sơ của tài khoản đang đăng nhập
export async function getMyProfile(): Promise<Profile> {
  return apiRequest<Profile>("/api/profiles/me");
}

// Cập nhật hồ sơ của tài khoản đang đăng nhập
export async function updateMyProfile(data: ProfileUpdate): Promise<Profile> {
  return apiRequest<Profile>("/api/profiles/me", {
    method: "PUT",
    body: data,
  });
}