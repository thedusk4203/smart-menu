// File: frontend/src/api/httpClient.ts
// HTTP client dùng chung. Tự gắn token vào header, tự xử lý lỗi 401.

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

// Lấy token từ localStorage
export const getToken = (): string | null => localStorage.getItem("access_token");

// Lưu token sau khi đăng nhập
export const saveToken = (token: string): void => localStorage.setItem("access_token", token);

// Xoá token khi đăng xuất
export const clearToken = (): void => localStorage.removeItem("access_token");

// ── Hàm gọi API chính ────────────────────────────────────────────────────

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  body?: unknown;
  isForm?: boolean; // true khi gửi dạng form (dùng cho /login)
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, isForm = false } = options;

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let bodyData: string | undefined;

  if (body !== undefined) {
    if (isForm) {
      // Dạng form — dùng cho POST /api/auth/login (chuẩn OAuth2)
      headers["Content-Type"] = "application/x-www-form-urlencoded";
      bodyData = new URLSearchParams(body as Record<string, string>).toString();
    } else {
      // Dạng JSON — dùng cho mọi endpoint còn lại
      headers["Content-Type"] = "application/json";
      bodyData = JSON.stringify(body);
    }
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: bodyData,
  });

  // 204 No Content (ví dụ DELETE thành công) — không có body JSON
  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    // Lỗi từ server — ném ra để component bắt bằng try/catch
    const message = data?.detail ?? `Lỗi ${response.status}`;
    throw new Error(message);
  }

  return data as T;
}