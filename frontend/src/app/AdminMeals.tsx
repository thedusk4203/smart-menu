import { useEffect, useMemo, useState } from "react";
import { ChefHat, Plus, Trash2, X, Pencil, Check, Search } from "lucide-react";
import toast from "react-hot-toast";
import { getMeals, createMeal, deleteMeal, updateMeal } from "../api/mealApi";
import type { MealSummary } from "../api/mealApi";

const mealTypes = ["breakfast", "lunch", "dinner"];
const typeLabel: Record<string, string> = {
  breakfast: "Bữa sáng", lunch: "Bữa trưa", dinner: "Bữa tối",
};

export default function AdminMeals() {
  const [items, setItems] = useState<MealSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string>("all");

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [mealType, setMealType] = useState("lunch");
  const [description, setDescription] = useState("");

  const [editId, setEditId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editType, setEditType] = useState("lunch");

  const load = () => {
    setLoading(true);
    getMeals()
      .then(setItems)
      .catch(() => toast.error("Không tải được"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    return items.filter((m) => {
      if (filterType !== "all" && m.meal_type !== filterType) return false;
      if (search && !m.name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [items, search, filterType]);

  const handleCreate = async () => {
    if (!name.trim()) { toast.error("Nhập tên món ăn"); return; }
    try {
      await createMeal({ name: name.trim(), meal_type: mealType, description: description.trim() || undefined, servings: 1 });
      toast.success("Đã thêm món ăn");
      setName(""); setDescription(""); setShowForm(false); load();
    } catch (e) { toast.error(e instanceof Error ? e.message : "Thêm thất bại"); }
  };

  const startEdit = (m: MealSummary) => {
    setEditId(m.id); setEditName(m.name); setEditType(m.meal_type);
  };
  const cancelEdit = () => setEditId(null);

  const saveEdit = async (id: number) => {
    if (!editName.trim()) { toast.error("Tên không được rỗng"); return; }
    try {
      await updateMeal(id, { name: editName.trim(), meal_type: editType });
      setItems((prev) => prev.map((m) => m.id === id
        ? { ...m, name: editName.trim(), meal_type: editType as "breakfast" | "lunch" | "dinner" } : m));
      setEditId(null);
      toast.success("Đã cập nhật");
    } catch (e) { toast.error(e instanceof Error ? e.message : "Cập nhật thất bại"); }
  };

  const handleDelete = async (id: number, tenMon: string) => {
    if (!confirm(`Xoá món "${tenMon}"?`)) return;
    try {
      await deleteMeal(id);
      setItems((prev) => prev.filter((m) => m.id !== id));
      toast.success("Đã xoá");
    } catch (e) { toast.error(e instanceof Error ? e.message : "Xoá thất bại"); }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-emerald-700 flex items-center gap-2">
            <ChefHat className="w-8 h-8" /> Quản Lý Món Ăn
          </h1>
          <button onClick={() => setShowForm(!showForm)}
            className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-4 py-2.5 rounded-xl flex items-center gap-1 cursor-pointer transition-colors">
            {showForm ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
            {showForm ? "Đóng" : "Thêm mới"}
          </button>
        </div>

        {showForm && (
          <div className="bg-white rounded-2xl border border-slate-100 p-5 mb-6 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
              <input type="text" placeholder="Tên món ăn" value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200" />
              <select value={mealType} onChange={(e) => setMealType(e.target.value)}
                className="bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 cursor-pointer">
                {mealTypes.map((t) => <option key={t} value={t}>{typeLabel[t]}</option>)}
              </select>
            </div>
            <input type="text" placeholder="Mô tả (không bắt buộc)" value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 mb-3" />
            <button onClick={handleCreate}
              className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-6 py-2.5 rounded-xl cursor-pointer transition-colors">
              Lưu món ăn
            </button>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3 mb-5">
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input type="text" placeholder="Tìm món ăn..." value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-white border border-slate-200 pl-11 pr-4 py-2.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200" />
          </div>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}
            className="bg-white border border-slate-200 px-4 py-2.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 cursor-pointer">
            <option value="all">Tất cả bữa</option>
            {mealTypes.map((t) => <option key={t} value={t}>{typeLabel[t]}</option>)}
          </select>
        </div>

        <p className="text-sm text-slate-500 mb-3">Hiển thị {filtered.length} / {items.length} món ăn</p>

        {loading ? (
          <p className="text-center text-emerald-600 font-semibold py-12">Đang tải...</p>
        ) : filtered.length === 0 ? (
          <p className="text-center text-slate-500 py-12">Không có món nào khớp.</p>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-emerald-600 text-white">
                <tr>
                  <th className="p-4">ID</th>
                  <th className="p-4">Tên món</th>
                  <th className="p-4">Loại bữa</th>
                  <th className="p-4">Calo</th>
                  <th className="p-4">Chi phí</th>
                  <th className="p-4 text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((m) => (
                  <tr key={m.id} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="p-4 text-slate-600">{m.id}</td>
                    <td className="p-4 font-medium text-slate-800">
                      {editId === m.id ? (
                        <input value={editName} onChange={(e) => setEditName(e.target.value)}
                          className="bg-emerald-50 border border-emerald-200 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-300 w-full" autoFocus />
                      ) : m.name}
                    </td>
                    <td className="p-4 text-slate-600">
                      {editId === m.id ? (
                        <select value={editType} onChange={(e) => setEditType(e.target.value)}
                          className="bg-emerald-50 border border-emerald-200 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-300 cursor-pointer">
                          {mealTypes.map((t) => <option key={t} value={t}>{typeLabel[t]}</option>)}
                        </select>
                      ) : (typeLabel[m.meal_type] ?? m.meal_type)}
                    </td>
                    <td className="p-4 text-slate-600">{Math.round(m.total_calories)} kcal</td>
                    <td className="p-4 text-slate-600">{m.estimated_cost.toLocaleString("vi-VN")}đ</td>
                    <td className="p-4">
                      <div className="flex items-center justify-center gap-1">
                        {editId === m.id ? (
                          <>
                            <button onClick={() => saveEdit(m.id)}
                              className="text-emerald-600 hover:bg-emerald-50 p-2 rounded-lg cursor-pointer" title="Lưu">
                              <Check className="w-5 h-5" />
                            </button>
                            <button onClick={cancelEdit}
                              className="text-slate-500 hover:bg-slate-100 p-2 rounded-lg cursor-pointer" title="Hủy">
                              <X className="w-5 h-5" />
                            </button>
                          </>
                        ) : (
                          <button onClick={() => startEdit(m)}
                            className="text-blue-500 hover:bg-blue-50 p-2 rounded-lg cursor-pointer" title="Sửa">
                            <Pencil className="w-5 h-5" />
                          </button>
                        )}
                        <button onClick={() => handleDelete(m.id, m.name)}
                          className="text-red-500 hover:bg-red-50 p-2 rounded-lg cursor-pointer" title="Xoá">
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}