import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LayoutDashboard, Users, Carrot, ChefHat, AlertTriangle } from "lucide-react";
import toast from "react-hot-toast";
import { getAdminStats } from "../api/adminApi";
import type { AdminStats } from "../api/adminApi";

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch((e) => toast.error(e instanceof Error ? e.message : "Không tải được số liệu"))
      .finally(() => setLoading(false));
  }, []);

  const StatCard = ({ icon: Icon, label, value, color, onClick }: {
    icon: React.ComponentType<{ className?: string }>;
    label: string; value: number | string; color: string; onClick?: () => void;
  }) => (
    <div onClick={onClick}
      className={`bg-white rounded-2xl shadow-sm border border-slate-100 p-6 ${onClick ? "cursor-pointer hover:shadow-md hover:-translate-y-0.5 transition-all" : ""}`}>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <p className="text-3xl font-bold text-slate-800 mb-1">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );

  const AlertCard = ({ label, value, onClick }: { label: string; value: number; onClick?: () => void }) => (
    <div onClick={onClick}
      className={`bg-white rounded-2xl border p-5 ${value > 0 ? "border-orange-200 bg-orange-50/50" : "border-emerald-200 bg-emerald-50/50"} ${onClick ? "cursor-pointer hover:shadow-sm transition-all" : ""}`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${value > 0 ? "bg-orange-500" : "bg-emerald-500"}`}>
          <AlertTriangle className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <p className="text-sm text-slate-600">{label}</p>
          <p className={`text-2xl font-bold ${value > 0 ? "text-orange-700" : "text-emerald-700"}`}>{value}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-emerald-700 flex items-center gap-2 mb-1">
            <LayoutDashboard className="w-8 h-8" /> Tổng Quan
          </h1>
          <p className="text-slate-500">Số liệu hệ thống Smart Menu</p>
        </div>

        {loading ? (
          <p className="text-center text-emerald-600 font-semibold py-12">Đang tải số liệu...</p>
        ) : !stats ? (
          <p className="text-center text-slate-500 py-12">Không có dữ liệu.</p>
        ) : (
          <>
            {/* 3 thẻ chính */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
              <StatCard icon={Users} label="Tài khoản người dùng" value={stats.total_users}
                color="bg-blue-500" onClick={() => navigate("/admin/users")} />
              <StatCard icon={Carrot} label="Nguyên liệu đang hoạt động" value={stats.total_ingredients}
                color="bg-emerald-500" onClick={() => navigate("/admin/ingredients")} />
              <StatCard icon={ChefHat} label="Món ăn đang hoạt động" value={stats.total_meals}
                color="bg-teal-500" onClick={() => navigate("/admin/meals")} />
            </div>

            {/* Cảnh báo dữ liệu thiếu */}
            <h2 className="text-xl font-bold text-slate-700 mb-4">Dữ liệu cần bổ sung</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <AlertCard label="Nguyên liệu thiếu dinh dưỡng"
                value={stats.ingredients_missing_nutrition}
                onClick={() => navigate("/admin/ingredients")} />
              <AlertCard label="Nguyên liệu thiếu giá"
                value={stats.ingredients_missing_price}
                onClick={() => navigate("/admin/ingredients")} />
              <AlertCard label="Món ăn thiếu nguyên liệu"
                value={stats.meals_missing_ingredients}
                onClick={() => navigate("/admin/meals")} />
            </div>

            {stats.ingredients_missing_nutrition + stats.ingredients_missing_price + stats.meals_missing_ingredients === 0 && (
              <div className="mt-6 bg-emerald-50 border border-emerald-200 rounded-2xl p-5 text-center">
                <p className="text-emerald-700 font-semibold">✓ Toàn bộ dữ liệu đã đầy đủ, không có cảnh báo.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}