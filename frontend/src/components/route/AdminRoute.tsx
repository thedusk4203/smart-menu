import { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../../context/AuthContext";
import { isAdminRole } from "../../lib/roles";
import { FullPageSpinner } from "../ui";

export function AdminRoute() {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user && !isAdminRole(user.role)) {
      toast.error("Bạn không có quyền truy cập khu vực quản trị.");
    }
  }, [loading, user]);

  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (!isAdminRole(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
