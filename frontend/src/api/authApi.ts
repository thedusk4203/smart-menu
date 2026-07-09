import { api } from "../lib/apiClient";
import type { RegisterInput, TokenResponse, User } from "../types";

export const authApi = {
  register: (input: RegisterInput) =>
    api.post<User>("/api/auth/register", {
      email: input.email,
      password: input.password,
      full_name: input.full_name ?? null,
      role: input.role ?? "user",
    }),

  // Backend dung OAuth2PasswordRequestForm -> gui form, field ten "username".
  login: (email: string, password: string) =>
    api.post<TokenResponse>(
      "/api/auth/login",
      { username: email, password },
      { form: true, auth: false }
    ),

  getMe: () => api.get<User>("/api/auth/me"),

  logout: () => api.post<{ detail: string }>("/api/auth/logout"),
};
