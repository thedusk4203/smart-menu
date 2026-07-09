import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  ShoppingCart,
  Sunrise,
  Sun,
  Moon,
  Flame,
  Wallet,
  RefreshCw,
  Save,
  ChefHat,
  AlertTriangle,
  Check,
} from "lucide-react";

import {
  generateMealPlan,
  isInfeasible,
  saveMealPlan,
  type GeneratedMealPlan,
  type GenerateParams,
  type PlannedMeal,
} from "../api/mealPlanApi";

// Định dạng tiền VNĐ: 920000 -> "920.000đ".
const formatVND = (n: number) => `${Math.round(n).toLocaleString("vi-VN")}đ`;

// Icon + màu theo loại bữa.
const SLOT_META: Record<string, { label: string; icon: typeof Sun; cls: string }> = {
  breakfast: { label: "Bữa Sáng", icon: Sunrise, cls: "bg-orange-50 text-orange-600" },
  lunch: { label: "Bữa Trưa", icon: Sun, cls: "bg-blue-50 text-blue-600" },
  dinner: { label: "Bữa Tối", icon: Moon, cls: "bg-indigo-50 text-indigo-600" },
};

export default function MenuResult() {
  const navigate = useNavigate();
  const location = useLocation();

  // Thực đơn + tham số sinh được truyền từ trang CreateMenu qua router state.
  const initial = (location.state ?? {}) as {
    plan?: GeneratedMealPlan;
    params?: GenerateParams;
  };

  const [plan, setPlan] = useState<GeneratedMealPlan | undefined>(initial.plan);
  const [params] = useState<GenerateParams>(initial.params ?? {});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Vào thẳng /menu-result mà không qua CreateMenu (vd: refresh) -> chưa có dữ liệu.
  if (!plan) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-emerald-50 flex flex-col items-center justify-center p-6 text-center">
        <div className="bg-emerald-100 p-5 rounded-full text-emerald-600 mb-5">
          <ChefHat className="w-10 h-10" />
        </div>
        <h1 className="text-2xl font-bold text-emerald-700 mb-2">Chưa có thực đơn</h1>
        <p className="text-gray-500 mb-6">Hãy tạo một thực đơn mới để bắt đầu.</p>
        <button
          onClick={() => navigate("/create-menu")}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-8 rounded-xl shadow-lg transition-all"
        >
          Tạo Thực Đơn
        </button>
      </div>
    );
  }

  const days = plan.plan_data.days;
  const warnings = plan.plan_data.warnings ?? [];
  const avgCalories = days.length ? Math.round(plan.total_calories / days.length) : 0;

  // "Tạo lại thực đơn khác" (FR-PLAN-05): giữ nguyên ràng buộc, đổi seed ngẫu nhiên.
  async function handleRegenerate() {
    setLoading(true);
    setError(null);
    setSaved(false);
    try {
      const seed = Math.floor(Math.random() * 1_000_000);
      const result = await generateMealPlan({ ...params, seed });
      if (isInfeasible(result)) {
        setError("Không thể tạo phương án khác: " + result.reasons.join(" "));
        return;
      }
      setPlan(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Có lỗi xảy ra, thử lại sau.");
    } finally {
      setLoading(false);
    }
  }

  // Lưu thực đơn hiện tại. Thực đơn vừa sinh chưa có ngày bắt đầu -> gán hôm nay.
  async function handleSave() {
    if (!plan) return;
    setLoading(true);
    setError(null);
    try {
      const today = new Date().toISOString().slice(0, 10);
      await saveMealPlan({
        name: plan.name,
        start_date: today,
        end_date: plan.end_date ?? undefined,
        budget_limit: plan.budget_limit ?? undefined,
        total_cost: plan.total_cost,
        total_calories: plan.total_calories,
        plan_data: plan.plan_data,
      });
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lưu thất bại, thử lại sau.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-emerald-50 p-4 md:p-8 relative pb-24">
      <div className="text-center mb-8 mt-4">
        <h1 className="text-3xl md:text-4xl font-bold text-emerald-700 mb-3">{plan.name}</h1>
        <p className="text-gray-500">Thực đơn {days.length} ngày được tối ưu theo ngân sách & dinh dưỡng</p>
      </div>

      {/* Thẻ thống kê tổng quan */}
      <div className="bg-white/80 backdrop-blur-lg p-6 md:p-8 rounded-3xl shadow-xl mb-6 max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 border border-white">
        <div className="flex items-center gap-4">
          <div className="bg-green-100 p-4 rounded-full"><Wallet className="w-8 h-8 text-green-600" /></div>
          <div>
            <p className="text-gray-500 text-sm font-bold uppercase tracking-wide">Tổng chi phí</p>
            <p className="text-3xl font-bold text-green-600">{formatVND(plan.total_cost)}</p>
          </div>
        </div>

        <button
          onClick={() => navigate("/shopping-list")}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-8 rounded-xl shadow-lg transform hover:-translate-y-1 transition-all flex items-center"
        >
          <ShoppingCart className="w-5 h-5 mr-2" /> Xem Danh Sách Đi Chợ
        </button>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-gray-500 text-sm font-bold uppercase tracking-wide">Trung bình/ngày</p>
            <p className="text-3xl font-bold text-orange-500">{avgCalories} kcal</p>
          </div>
          <div className="bg-orange-100 p-4 rounded-full"><Flame className="w-8 h-8 text-orange-500" /></div>
        </div>
      </div>

      {/* Hành động: tạo lại + lưu */}
      <div className="max-w-4xl mx-auto flex flex-wrap justify-center gap-3 mb-6">
        <button
          onClick={handleRegenerate}
          disabled={loading}
          className="bg-white border border-emerald-200 text-emerald-700 hover:bg-emerald-50 disabled:opacity-60 font-bold py-2.5 px-6 rounded-xl shadow-sm transition-all flex items-center"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Tạo lại thực đơn khác
        </button>
        <button
          onClick={handleSave}
          disabled={loading || saved}
          className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white font-bold py-2.5 px-6 rounded-xl shadow-sm transition-all flex items-center"
        >
          {saved ? <Check className="w-4 h-4 mr-2" /> : <Save className="w-4 h-4 mr-2" />}
          {saved ? "Đã lưu" : "Lưu thực đơn"}
        </button>
      </div>

      {error && (
        <div className="max-w-4xl mx-auto mb-6 bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-xl flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="max-w-4xl mx-auto mb-8 bg-amber-50 border border-amber-200 text-amber-800 text-sm p-4 rounded-xl">
          <p className="font-bold flex items-center gap-1 mb-1">
            <AlertTriangle className="w-4 h-4" /> Lưu ý dinh dưỡng:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Lưới các ngày */}
      <div className="max-w-4xl mx-auto grid gap-8 md:grid-cols-2">
        {days.map((d) => (
          <div key={d.day} className="bg-white rounded-3xl overflow-hidden shadow-lg border border-gray-100 hover:shadow-2xl transition-shadow duration-300">
            <div className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white p-4 font-bold text-lg text-center shadow-inner">
              Ngày {d.day}
              {d.date ? <span className="font-normal text-white/80 text-sm ml-2">({d.date})</span> : null}
            </div>
            <div className="p-6 space-y-5">
              {d.meals.map((m: PlannedMeal, idx) => {
                const meta = SLOT_META[m.meal_type] ?? {
                  label: m.meal_type,
                  icon: Sun,
                  cls: "bg-gray-50 text-gray-600",
                };
                const Icon = meta.icon;
                return (
                  <div
                    key={`${m.meal_id}-${idx}`}
                    className={`${idx > 0 ? "border-t border-gray-100 pt-4" : ""} group cursor-pointer`}
                    onClick={() => navigate("/food-detail", { state: { mealId: m.meal_id } })}
                  >
                    <span className={`inline-flex items-center ${meta.cls} text-xs font-bold px-3 py-1 rounded-full mb-2`}>
                      <Icon className="w-3.5 h-3.5 mr-1" /> {meta.label}
                    </span>
                    <h3 className="font-bold text-gray-800 text-lg group-hover:text-emerald-600 transition-colors">{m.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {Math.round(m.calories)} kcal • {formatVND(m.cost)}
                    </p>
                  </div>
                );
              })}
              <div className="border-t border-gray-100 pt-3 text-sm text-gray-500 flex justify-between">
                <span>Tổng ngày: {Math.round(d.day_calories)} kcal</span>
                <span>{formatVND(d.day_cost)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
