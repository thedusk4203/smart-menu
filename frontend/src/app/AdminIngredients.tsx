import { useEffect, useMemo, useState } from "react";
import { Carrot, Plus, Trash2, X, Pencil, Check, Search } from "lucide-react";
import toast from "react-hot-toast";
import { getIngredients, createIngredient, deleteIngredient, updateIngredient } from "../api/ingredientApi";
import type { Ingredient } from "../api/ingredientApi";

const groups = ["meat", "seafood", "vegetable", "fruit", "grain", "dairy", "spice", "other"];
const groupLabel: Record<string, string> = {
  meat: "Thịt", seafood: "Hải sản", vegetable: "Rau củ", fruit: "Trái cây",
  grain: "Ngũ cốc", dairy: "Sữa & trứng", spice: "Gia vị", other: "Khác",
};
const units = ["g", "ml", "quả", "củ", "lá", "gói"];

export default function AdminIngredients() {
  const [items, setItems] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterGroup, setFilterGroup] = useState<string>("all");

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [group, setGroup] = useState("meat");
  const [unit, setUnit] = useState("g");

  const [editId, setEditId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editGroup, setEditGroup] = useState("meat");
  const [editUnit, setEditUnit] = useState("g");

  const load = () => {
    setLoading(true);
    getIngredients({ limit: 200 })
      .then(setItems)
      .catch(() => toast.error("Không tải được"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  // Lọc theo tìm kiếm + nhóm
  const filtered = useMemo(() => {
    return items.filter((i) => {
      if (filterGroup !== "all" && i.food_group !== filterGroup) return false;
      if (search && !i.name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [items, search, filterGroup]);

  const handleCreate = async () => {
    if (!name.trim()) { toast.error("Nhập tên nguyên liệu"); return; }
    try {
      await createIngredient({ name: name.trim(), food_group: group, default_unit: unit });
      toast.success("Đã thêm nguyên liệu");
      setName(""); setShowForm(false); load();
    } catch (e) { toast.error(e instanceof Error ? e.message : "Thêm thất bại"); }
  };

  const startEdit = (ing: Ingredient) => {
    setEditId(ing.id);
    setEditName(ing.name);
    setEditGroup(ing.food_group);
    setEditUnit(ing.default_unit);
  };

  const cancelEdit = () => setEditId(null);

  const saveEdit = async (id: number) => {
    if (!editName.trim()) { toast.error("Tên không được rỗng"); return; }
    try {
      await updateIngredient(id, { name: editName.trim(), food_group: editGroup, default_unit: editUnit });
      setItems((prev) => prev.map((i) => i.id === id
        ? { ...i, name: editName.trim(), food_group: editGroup, default_unit: editUnit } : i));
      setEditId(null);
      toast.success("Đã cập nhật");
    } catch (e) { toast.error(e instanceof Error ? e.message : "Cập nhật thất bại"); }
  };

  const handleDelete = async (id: number, tenNL: string) => {
    if (!confirm(`Xoá nguyên liệu "${tenNL}"?`)) return;
    try {
      await deleteIngredient(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      toast.success("Đã xoá");
    } catch (e) { toast.error(e instanceof Error ? e.message : "Xoá thất bại"); }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-emerald-700 flex items-center gap-2">
            <Carrot className="w-8 h-8" /> Quản Lý Nguyên Liệu
          </h1>
          <button onClick={() => setShowForm(!showForm)}
            className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-4 py-2.5 rounded-xl flex items-center gap-1 cursor-pointer transition-colors">
            {showForm ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
            {showForm ? "Đóng" : "Thêm mới"}
          </button>
        </div>

        {/* Form thêm */}
        {showForm && (
          <div className="bg-white rounded-2xl border border-slate-100 p-5 mb-6 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
              <input type="text" placeholder="Tên nguyên liệu" value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200" />
              <select value={group} onChange={(e) => setGroup(e.target.value)}
                className="bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 cursor-pointer">
                {groups.map((g) => <option key={g} value={g}>{groupLabel[g]}</option>)}
              </select>
              <select value={unit} onChange={(e) => setUnit(e.target.value)}
                className="bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 cursor-pointer">
                {units.map((u) => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
            <button onClick={handleCreate}
              className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-6 py-2.5 rounded-xl cursor-pointer transition-colors">
              Lưu nguyên liệu
            </button>
          </div>
        )}

        {/* Tìm kiếm + lọc */}
        <div className="flex flex-col sm:flex-row gap-3 mb-5">
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input type="text" placeholder="Tìm nguyên liệu..." value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-white border border-slate-200 pl-11 pr-4 py-2.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200" />
          </div>
          <select value={filterGroup} onChange={(e) => setFilterGroup(e.target.value)}
            className="bg-white border border-slate-200 px-4 py-2.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 cursor-pointer">
            <option value="all">Tất cả nhóm</option>
            {groups.map((g) => <option key={g} value={g}>{groupLabel[g]}</option>)}
          </select>
        </div>

        <p className="text-sm text-slate-500 mb-3">Hiển thị {filtered.length} / {items.length} nguyên liệu</p>

        {loading ? (
          <p className="text-center text-emerald-600 font-semibold py-12">Đang tải...</p>
        ) : filtered.length === 0 ? (
          <p className="text-center text-slate-500 py-12">Không có nguyên liệu nào khớp.</p>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-emerald-600 text-white">
                <tr>
                  <th className="p-4">ID</th>
                  <th className="p-4">Tên</th>
                  <th className="p-4">Nhóm</th>
                  <th className="p-4">Đơn vị</th>
                  <th className="p-4 text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((ing) => (
                  <tr key={ing.id} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="p-4 text-slate-600">{ing.id}</td>
                    <td className="p-4 font-medium text-slate-800">
                      {editId === ing.id ? (
                        <input value={editName} onChange={(e) => setEditName(e.target.value)}
                          className="bg-emerald-50 border border-emerald-200 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-300 w-full" autoFocus />
                      ) : ing.name}
                    </td>
                    <td className="p-4 text-slate-600">
                      {editId === ing.id ? (
                        <select value={editGroup} onChange={(e) => setEditGroup(e.target.value)}
                          className="bg-emerald-50 border border-emerald-200 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-300 cursor-pointer">
                          {groups.map((g) => <option key={g} value={g}>{groupLabel[g]}</option>)}
                        </select>
                      ) : (groupLabel[ing.food_group] ?? ing.food_group)}
                    </td>
                    <td className="p-4 text-slate-600">
                      {editId === ing.id ? (
                        <select value={editUnit} onChange={(e) => setEditUnit(e.target.value)}
                          className="bg-emerald-50 border border-emerald-200 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-300 cursor-pointer">
                          {units.map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>
                      ) : ing.default_unit}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center justify-center gap-1">
                        {editId === ing.id ? (
                          <>
                            <button onClick={() => saveEdit(ing.id)}
                              className="text-emerald-600 hover:bg-emerald-50 p-2 rounded-lg cursor-pointer" title="Lưu">
                              <Check className="w-5 h-5" />
                            </button>
                            <button onClick={cancelEdit}
                              className="text-slate-500 hover:bg-slate-100 p-2 rounded-lg cursor-pointer" title="Hủy">
                              <X className="w-5 h-5" />
                            </button>
                          </>
                        ) : (
                          <button onClick={() => startEdit(ing)}
                            className="text-blue-500 hover:bg-blue-50 p-2 rounded-lg cursor-pointer" title="Sửa">
                            <Pencil className="w-5 h-5" />
                          </button>
                        )}
                        <button onClick={() => handleDelete(ing.id, ing.name)}
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