import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { isAdminRole } from "../../lib/roles";
import { FullPageSpinner } from "../ui";

export function UserRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <FullPageSpinner label="Đang kiểm tra phiên đăng nhập..." />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  if (isAdminRole(user.role)) return <Navigate to="/admin" replace />;

  return <Outlet />;
}
