import { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../../context/AuthContext";
import { FullPageSpinner } from "../ui";

export function AdminRoute() {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user && user.role !== "admin") {
      toast.error("Bạn không có quyền truy cập khu vực quản trị.");
    }
  }, [loading, user]);

  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin") return <Navigate to="/dashboard" replace />;

  return <Outlet />;
}
