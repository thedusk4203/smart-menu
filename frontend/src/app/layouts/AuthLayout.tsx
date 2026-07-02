// File: frontend/src/app/layouts/AuthLayout.tsx
// TODO: Implement logic here
// File: frontend/src/app/layouts/AuthLayout.tsx
// Layout cho trang công khai (Login, Register): KHÔNG có thanh menu.
// Nếu đã đăng nhập rồi mà vào lại Login thì đưa thẳng vào trong.
import { Navigate, Outlet } from "react-router-dom";
import { isAuthenticated } from "../../shared/utils/auth";

export default function AuthLayout() {
  if (isAuthenticated()) {
    return <Navigate to="/profile" replace />;
  }
  return <Outlet />;
}