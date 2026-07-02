// File: frontend/src/shared/utils/auth.ts
// Tiện ích kiểm tra trạng thái đăng nhập, dùng chung toàn app.
import { getToken } from "../../api/httpClient";

export const isAuthenticated = (): boolean => !!getToken();