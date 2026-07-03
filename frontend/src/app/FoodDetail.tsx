import { useEffect, useState } from "react";
import { Flame, Utensils, DollarSign, ArrowLeft, Beef } from "lucide-react";
import toast from "react-hot-toast";
import { getMeals, getMealDetail } from "../api/mealApi";
import type { MealSummary, MealDetail } from "../api/mealApi";

// Nhãn tiếng Việt cho loại bữa
const mealTypeLabel: Record<string, string> = {
  breakfast: "Bữa Sáng",
  lunch: "Bữa Trưa",
  dinner: "Bữa Tối",
};

export default function FoodDetail() {
  const [meals, setMeals] = useState<MealSummary[]>([]);
  const [selected, setSelected] = useState<MealDetail | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Tải danh sách món khi vào trang
  useEffect(() => {
    getMeals()
      .then(setMeals)
      .catch(() => toast.error("Không tải được danh sách món ăn"))
      .finally(() => setLoadingList(false));
  }, []);

  // Bấm vào 1 món → tải chi tiết
  const openDetail = async (mealId: number) => {
    setLoadingDetail(true);
    try {
      const detail = await getMealDetail(mealId);
      setSelected(detail);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      toast.error("Không tải được chi tiết món");
    } finally {
      setLoadingDetail(false);
    }
  };

  const money = (n: number) => n.toLocaleString("vi-VN") + "đ";

  // ── MÀN CHI TIẾT ─────────────────────────────────────────────────────
  if (selected) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 md:px-8">
        <div className="max-w-3xl mx-auto">
          <button
            onClick={() => setSelected(null)}
            className="flex items-center gap-2 text-gray-600 hover:text-emerald-600 font-semibold mb-4 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" /> Quay lại danh sách
          </button>

          <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100">
            {/* Tiêu đề */}
            <div className="bg-gradient-to-r from-emerald-500 to-teal-500 p-8 text-white">
              <span className="bg-white/25 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider inline-block mb-3">
                {mealTypeLabel[selected.meal_type] ?? selected.meal_type}
              </span>
              <h1 className="text-3xl md:text-4xl font-bold">{selected.name}</h1>
              {selected.description && (
                <p className="text-white/90 mt-2">{selected.description}</p>
              )}
            </div>

            <div className="p-8">
              {/* Chỉ số dinh dưỡng + chi phí */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-orange-50 rounded-2xl p-4 text-center">
                  <Flame className="w-6 h-6 text-orange-500 mx-auto mb-1" />
                  <p className="text-2xl font-bold text-gray-800">{Math.round(selected.total_calories)}</p>
                  <p className="text-xs text-gray-500">kcal</p>
                </div>
                <div className="bg-red-50 rounded-2xl p-4 text-center">
                  <Beef className="w-6 h-6 text-red-500 mx-auto mb-1" />
                  <p className="text-2xl font-bold text-gray-800">{Math.round(selected.total_protein_g)}g</p>
                  <p className="text-xs text-gray-500">đạm</p>
                </div>
                <div className="bg-emerald-50 rounded-2xl p-4 text-center">
                  <Utensils className="w-6 h-6 text-emerald-500 mx-auto mb-1" />
                  <p className="text-2xl font-bold text-gray-800">{selected.servings}</p>
                  <p className="text-xs text-gray-500">khẩu phần</p>
                </div>
                <div className="bg-teal-50 rounded-2xl p-4 text-center">
                  <DollarSign className="w-6 h-6 text-teal-500 mx-auto mb-1" />
                  <p className="text-xl font-bold text-gray-800">{money(selected.estimated_cost)}</p>
                  <p className="text-xs text-gray-500">chi phí</p>
                </div>
              </div>

              {/* Nguyên liệu */}
              <h3 className="text-xl font-bold text-gray-800 mb-4">🥗 Nguyên liệu</h3>
              <ul className="space-y-3 mb-8">
                {selected.ingredients.map((ing) => (
                  <li key={ing.ingredient_id} className="flex justify-between items-center border-b border-gray-100 pb-2">
                    <span className="text-gray-700">{ing.name ?? `Nguyên liệu #${ing.ingredient_id}`}</span>
                    <span className="font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-lg">
                      {ing.quantity}{ing.unit}
                    </span>
                  </li>
                ))}
              </ul>

              {/* Cách nấu — chỉ hiện nếu có */}
              {selected.instructions && (
                <>
                  <h3 className="text-xl font-bold text-gray-800 mb-4">👨‍🍳 Cách nấu</h3>
                  <p className="text-gray-600 leading-relaxed whitespace-pre-line">{selected.instructions}</p>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── MÀN DANH SÁCH ────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 md:px-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-emerald-700 mb-2">Danh Sách Món Ăn</h1>
        <p className="text-gray-500 mb-8">Bấm vào một món để xem chi tiết dinh dưỡng và cách nấu</p>

        {loadingList ? (
          <p className="text-center text-emerald-600 font-semibold py-12">Đang tải món ăn...</p>
        ) : meals.length === 0 ? (
          <p className="text-center text-gray-500 py-12">Chưa có món ăn nào trong hệ thống.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {meals.map((meal) => (
              <button
                key={meal.id}
                onClick={() => openDetail(meal.id)}
                disabled={loadingDetail}
                className="bg-white rounded-2xl shadow-md hover:shadow-xl border border-gray-100 p-6 text-left transition-all transform hover:-translate-y-1 disabled:opacity-60"
              >
                <span className="bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider inline-block mb-3">
                  {mealTypeLabel[meal.meal_type] ?? meal.meal_type}
                </span>
                <h3 className="text-xl font-bold text-gray-800 mb-3">{meal.name}</h3>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <Flame className="w-4 h-4 text-orange-500" /> {Math.round(meal.total_calories)} kcal
                  </span>
                  <span className="flex items-center gap-1">
                    <DollarSign className="w-4 h-4 text-teal-500" /> {money(meal.estimated_cost)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}