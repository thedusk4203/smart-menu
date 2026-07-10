import { NavLink, Outlet, useNavigate } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import {
  ChefHat, ClipboardCheck, Database, FileUp, LayoutDashboard,
  Leaf, LogOut, Salad, Settings2, Users,
} from "lucide-react";
import toast from "react-hot-toast";
import { useAuth } from "../../context/AuthContext";
import { ROLE_LABELS } from "../../lib/labels";

interface AdminNavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  superOnly?: boolean;
}

const ADMIN_NAV: AdminNavItem[] = [
  { to: "/admin", label: "Tổng quan", icon: LayoutDashboard },
  { to: "/admin/users", label: "Người dùng", icon: Users, superOnly: true },
  { to: "/admin/ingredients", label: "Nguyên liệu", icon: Salad },
  { to: "/admin/dishes", label: "Món thành phần", icon: ChefHat },
  { to: "/admin/meal-sets", label: "Bữa / Mâm món", icon: Database },
  { to: "/admin/quality", label: "Chất lượng dữ liệu", icon: ClipboardCheck },
  { to: "/admin/imports", label: "Lịch sử import", icon: FileUp },
];

function navClass(active: boolean): string {
  return `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 ${
    active
      ? "bg-brand-100 text-brand-800"
      : "text-gray-600 hover:bg-sand-100 hover:text-gray-900"
  }`;
}

export function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isSuper = user?.role === "admin" || user?.role === "super_admin";
  const items = ADMIN_NAV.filter((item) => !item.superOnly || isSuper);

  const handleLogout = async () => {
    await logout();
    toast.success("Đã đăng xuất.");
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-[#f7f9f8] text-gray-900">
      <a
        href="#admin-main"
        className="fixed left-4 top-2 z-50 -translate-y-16 rounded-lg bg-gray-900 px-3 py-2 text-sm text-white transition focus:translate-y-0"
      >
        Bỏ qua điều hướng
      </a>

      <header className="sticky top-0 z-30 border-b border-sand-200 bg-white">
        <div className="flex h-16 items-center justify-between gap-4 px-4 lg:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <NavLink to="/admin" className="flex shrink-0 items-center gap-2" aria-label="Trang tổng quan quản trị">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-700 text-white">
                <Leaf className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className="hidden font-bold sm:inline">Smart Menu</span>
            </NavLink>
            <span className="hidden h-6 w-px bg-sand-200 sm:block" />
            <span className="truncate text-sm font-semibold text-gray-700">Trung tâm quản trị</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden text-right md:block">
              <p className="max-w-56 truncate text-sm font-medium text-gray-800">{user?.email}</p>
              {user && <p className="text-xs text-gray-500">{ROLE_LABELS[user.role]}</p>}
            </div>
            <button
              onClick={handleLogout}
              aria-label="Đăng xuất"
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl text-gray-600 transition hover:bg-sand-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      <nav className="border-b border-sand-200 bg-white px-3 py-2 lg:hidden" aria-label="Quản trị">
        <div className="flex gap-1 overflow-x-auto">
          {items.map((item) => (
            <NavLink
              end={item.to === "/admin"}
              key={item.to}
              to={item.to}
              className={({ isActive }) => `${navClass(isActive)} shrink-0`}
            >
              <item.icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="mx-auto flex max-w-[1600px]">
        <aside className="hidden w-64 shrink-0 border-r border-sand-200 bg-white lg:block">
          <div className="sticky top-16 flex h-[calc(100vh-4rem)] flex-col p-4">
            <nav className="space-y-1" aria-label="Quản trị">
              {items.map((item) => (
                <NavLink
                  end={item.to === "/admin"}
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => navClass(isActive)}
                >
                  <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                  {item.label}
                </NavLink>
              ))}
            </nav>
            <div className="mt-auto rounded-xl bg-sand-50 p-3 text-xs leading-5 text-gray-600">
              <div className="mb-1 flex items-center gap-2 font-semibold text-gray-800">
                <Settings2 className="h-4 w-4" aria-hidden="true" /> Dữ liệu đáng tin cậy
              </div>
              Giá và dinh dưỡng được tính từ nguồn có cấu trúc, không nhập tay ở kết quả thực đơn.
            </div>
          </div>
        </aside>

        <main id="admin-main" className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
