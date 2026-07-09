import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import toast from "react-hot-toast";
import { Salad, Search, Plus, Pencil, EyeOff } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { ingredientApi } from "../../api/ingredientApi";
import {
  PageHeader, Card, Button, Badge, Modal, TextField, NumberField, SelectField,
  Spinner, EmptyState, Pagination,
} from "../../components/ui";
import { FilterBar } from "../../components/domain/FilterBar";
import { FOOD_GROUP_LABELS, FOOD_GROUP_STYLES } from "../../lib/labels";
import { formatVND, formatKcal, formatGram } from "../../lib/format";
import { ApiError } from "../../lib/apiClient";
import type { FoodGroup, Ingredient } from "../../types";

const LIMIT = 20;
const GROUP_OPTIONS = Object.entries(FOOD_GROUP_LABELS).map(([value, label]) => ({ value, label }));

interface FormState {
  name: string;
  food_group: FoodGroup;
  default_unit: string;
  grams_per_unit: string;
  calories: string;
  protein_g: string;
  carbs_g: string;
  fat_g: string;
  fiber_g: string;
}

const EMPTY_FORM: FormState = {
  name: "", food_group: "protein", default_unit: "g", grams_per_unit: "1",
  calories: "", protein_g: "", carbs_g: "", fat_g: "", fiber_g: "",
};

export function Ingredients() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [items, setItems] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [foodGroup, setFoodGroup] = useState<FoodGroup | "">("");
  const [activeOnly, setActiveOnly] = useState(true);
  const [offset, setOffset] = useState(0);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await ingredientApi.list({
        search: search.trim() || undefined,
        food_group: foodGroup || undefined,
        active_only: activeOnly,
        limit: LIMIT,
        offset,
      });
      setItems(list);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setLoading(false);
    }
  }, [search, foodGroup, activeOnly, offset]);

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
  }, [load]);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  };

  const openEdit = (ing: Ingredient) => {
    setEditingId(ing.id);
    setForm({
      name: ing.name,
      food_group: ing.food_group,
      default_unit: ing.default_unit,
      grams_per_unit: String(ing.grams_per_unit),
      calories: ing.calories != null ? String(ing.calories) : "",
      protein_g: ing.protein_g != null ? String(ing.protein_g) : "",
      carbs_g: ing.carbs_g != null ? String(ing.carbs_g) : "",
      fat_g: ing.fat_g != null ? String(ing.fat_g) : "",
      fiber_g: ing.fiber_g != null ? String(ing.fiber_g) : "",
    });
    setModalOpen(true);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingId != null) {
        await ingredientApi.update(editingId, {
          name: form.name,
          food_group: form.food_group,
          default_unit: form.default_unit,
          grams_per_unit: Number(form.grams_per_unit),
        });
        toast.success("Đã cập nhật nguyên liệu.");
      } else {
        await ingredientApi.create({
          name: form.name,
          food_group: form.food_group,
          default_unit: form.default_unit,
          grams_per_unit: Number(form.grams_per_unit),
          nutrition: {
            calories: Number(form.calories) || 0,
            protein_g: Number(form.protein_g) || 0,
            carbs_g: Number(form.carbs_g) || 0,
            fat_g: Number(form.fat_g) || 0,
            fiber_g: Number(form.fiber_g) || 0,
          },
        });
        toast.success("Đã thêm nguyên liệu.");
      }
      setModalOpen(false);
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setSaving(false);
    }
  };

  const deactivate = async (ing: Ingredient) => {
    if (!window.confirm(`Ẩn nguyên liệu "${ing.name}"?`)) return;
    try {
      await ingredientApi.remove(ing.id);
      toast.success("Đã ẩn nguyên liệu.");
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    }
  };

  return (
    <div>
      <PageHeader
        title="Nguyên liệu"
        description="Tra cứu kho nguyên liệu và thông tin dinh dưỡng."
        actions={
          isAdmin ? (
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" /> Thêm nguyên liệu
            </Button>
          ) : undefined
        }
      />

      <FilterBar>
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOffset(0);
            }}
            placeholder="Tìm theo tên..."
            className="w-full rounded-xl border border-sand-200 bg-white py-2.5 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          />
        </div>
        <SelectField
          value={foodGroup}
          onChange={(e) => {
            setFoodGroup(e.target.value as FoodGroup);
            setOffset(0);
          }}
          options={GROUP_OPTIONS}
          placeholder="Tất cả nhóm"
          className="sm:w-44"
        />
        <label className="flex items-center gap-2 px-1 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={activeOnly}
            onChange={(e) => {
              setActiveOnly(e.target.checked);
              setOffset(0);
            }}
            className="h-4 w-4 rounded border-sand-300 text-brand-600 focus:ring-brand-400"
          />
          Chỉ hiển thị đang dùng
        </label>
      </FilterBar>

      <Card bodyClassName="p-0">
        {loading ? (
          <div className="flex justify-center py-16">
            <Spinner className="h-7 w-7" />
          </div>
        ) : items.length === 0 ? (
          <div className="p-5">
            <EmptyState icon={Salad} title="Không có nguyên liệu" description="Thử đổi từ khoá hoặc bộ lọc khác." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-sand-200 text-left text-xs uppercase tracking-wide text-gray-400">
                  <th className="px-5 py-3 font-medium">Tên</th>
                  <th className="px-5 py-3 font-medium">Nhóm</th>
                  <th className="px-5 py-3 text-right font-medium">Calo</th>
                  <th className="px-5 py-3 text-right font-medium">Đạm</th>
                  <th className="px-5 py-3 text-right font-medium">Giá</th>
                  {isAdmin && <th className="px-5 py-3 text-right font-medium">Thao tác</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-sand-100">
                {items.map((ing) => (
                  <tr key={ing.id} className="hover:bg-sand-50">
                    <td className="px-5 py-3">
                      <span className="font-medium text-gray-800">{ing.name}</span>
                      {!ing.is_active && (
                        <Badge className="ml-2 bg-sand-200 text-gray-500">Đã ẩn</Badge>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <Badge className={FOOD_GROUP_STYLES[ing.food_group]}>
                        {FOOD_GROUP_LABELS[ing.food_group]}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-right text-gray-600">{formatKcal(ing.calories)}</td>
                    <td className="px-5 py-3 text-right text-gray-600">{formatGram(ing.protein_g)}</td>
                    <td className="px-5 py-3 text-right text-gray-600">
                      {formatVND(ing.latest_price_per_unit ?? ing.latest_price)}
                    </td>
                    {isAdmin && (
                      <td className="px-5 py-3">
                        <div className="flex justify-end gap-1">
                          <button
                            onClick={() => openEdit(ing)}
                            className="rounded-lg p-1.5 text-gray-400 transition hover:bg-brand-50 hover:text-brand-600"
                            aria-label="Sửa"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => deactivate(ing)}
                            className="rounded-lg p-1.5 text-gray-400 transition hover:bg-red-50 hover:text-red-600"
                            aria-label="Ẩn"
                          >
                            <EyeOff className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <div className="mt-4">
        <Pagination offset={offset} limit={LIMIT} count={items.length} onChange={setOffset} />
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingId != null ? "Sửa nguyên liệu" : "Thêm nguyên liệu"}
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Huỷ
            </Button>
            <Button form="ingredient-form" type="submit" loading={saving}>
              Lưu
            </Button>
          </>
        }
      >
        <form id="ingredient-form" onSubmit={submit} className="space-y-4">
          <TextField
            label="Tên nguyên liệu"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              label="Nhóm thực phẩm"
              value={form.food_group}
              onChange={(e) => setForm({ ...form, food_group: e.target.value as FoodGroup })}
              options={GROUP_OPTIONS}
            />
            <TextField
              label="Đơn vị mặc định"
              required
              value={form.default_unit}
              onChange={(e) => setForm({ ...form, default_unit: e.target.value })}
              placeholder="g, ml, quả..."
            />
            <NumberField
              label="Số gram / đơn vị"
              required
              value={form.grams_per_unit}
              onChange={(e) => setForm({ ...form, grams_per_unit: e.target.value })}
              min={0}
            />
          </div>

          {editingId == null && (
            <div>
              <p className="mb-2 text-sm font-medium text-gray-700">Dinh dưỡng (trên 100g)</p>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                <NumberField
                  label="Calo"
                  value={form.calories}
                  onChange={(e) => setForm({ ...form, calories: e.target.value })}
                  suffix="kcal"
                />
                <NumberField
                  label="Đạm"
                  value={form.protein_g}
                  onChange={(e) => setForm({ ...form, protein_g: e.target.value })}
                  suffix="g"
                />
                <NumberField
                  label="Tinh bột"
                  value={form.carbs_g}
                  onChange={(e) => setForm({ ...form, carbs_g: e.target.value })}
                  suffix="g"
                />
                <NumberField
                  label="Chất béo"
                  value={form.fat_g}
                  onChange={(e) => setForm({ ...form, fat_g: e.target.value })}
                  suffix="g"
                />
                <NumberField
                  label="Chất xơ"
                  value={form.fiber_g}
                  onChange={(e) => setForm({ ...form, fiber_g: e.target.value })}
                  suffix="g"
                />
              </div>
            </div>
          )}
        </form>
      </Modal>
    </div>
  );
}
