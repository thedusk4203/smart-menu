import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { ChefHat, Search, Plus, Pencil, EyeOff, Trash2, Flame, Beef, Droplet, Wallet } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealApi } from "../../api/mealApi";
import {
  PageHeader, Button, Badge, Modal, TextField, NumberField, SelectField, Textarea,
  Spinner, EmptyState, Pagination,
} from "../../components/ui";
import { FilterBar } from "../../components/domain/FilterBar";
import { IngredientPicker } from "../../components/domain/IngredientPicker";
import {
  MEAL_TYPE_LABELS, MEAL_TYPE_STYLES, COOKING_METHOD_LABELS,
} from "../../lib/labels";
import { formatVND, formatKcal, formatGram } from "../../lib/format";
import { ApiError } from "../../lib/apiClient";
import type { CookingMethod, MealSummary, MealType } from "../../types";

const LIMIT = 12;
const TYPE_OPTIONS = Object.entries(MEAL_TYPE_LABELS).map(([value, label]) => ({ value, label }));
const METHOD_OPTIONS = Object.entries(COOKING_METHOD_LABELS).map(([value, label]) => ({ value, label }));

interface FormIngredient {
  ingredient_id: number;
  name: string;
  quantity: string;
  unit: string;
}

interface FormState {
  name: string;
  meal_type: MealType;
  cooking_method: CookingMethod | "";
  servings: string;
  description: string;
  instructions: string;
  tags: string;
  ingredients: FormIngredient[];
}

const EMPTY_FORM: FormState = {
  name: "", meal_type: "lunch", cooking_method: "", servings: "1",
  description: "", instructions: "", tags: "", ingredients: [],
};

export function Meals() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const navigate = useNavigate();

  const [items, setItems] = useState<MealSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [mealType, setMealType] = useState<MealType | "">("");
  const [activeOnly, setActiveOnly] = useState(true);
  const [offset, setOffset] = useState(0);

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await mealApi.list({
        search: search.trim() || undefined,
        meal_type: mealType || undefined,
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
  }, [search, mealType, activeOnly, offset]);

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
  }, [load]);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  };

  const openEdit = async (id: number) => {
    try {
      const meal = await mealApi.get(id);
      setEditingId(id);
      setForm({
        name: meal.name,
        meal_type: meal.meal_type,
        cooking_method: meal.cooking_method ?? "",
        servings: String(meal.servings),
        description: meal.description ?? "",
        instructions: meal.instructions ?? "",
        tags: meal.tags.join(", "),
        ingredients: meal.ingredients.map((i) => ({
          ingredient_id: i.ingredient_id,
          name: i.name ?? `#${i.ingredient_id}`,
          quantity: String(i.quantity),
          unit: i.unit,
        })),
      });
      setModalOpen(true);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    }
  };

  const addIngredient = (id: number, name: string, unit: string) => {
    if (form.ingredients.some((i) => i.ingredient_id === id)) return;
    setForm((f) => ({
      ...f,
      ingredients: [...f.ingredients, { ingredient_id: id, name, quantity: "1", unit }],
    }));
  };

  const updateIngredient = (id: number, patch: Partial<FormIngredient>) => {
    setForm((f) => ({
      ...f,
      ingredients: f.ingredients.map((i) => (i.ingredient_id === id ? { ...i, ...patch } : i)),
    }));
  };

  const removeIngredient = (id: number) => {
    setForm((f) => ({ ...f, ingredients: f.ingredients.filter((i) => i.ingredient_id !== id) }));
  };

  const parseTags = (t: string) => t.split(",").map((s) => s.trim()).filter(Boolean);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingId != null) {
        await mealApi.update(editingId, {
          name: form.name,
          meal_type: form.meal_type,
          cooking_method: form.cooking_method || null,
          description: form.description || null,
          instructions: form.instructions || null,
          servings: Number(form.servings),
          tags: parseTags(form.tags),
        });
        toast.success("Đã cập nhật món ăn.");
      } else {
        if (form.ingredients.length === 0) {
          toast.error("Vui lòng thêm ít nhất một nguyên liệu.");
          setSaving(false);
          return;
        }
        await mealApi.create({
          name: form.name,
          meal_type: form.meal_type,
          cooking_method: form.cooking_method || null,
          description: form.description || null,
          instructions: form.instructions || null,
          servings: Number(form.servings),
          tags: parseTags(form.tags),
          ingredients: form.ingredients.map((i) => ({
            ingredient_id: i.ingredient_id,
            quantity: Number(i.quantity) || 0,
            unit: i.unit,
          })),
        });
        toast.success("Đã thêm món ăn.");
      }
      setModalOpen(false);
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setSaving(false);
    }
  };

  const deactivate = async (meal: MealSummary) => {
    if (!window.confirm(`Ẩn món "${meal.name}"?`)) return;
    try {
      await mealApi.remove(meal.id);
      toast.success("Đã ẩn món ăn.");
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    }
  };

  return (
    <div>
      <PageHeader
        title="Món ăn"
        description="Khám phá các món ăn cùng thông tin dinh dưỡng và chi phí."
        actions={
          isAdmin ? (
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" /> Thêm món ăn
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
            placeholder="Tìm theo tên món..."
            className="w-full rounded-xl border border-sand-200 bg-white py-2.5 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          />
        </div>
        <SelectField
          value={mealType}
          onChange={(e) => {
            setMealType(e.target.value as MealType);
            setOffset(0);
          }}
          options={TYPE_OPTIONS}
          placeholder="Tất cả bữa"
          className="sm:w-40"
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

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-7 w-7" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState icon={ChefHat} title="Không có món ăn" description="Thử đổi từ khoá hoặc bộ lọc khác." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((meal) => (
            <div
              key={meal.id}
              onClick={() => navigate(`/meals/${meal.id}`)}
              className="group cursor-pointer rounded-2xl border border-sand-200 bg-white p-4 shadow-sm transition hover:border-brand-200 hover:shadow"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <Badge className={MEAL_TYPE_STYLES[meal.meal_type]}>
                    {MEAL_TYPE_LABELS[meal.meal_type]}
                  </Badge>
                  <h3 className="mt-2 font-semibold text-gray-800 group-hover:text-brand-700">{meal.name}</h3>
                </div>
                {isAdmin && (
                  <div className="flex shrink-0 gap-1" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => openEdit(meal.id)}
                      className="rounded-lg p-1.5 text-gray-400 transition hover:bg-brand-50 hover:text-brand-600"
                      aria-label="Sửa"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deactivate(meal)}
                      className="rounded-lg p-1.5 text-gray-400 transition hover:bg-red-50 hover:text-red-600"
                      aria-label="Ẩn"
                    >
                      <EyeOff className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>

              <div className="mt-3 grid grid-cols-2 gap-y-1.5 text-xs text-gray-500">
                <span className="flex items-center gap-1"><Flame className="h-3.5 w-3.5" /> {formatKcal(meal.total_calories)}</span>
                <span className="flex items-center gap-1"><Beef className="h-3.5 w-3.5" /> {formatGram(meal.total_protein_g)}</span>
                <span className="flex items-center gap-1"><Droplet className="h-3.5 w-3.5" /> {formatGram(meal.total_fat_g)}</span>
                <span className="flex items-center gap-1 font-medium text-brand-600"><Wallet className="h-3.5 w-3.5" /> {formatVND(meal.estimated_cost)}</span>
              </div>

              {meal.tags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {meal.tags.slice(0, 4).map((tag) => (
                    <span key={tag} className="rounded-full bg-sand-100 px-2 py-0.5 text-xs text-gray-600">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}

              {meal.components?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {meal.components.slice(0, 4).map((component) => (
                    <span key={component} className="rounded-md bg-brand-50 px-2 py-0.5 text-xs text-brand-700">
                      {component}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-4">
        <Pagination offset={offset} limit={LIMIT} count={items.length} onChange={setOffset} />
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingId != null ? "Sửa món ăn" : "Thêm món ăn"}
        size="lg"
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Huỷ
            </Button>
            <Button form="meal-form" type="submit" loading={saving}>
              Lưu
            </Button>
          </>
        }
      >
        <form id="meal-form" onSubmit={submit} className="space-y-4">
          <TextField
            label="Tên món"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <div className="grid grid-cols-3 gap-4">
            <SelectField
              label="Loại bữa"
              value={form.meal_type}
              onChange={(e) => setForm({ ...form, meal_type: e.target.value as MealType })}
              options={TYPE_OPTIONS}
            />
            <SelectField
              label="Cách chế biến"
              value={form.cooking_method}
              onChange={(e) => setForm({ ...form, cooking_method: e.target.value as CookingMethod })}
              options={METHOD_OPTIONS}
              placeholder="Không rõ"
            />
            <NumberField
              label="Khẩu phần"
              value={form.servings}
              onChange={(e) => setForm({ ...form, servings: e.target.value })}
              min={1}
            />
          </div>
          <Textarea
            label="Mô tả"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={2}
          />
          <Textarea
            label="Cách làm"
            value={form.instructions}
            onChange={(e) => setForm({ ...form, instructions: e.target.value })}
            rows={3}
          />
          <TextField
            label="Thẻ (cách nhau bằng dấu phẩy)"
            value={form.tags}
            onChange={(e) => setForm({ ...form, tags: e.target.value })}
            placeholder="healthy, gà, ít dầu"
          />

          {editingId == null && (
            <div>
              <p className="mb-2 text-sm font-medium text-gray-700">Nguyên liệu</p>
              <IngredientPicker
                placeholder="Tìm và thêm nguyên liệu..."
                onSelect={(ing) => addIngredient(ing.id, ing.name, ing.default_unit)}
              />
              {form.ingredients.length > 0 && (
                <ul className="mt-3 space-y-2">
                  {form.ingredients.map((ing) => (
                    <li key={ing.ingredient_id} className="flex items-center gap-2 rounded-xl border border-sand-200 p-2">
                      <span className="flex-1 truncate text-sm font-medium text-gray-800">{ing.name}</span>
                      <input
                        type="number"
                        value={ing.quantity}
                        onChange={(e) => updateIngredient(ing.ingredient_id, { quantity: e.target.value })}
                        className="w-20 rounded-lg border border-sand-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                        min={0}
                      />
                      <input
                        value={ing.unit}
                        onChange={(e) => updateIngredient(ing.ingredient_id, { unit: e.target.value })}
                        className="w-16 rounded-lg border border-sand-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
                        placeholder="đơn vị"
                      />
                      <button
                        type="button"
                        onClick={() => removeIngredient(ing.ingredient_id)}
                        className="rounded-lg p-1.5 text-gray-400 transition hover:bg-red-50 hover:text-red-600"
                        aria-label="Xoá"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </form>
      </Modal>
    </div>
  );
}
