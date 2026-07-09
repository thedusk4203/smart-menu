import { useEffect, useState } from "react";
import { Search, Flame, DollarSign, Carrot } from "lucide-react";
import toast from "react-hot-toast";
import { getIngredients } from "../api/ingredientApi";
import type { Ingredient } from "../api/ingredientApi";

// Nhãn tiếng Việt cho nhóm thực phẩm
const groupLabel: Record<string, string> = {
  meat: "Thịt", seafood: "Hải sản", vegetable: "Rau củ",
  fruit: "Trái cây", grain: "Ngũ cốc", dairy: "Sữa & trứng",
  spice: "Gia vị", other: "Khác",
};

export default function IngredientList() {
  const [items, setItems] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const load = (searchText?: string) => {
    setLoading(true);
    getIngredients({ search: searchText, limit: 100 })
      .then(setItems)
      .catch(() => toast.error("Không tải được danh sách nguyên liệu"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  // Tìm kiếm khi bấm Enter hoặc nút
  const handleSearch = () => load(search.trim() || undefined);

  const money = (n: number | null) =>
    n != null ? n.toLocaleString("vi-VN") + "đ" : "—";

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 md:px-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-emerald-700 mb-2">Danh Sách Nguyên Liệu</h1>
        <p className="text-gray-500 mb-6">Thông tin dinh dưỡng và giá của các nguyên liệu trong hệ thống</p>

        {/* Ô tìm kiếm */}
        <div className="flex gap-3 mb-8">
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Tìm nguyên liệu (ví dụ: ức gà, gạo...)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full bg-white border border-gray-200 pl-11 pr-4 py-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all"
            />
          </div>
          <button
            onClick={handleSearch}
            className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-6 rounded-xl transition-colors"
          >
            Tìm
          </button>
        </div>

        {loading ? (
          <p className="text-center text-emerald-600 font-semibold py-12">Đang tải nguyên liệu...</p>
        ) : items.length === 0 ? (
          <p className="text-center text-gray-500 py-12">Không tìm thấy nguyên liệu nào.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {items.map((ing) => (
              <div key={ing.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-lg transition-all">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-bold text-gray-800">{ing.name}</h3>
                  <span className="bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full text-xs font-bold flex items-center gap-1 whitespace-nowrap">
                    <Carrot className="w-3 h-3" /> {groupLabel[ing.food_group] ?? ing.food_group}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center gap-1.5 text-gray-600">
                    <Flame className="w-4 h-4 text-orange-500" />
                    {ing.calories != null ? `${Math.round(ing.calories)} kcal` : "—"}
                  </div>
                  <div className="flex items-center gap-1.5 text-gray-600">
                    <DollarSign className="w-4 h-4 text-teal-500" />
                    {money(ing.latest_price)}
                  </div>
                  <div className="text-gray-500">Đạm: {ing.protein_g != null ? `${ing.protein_g}g` : "—"}</div>
                  <div className="text-gray-500">Đơn vị: {ing.default_unit}</div>
                </div>
                <p className="text-xs text-gray-400 mt-2">* Dinh dưỡng tính trên 100g</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}