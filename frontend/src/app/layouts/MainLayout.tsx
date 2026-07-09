// File: frontend/src/app/layouts/MainLayout.tsx
// Layout cho trang bên trong: CÓ thanh menu + nút đăng xuất.
// Chưa đăng nhập thì đá về trang Login.
import { useEffect, useState } from "react";
import { getMe } from "../../api/authApi";
import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom";
import { User, History, PlusCircle, Utensils, ShoppingCart, ChefHat, Carrot, Shield, LogOut, LayoutDashboard } from "lucide-react";
import toast from "react-hot-toast";
import { isAuthenticated } from "../../shared/utils/auth";
import { logout } from "../../api/authApi";

export default function MainLayout() {
  const navigate = useNavigate();

  // Đọc role thẳng từ JWT token (phần giữa, giải mã base64) — không cần gọi API
  const isAdmin = (() => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) return false;
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.role === "admin";
    } catch {
      return false;
    }
  })();

  if (!isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  const handleLogout = async () => {
    await logout();
    toast.success("Đã đăng xuất");
    navigate("/");
  };

  // NavLink tự thêm class "active" cho trang đang xem.
  // cursor-pointer = con trỏ thành hình bàn tay khi rê chuột.
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 font-semibold transition-colors cursor-pointer ${
      isActive
        ? "text-green-600 border-b-2 border-green-600 pb-1"  // trang đang xem: đậm + gạch chân
        : "text-gray-500 hover:text-green-600"                // trang khác: xám, rê vào thì xanh
    }`;

  return (
    <>
      <nav className="bg-white shadow-md p-4 flex justify-center flex-wrap items-center gap-6 md:gap-8 relative z-50">
        <NavLink to="/profile" className={linkClass}>
          <User className="w-5 h-5" /> <span className="hidden md:inline">Hồ Sơ</span>
        </NavLink>
        <NavLink to="/history" className={linkClass}>
          <History className="w-5 h-5" /> <span className="hidden md:inline">Lịch Sử</span>
        </NavLink>
        <NavLink to="/create-menu" className={linkClass}>
          <PlusCircle className="w-5 h-5" /> <span className="hidden md:inline">Tạo Thực Đơn</span>
        </NavLink>
        <NavLink to="/menu-result" className={linkClass}>
          <Utensils className="w-5 h-5" /> <span className="hidden md:inline">Kết Quả</span>
        </NavLink>
        <NavLink to="/ingredients" className={linkClass}>
          <Carrot className="w-5 h-5" /> <span className="hidden md:inline">Nguyên Liệu</span>
        </NavLink>
        <NavLink to="/food-detail" className={linkClass}>
          <ChefHat className="w-5 h-5" /> <span className="hidden md:inline">Món Ăn</span>
        </NavLink>
        <NavLink to="/shopping-list" className={linkClass}>
          <ShoppingCart className="w-5 h-5" /> <span className="hidden md:inline">Đi Chợ</span>
        </NavLink>
        {isAdmin && (
          <NavLink to="/admin/users" className={linkClass}>
            <Shield className="w-5 h-5" /> <span className="hidden md:inline">Quản Trị</span>
          </NavLink>
        )}
        {isAdmin && (
          <NavLink to="/admin/ingredients" className={linkClass}>
            <Carrot className="w-5 h-5" /> <span className="hidden md:inline">QL Nguyên Liệu</span>
          </NavLink>
        )}
        {isAdmin && (
          <NavLink to="/admin/meals" className={linkClass}>
            <ChefHat className="w-5 h-5" /> <span className="hidden md:inline">QL Món Ăn</span>
          </NavLink>
        )}
        {isAdmin && (
          <NavLink to="/admin/dashboard" className={linkClass}>
            <LayoutDashboard className="w-5 h-5" /> <span className="hidden md:inline">Tổng Quan</span>
          </NavLink>
        )}
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-red-500 hover:text-red-600 font-semibold transition-colors cursor-pointer"
        >
          <LogOut className="w-5 h-5" /> <span className="hidden md:inline">Đăng Xuất</span>
        </button>
      </nav>

      <Outlet />
    </>
  );
}