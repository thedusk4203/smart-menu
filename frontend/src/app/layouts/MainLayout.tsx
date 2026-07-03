// File: frontend/src/app/layouts/MainLayout.tsx
// TODO: Implement logic here
// File: frontend/src/app/layouts/MainLayout.tsx
// Layout cho trang bên trong: CÓ thanh menu + nút đăng xuất.
// Chưa đăng nhập thì đá về trang Login.
import { Link, Navigate, Outlet, useNavigate } from "react-router-dom";
import { User, History, PlusCircle, Utensils, ShoppingCart, ChefHat, LogOut } from "lucide-react";
import toast from "react-hot-toast";
import { isAuthenticated } from "../../shared/utils/auth";
import { logout } from "../../api/authApi";

export default function MainLayout() {
  const navigate = useNavigate();

  if (!isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  const handleLogout = async () => {
    await logout();
    toast.success("Đã đăng xuất");
    navigate("/");
  };

  const linkClass =
    "flex items-center gap-2 text-gray-500 hover:text-green-600 font-semibold transition-colors";

  return (
    <>
      <nav className="bg-white shadow-md p-4 flex justify-center flex-wrap items-center gap-6 md:gap-8 relative z-50">
        <Link to="/profile" className={linkClass}>
          <User className="w-5 h-5" /> <span className="hidden md:inline">Hồ Sơ</span>
        </Link>
        <Link to="/history" className={linkClass}>
          <History className="w-5 h-5" /> <span className="hidden md:inline">Lịch Sử</span>
        </Link>
        <Link to="/create-menu" className={linkClass}>
          <PlusCircle className="w-5 h-5" /> <span className="hidden md:inline">Tạo Thực Đơn</span>
        </Link>
        <Link to="/menu-result" className={linkClass}>
          <Utensils className="w-5 h-5" /> <span className="hidden md:inline">Kết Quả</span>
        </Link>
        <Link to="/shopping-list" className={linkClass}>
          <ShoppingCart className="w-5 h-5" /> <span className="hidden md:inline">Đi Chợ</span>
        </Link>
        <Link to="/food-detail" className={linkClass}>
          <ChefHat className="w-5 h-5" /> <span className="hidden md:inline">Món Ăn</span>
        </Link>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-red-500 hover:text-red-600 font-semibold transition-colors"
        >
          <LogOut className="w-5 h-5" /> <span className="hidden md:inline">Đăng Xuất</span>
        </button>
      </nav>

      {/* Nội dung trang con hiển thị ở đây */}
      <Outlet />
    </>
  );
}