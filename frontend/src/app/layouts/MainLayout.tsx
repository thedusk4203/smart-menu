import { NavLink, Outlet, useNavigate } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard, User, UtensilsCrossed, History, Salad, ChefHat,
  ShoppingCart, Sparkles, Shield, LogOut, Leaf,
} from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../../context/AuthContext";
import { ProtectedRoute } from "../../components/route/ProtectedRoute";
import { ROLE_LABELS } from "../../lib/labels";
import { ApiError } from "../../lib/apiClient";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Tổng quan", icon: LayoutDashboard },
  { to: "/profile", label: "Hồ sơ", icon: User },
  { to: "/create-menu", label: "Tạo thực đơn", icon: UtensilsCrossed },
  { to: "/history", label: "Lịch sử", icon: History },
  { to: "/ingredients", label: "Nguyên liệu", icon: Salad },
  { to: "/meals", label: "Món ăn", icon: ChefHat },
  { to: "/shopping-list", label: "Đi chợ", icon: ShoppingCart },
  { to: "/ai-chat", label: "Trợ lý AI", icon: Sparkles },
];

function linkClass(isActive: boolean): string {
  return `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
    isActive ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-sand-100 hover:text-gray-900"
  }`;
}

export function MainLayout() {
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();

  if (loading || !user) return <ProtectedRoute />;

  const isAdmin = user.role === "admin";

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Đã đăng xuất.");
      navigate("/login");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    }
  };

  const navItems = isAdmin
    ? [...NAV_ITEMS, { to: "/admin/users", label: "Quản trị", icon: Shield }]
    : NAV_ITEMS;

  return (
    <div className="min-h-screen bg-sand-50">
      <header className="sticky top-0 z-30 border-b border-sand-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3">
          <NavLink to="/dashboard" className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
              <Leaf className="h-5 w-5" />
            </span>
            <span className="text-lg font-bold text-gray-900">Smart Menu</span>
          </NavLink>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-gray-800">{user.email}</p>
              <p className="text-xs text-gray-400">{ROLE_LABELS[user.role]}</p>
            </div>
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 rounded-xl border border-sand-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-sand-100"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Đăng xuất</span>
            </button>
          </div>
        </div>
      </header>

      {/* Nav ngang cho man hinh nho */}
      <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 pt-4 lg:hidden">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex shrink-0 items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium transition ${
                isActive ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-sand-100"
              }`
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mx-auto flex max-w-7xl gap-6 px-4 py-6">
        <aside className="hidden w-56 shrink-0 lg:block">
          <nav className="sticky top-20 space-y-1">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => linkClass(isActive)}>
                <item.icon className="h-5 w-5 shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
