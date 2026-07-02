// File: frontend/src/api/authApi.ts
import { apiRequest, clearToken, saveToken } from "./httpClient";

export interface UserInfo {
  id: number;
  email: string;
  role: "user" | "admin";
  is_active: boolean;
}

// Đăng ký tài khoản mới
export async function register(
  email: string,
  password: string,
  fullName?: string
): Promise<UserInfo> {
  return apiRequest<UserInfo>("/api/auth/register", {
    method: "POST",
    body: { email, password, full_name: fullName },
  });
}

// Đăng nhập — gửi dạng form (chuẩn OAuth2), nhận JWT token
export async function login(email: string, password: string): Promise<string> {
  const data = await apiRequest<{ access_token: string; token_type: string }>(
    "/api/auth/login",
    {
      method: "POST",
      // isForm: true vì /login nhận form, không phải JSON
      isForm: true,
      body: { username: email, password },
    }
  );
  saveToken(data.access_token); // lưu token vào localStorage
  return data.access_token;
}

// Đăng xuất — xoá token ở client
export async function logout(): Promise<void> {
  try {
    await apiRequest("/api/auth/logout", { method: "POST" });
  } finally {
    clearToken(); // dù server lỗi vẫn xoá token phía client
  }
}

// Xem thông tin tài khoản đang đăng nhập
export async function getMe(): Promise<UserInfo> {
  return apiRequest<UserInfo>("/api/auth/me");
}