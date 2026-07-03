import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Calendar, ChevronRight, Flame, DollarSign, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { getMyMealPlans, deleteMealPlan } from "../api/mealPlanApi";
import type { MealPlan } from "../api/mealPlanApi";

export default function MenuHistory() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);

  // Tải danh sách thực đơn đã lưu
  const loadPlans = () => {
    setLoading(true);
    getMyMealPlans()
      .then(setPlans)
      .catch(() => toast.error("Không tải được lịch sử thực đơn"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadPlans();
  }, []);

  // Xoá 1 thực đơn
  const handleDelete = async (e: React.MouseEvent, planId: number) => {
    e.stopPropagation(); // không cho bấm xoá lan sang mở chi tiết
    if (!confirm("Bạn có chắc muốn xoá thực đơn này?")) return;
    try {
      await deleteMealPlan(planId);
      toast.success("Đã xoá thực đơn");
      setPlans((prev) => prev.filter((p) => p.id !== planId));
    } catch {
      toast.error("Xoá thất bại");
    }
  };

  const money = (n: number) => (n ?? 0).toLocaleString("vi-VN") + "đ";
  const formatDate = (d: string) => {
    try {
      return new Date(d).toLocaleDateString("vi-VN");
    } catch {
      return d;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50 p-4 md:p-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10 mt-4">
          <h2 className="text-3xl font-bold text-emerald-700 mb-2">Lịch Sử Thực Đơn</h2>
          <p className="text-gray-500">Xem lại những thực đơn bạn đã tạo trước đây</p>
        </div>

        {loading ? (
          <p className="text-center text-emerald-600 font-semibold py-12">Đang tải lịch sử...</p>
        ) : plans.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-4">Bạn chưa lưu thực đơn nào.</p>
            <button
              onClick={() => navigate("/create-menu")}
              className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-6 py-2.5 rounded-xl transition-colors"
            >
              Tạo thực đơn đầu tiên
            </button>
          </div>
        ) : (
          <div className="space-y-5">
            {plans.map((plan) => (
              <div
                key={plan.id}
                onClick={() => navigate("/menu-result")}
                className="group bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row justify-between items-center cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
              >
                <div className="mb-4 md:mb-0">
                  <h3 className="font-bold text-xl text-gray-800 flex items-center mb-2">
                    <Calendar className="w-5 h-5 mr-2 text-emerald-500" /> {plan.name}
                  </h3>
                  <div className="flex flex-wrap gap-3 text-sm">
                    <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full font-medium">
                      {formatDate(plan.start_date)}
                      {plan.end_date ? ` - ${formatDate(plan.end_date)}` : ""}
                    </span>
                    <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full font-medium flex items-center">
                      <Flame className="w-3.5 h-3.5 mr-1" /> {Math.round(plan.total_calories)} kcal
                    </span>
                    <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium flex items-center">
                      <DollarSign className="w-3.5 h-3.5 mr-1" /> {money(plan.total_cost)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleDelete(e, plan.id)}
                    className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center hover:bg-red-100 transition-colors"
                    title="Xoá thực đơn"
                  >
                    <Trash2 className="w-5 h-5 text-gray-400 hover:text-red-500" />
                  </button>
                  <div className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-emerald-100 transition-colors">
                    <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-600" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}