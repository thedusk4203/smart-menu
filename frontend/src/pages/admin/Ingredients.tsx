import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Eye, EyeOff, Pencil, Plus, Search, Salad, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { useSearchParams } from "react-router-dom";
import { adminApi } from "../../api/adminApi";
import { ApiError } from "../../lib/apiClient";
import { FOOD_GROUP_LABELS, FOOD_GROUP_STYLES } from "../../lib/labels";
import { formatDate, formatVND } from "../../lib/format";
import { Badge, Button, Card, ConfirmDialog, Modal, MoneyField, NumberField, PageHeader, SelectField, TextField } from "../../components/ui";
import { AdminEmptyState, AdminErrorState, AdminTableSkeleton } from "../../components/admin/AdminStates";
import { AdminExportDialog } from "../../components/admin/AdminExportDialog";
import { AdminPagination } from "../../components/admin/AdminPagination";
import { DataStateBadge } from "../../components/admin/QualityBadges";
import type { AdminIngredient, AdminIngredientWrite, IngredientPurchaseMode } from "../../types/admin";
import type { FoodGroup } from "../../types";

const LIMIT = 20;
const GROUP_OPTIONS = Object.entries(FOOD_GROUP_LABELS).map(([value, label]) => ({ value, label }));

type IngredientForm = {
  name: string; food_group: FoodGroup; default_unit: string; grams_per_unit: string; is_active: boolean;
  calories: string; protein_g: string; carbs_g: string; fat_g: string; fiber_g: string;
  price: string; price_unit: string; price_per_default_unit: string; price_source: string;
  purchase_mode: IngredientPurchaseMode; purchase_increment: string;
  room_shelf_life_days: string; fridge_shelf_life_days: string; freezer_shelf_life_days: string;
  shelf_life_source: string; shelf_life_reviewed_at: string;
};

const EMPTY_FORM: IngredientForm = {
  name: "", food_group: "protein", default_unit: "g", grams_per_unit: "1", is_active: true,
  calories: "", protein_g: "", carbs_g: "", fat_g: "", fiber_g: "",
  price: "", price_unit: "kg", price_per_default_unit: "", price_source: "",
  purchase_mode: "regular", purchase_increment: "", room_shelf_life_days: "",
  fridge_shelf_life_days: "", freezer_shelf_life_days: "",
  shelf_life_source: "", shelf_life_reviewed_at: "",
};

function toForm(item: AdminIngredient): IngredientForm {
  return {
    name: item.name, food_group: item.food_group, default_unit: item.default_unit,
    grams_per_unit: String(item.grams_per_unit), is_active: item.is_active,
    calories: item.calories == null ? "" : String(item.calories),
    protein_g: item.protein_g == null ? "" : String(item.protein_g),
    carbs_g: item.carbs_g == null ? "" : String(item.carbs_g),
    fat_g: item.fat_g == null ? "" : String(item.fat_g),
    fiber_g: item.fiber_g == null ? "" : String(item.fiber_g),
    price: item.latest_price == null ? "" : String(item.latest_price),
    price_unit: item.price_unit || "kg",
    price_per_default_unit: item.latest_price_per_unit == null ? "" : String(item.latest_price_per_unit),
    price_source: item.price_source || "",
    purchase_mode: item.purchase_mode,
    purchase_increment: item.purchase_increment == null ? "" : String(item.purchase_increment),
    room_shelf_life_days: item.room_shelf_life_days == null ? "" : String(item.room_shelf_life_days),
    fridge_shelf_life_days: item.fridge_shelf_life_days == null ? "" : String(item.fridge_shelf_life_days),
    freezer_shelf_life_days: item.freezer_shelf_life_days == null ? "" : String(item.freezer_shelf_life_days),
    shelf_life_source: item.shelf_life_source || "",
    shelf_life_reviewed_at: item.shelf_life_reviewed_at || "",
  };
}

function toPayload(form: IngredientForm): AdminIngredientWrite {
  const nutritionValues = [form.calories, form.protein_g, form.carbs_g, form.fat_g, form.fiber_g];
  const hasNutrition = nutritionValues.some((value) => value.trim() !== "");
  const hasPrice = form.price.trim() !== "" || form.price_per_default_unit.trim() !== "";
  return {
    name: form.name.trim(), food_group: form.food_group, default_unit: form.default_unit.trim(),
    grams_per_unit: Number(form.grams_per_unit), is_active: form.is_active,
    purchase_mode: form.purchase_mode,
    purchase_increment: form.purchase_mode === "regular" && form.purchase_increment ? Number(form.purchase_increment) : null,
    room_shelf_life_days: form.purchase_mode === "regular" && form.room_shelf_life_days !== "" ? Number(form.room_shelf_life_days) : null,
    fridge_shelf_life_days: form.purchase_mode === "regular" && form.fridge_shelf_life_days !== "" ? Number(form.fridge_shelf_life_days) : null,
    freezer_shelf_life_days: form.purchase_mode === "regular" && form.freezer_shelf_life_days !== "" ? Number(form.freezer_shelf_life_days) : null,
    shelf_life_source: form.purchase_mode === "regular" ? form.shelf_life_source.trim() || null : null,
    shelf_life_reviewed_at: form.purchase_mode === "regular" ? form.shelf_life_reviewed_at || null : null,
    nutrition: hasNutrition ? {
      calories: Number(form.calories || 0), protein_g: Number(form.protein_g || 0),
      carbs_g: Number(form.carbs_g || 0), fat_g: Number(form.fat_g || 0), fiber_g: Number(form.fiber_g || 0),
    } : null,
    price: hasPrice ? {
      price: Number(form.price), unit: form.price_unit.trim(),
      price_per_default_unit: Number(form.price_per_default_unit), source: form.price_source.trim() || null,
    } : null,
  };
}

export function AdminIngredients() {
  const [params, setParams] = useSearchParams();
  const editId = params.get("edit");
  const [items, setItems] = useState<AdminIngredient[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState("");
  const [status, setStatus] = useState("");
  const [quality, setQuality] = useState(params.get("quality") || "");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<AdminIngredient | null>(null);
  const [form, setForm] = useState<IngredientForm>(EMPTY_FORM);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<AdminIngredient | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const page = await adminApi.ingredients({ search: search.trim() || undefined, food_group: group, status, quality, limit: LIMIT, offset });
      setItems(page.items); setTotal(page.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải nguyên liệu.");
    } finally { setLoading(false); }
  }, [group, offset, quality, search, status]);

  useEffect(() => { const timer = window.setTimeout(load, 250); return () => window.clearTimeout(timer); }, [load]);

  useEffect(() => {
    if (!editId) return;
    const id = Number(editId);
    const clearEditParam = () => setParams((current) => {
      const next = new URLSearchParams(current);
      next.delete("edit");
      return next;
    }, { replace: true });
    if (!Number.isInteger(id) || id < 1) {
      clearEditParam();
      return;
    }
    let active = true;
    adminApi.ingredient(id)
      .then((detail) => {
        if (!active) return;
        setEditing(detail);
        setForm(toForm(detail));
        setOpen(true);
      })
      .catch((err) => {
        if (active) toast.error(err instanceof ApiError ? err.message : "Không thể tải nguyên liệu.");
      })
      .finally(() => {
        if (active) clearEditParam();
      });
    return () => { active = false; };
  }, [editId, setParams]);

  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setOpen(true); };
  const openEdit = async (item: AdminIngredient) => {
    try { const detail = await adminApi.ingredient(item.id); setEditing(detail); setForm(toForm(detail)); setOpen(true); }
    catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể tải nguyên liệu."); }
  };
  const save = async (event: FormEvent) => {
    event.preventDefault(); setSaving(true);
    try {
      const payload = toPayload(form);
      const result = editing ? await adminApi.updateIngredient(editing.id, payload) : await adminApi.createIngredient(payload);
      setItems((current) => editing ? current.map((item) => item.id === result.id ? result : item) : [result, ...current]);
      if (!editing) setTotal((value) => value + 1);
      setOpen(false); toast.success(editing ? "Đã cập nhật nguyên liệu." : "Đã thêm nguyên liệu.");
    } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể lưu nguyên liệu."); }
    finally { setSaving(false); }
  };
  const toggle = async (item: AdminIngredient) => {
    setSavingId(item.id);
    try {
      const updated = await adminApi.setIngredientActive(item.id, !item.is_active);
      setItems((current) => current.map((value) => value.id === item.id ? updated : value));
      toast.success(updated.is_active ? "Đã khôi phục nguyên liệu." : "Đã ẩn nguyên liệu khỏi dữ liệu mới.");
    } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể đổi trạng thái."); }
    finally { setSavingId(null); }
  };
  const deleteIngredient = async () => {
    if (!deleting) return;
    setDeletingId(deleting.id);
    try {
      await adminApi.deleteIngredient(deleting.id);
      setItems((current) => current.filter((item) => item.id !== deleting.id));
      setTotal((value) => Math.max(0, value - 1));
      setOpen(false); setEditing(null); setDeleting(null);
      toast.success("Đã xóa nguyên liệu.");
    } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể xóa nguyên liệu."); }
    finally { setDeletingId(null); }
  };
  const setQualityFilter = (value: string) => { setQuality(value); setOffset(0); setParams(value ? { quality: value } : {}); };

  return (
    <div>
      <PageHeader title="Nguyên liệu" description="Quản lý đơn vị, dinh dưỡng, giá và dữ liệu đầu vào cho mọi công thức." actions={<div className="flex flex-wrap gap-2"><AdminExportDialog entityType="ingredients" filteredParams={{ search: search.trim() || undefined, food_group: group, status, quality }} filteredTotal={total} /><Button onClick={openCreate}><Plus className="h-4 w-4" /> Thêm nguyên liệu</Button></div>} />
      <div className="mb-4 grid gap-3 rounded-2xl border border-sand-200 bg-white p-3 shadow-sm lg:grid-cols-[minmax(0,1fr)_10rem_10rem_13rem]">
        <label className="relative block"><span className="sr-only">Tìm nguyên liệu</span><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" /><input value={search} onChange={(e) => { setSearch(e.target.value); setOffset(0); }} placeholder="Tìm tên nguyên liệu" className="min-h-11 w-full rounded-xl border border-sand-200 px-3 pl-9 text-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-400" /></label>
        <SelectField value={group} onChange={(e) => { setGroup(e.target.value); setOffset(0); }} placeholder="Tất cả nhóm" options={GROUP_OPTIONS} />
        <SelectField value={status} onChange={(e) => { setStatus(e.target.value); setOffset(0); }} placeholder="Tất cả trạng thái" options={[{ value: "active", label: "Đang dùng" }, { value: "inactive", label: "Đã ẩn" }]} />
        <SelectField value={quality} onChange={(e) => setQualityFilter(e.target.value)} placeholder="Tất cả chất lượng" options={[{ value: "missing_price", label: "Thiếu giá" }, { value: "missing_purchase_rule", label: "Thiếu quy cách mua" }, { value: "missing_storage_rule", label: "Thiếu bảo quản" }, { value: "missing_nutrition", label: "Thiếu dinh dưỡng" }, { value: "missing_conversion", label: "Cần quy đổi" }]} />
      </div>
      <Card bodyClassName="p-0">
        {loading ? <AdminTableSkeleton /> : error ? <AdminErrorState message={error} onRetry={load} /> : items.length === 0 ? <AdminEmptyState icon={Salad} title="Không có nguyên liệu phù hợp" description="Thử đổi bộ lọc hoặc thêm nguyên liệu mới." action={<Button size="sm" onClick={openCreate}><Plus className="h-4 w-4" /> Thêm nguyên liệu</Button>} /> : (
          <div className="overflow-x-auto"><table className="min-w-[900px] w-full text-left text-sm"><thead className="bg-sand-50 text-xs text-gray-600"><tr className="border-b border-sand-200"><th className="px-5 py-3 font-semibold">Nguyên liệu</th><th className="px-5 py-3 font-semibold">Dữ liệu</th><th className="px-5 py-3 font-semibold">Giá mới nhất</th><th className="px-5 py-3 font-semibold">Cập nhật</th><th className="px-5 py-3 text-right font-semibold">Thao tác</th></tr></thead><tbody className="divide-y divide-sand-100">
            {items.map((item) => <tr key={item.id} className="hover:bg-sand-50"><td className="px-5 py-3.5"><div className="flex items-center gap-2"><p className="font-semibold text-gray-900">{item.name}</p>{!item.is_active && <Badge className="bg-sand-200 text-gray-700">Đã ẩn</Badge>}</div><Badge className={`mt-1 ${FOOD_GROUP_STYLES[item.food_group]}`}>{FOOD_GROUP_LABELS[item.food_group]}</Badge></td><td className="px-5 py-3.5"><div className="flex flex-wrap gap-1.5">{item.missing_nutrition ? <DataStateBadge state="error" label="Thiếu dinh dưỡng" /> : <DataStateBadge state="ok" label="Dinh dưỡng" />}{item.missing_purchase_rule && <DataStateBadge state="error" label="Thiếu bước mua" />}{item.missing_storage_rule && <DataStateBadge state="warning" label="Chỉ dùng cùng ngày" />}{item.missing_conversion && <DataStateBadge state="warning" label="Kiểm tra quy đổi" />}{item.purchase_mode === "pantry" && <DataStateBadge state="ok" label="Pantry" />}{item.purchase_mode === "ignored" && <DataStateBadge state="ok" label="Bỏ qua mua" />}</div></td><td className="px-5 py-3.5">{item.missing_price ? <><p className="font-semibold text-gray-900">—</p><p className="mt-0.5 text-xs text-gray-600">Thiếu giá chuẩn hóa</p></> : <><p className="font-semibold tabular-nums text-gray-900">{formatVND(item.latest_price)} <span className="font-normal text-gray-600">/ {item.price_unit || item.default_unit}</span></p><p className="mt-0.5 text-xs text-gray-600">{item.price_source || "Không rõ nguồn"}</p><p className="mt-0.5 text-xs text-gray-500">Quy đổi để tính món: {formatVND(item.latest_price_per_unit)} / {item.default_unit}</p>{item.purchase_block_cost != null && <p className="mt-0.5 text-xs font-medium text-brand-700">Mỗi block: {formatVND(item.purchase_block_cost)}</p>}</>}</td><td className="px-5 py-3.5 text-gray-600">{formatDate(item.updated_at)}</td><td className="px-5 py-3.5"><div className="flex justify-end gap-1"><button type="button" onClick={() => openEdit(item)} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-gray-600 transition hover:bg-brand-50 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400" aria-label={`Sửa ${item.name}`}><Pencil className="h-4 w-4" /></button><button type="button" disabled={savingId === item.id} onClick={() => toggle(item)} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-gray-600 transition hover:bg-sand-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:opacity-50" aria-label={item.is_active ? `Ẩn ${item.name}` : `Khôi phục ${item.name}`}>{item.is_active ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></div></td></tr>)}
          </tbody></table></div>
        )}
        {!loading && !error && <AdminPagination offset={offset} limit={LIMIT} total={total} onChange={setOffset} />}
      </Card>
      <Modal open={open} onClose={() => setOpen(false)} title={editing ? `Sửa ${editing.name}` : "Thêm nguyên liệu"} size="lg" footer={<>{editing && <Button type="button" variant="danger" onClick={() => setDeleting(editing)}><Trash2 className="h-4 w-4" /> Xóa nguyên liệu</Button>}<Button variant="ghost" onClick={() => setOpen(false)}>Hủy</Button><Button form="admin-ingredient-form" type="submit" loading={saving}>Lưu nguyên liệu</Button></>}>
        <form id="admin-ingredient-form" onSubmit={save} className="space-y-6">
          <section><h3 className="font-semibold text-gray-900">Thông tin cơ bản</h3><div className="mt-3 grid gap-4 sm:grid-cols-2"><TextField className="sm:col-span-2" label="Tên nguyên liệu" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /><SelectField label="Nhóm thực phẩm" value={form.food_group} options={GROUP_OPTIONS} onChange={(e) => setForm({ ...form, food_group: e.target.value as FoodGroup })} /><TextField label="Đơn vị mặc định" required value={form.default_unit} hint="Ví dụ: g, ml, quả" onChange={(e) => setForm({ ...form, default_unit: e.target.value })} /><NumberField label="Gram / đơn vị" required min="0.0001" step="0.01" value={form.grams_per_unit} hint="Dùng để quy đổi dinh dưỡng về gram." onChange={(e) => setForm({ ...form, grams_per_unit: e.target.value })} /></div></section>
          <section className="border-t border-sand-200 pt-5"><h3 className="font-semibold text-gray-900">Dinh dưỡng trên 100g</h3><p className="mt-1 text-sm text-gray-600">Để trống khi chưa có nguồn đáng tin cậy; trang Quality sẽ nhắc bổ sung.</p><div className="mt-3 grid gap-4 sm:grid-cols-3"><NumberField label="Calo" suffix="kcal" min="0" value={form.calories} onChange={(e) => setForm({ ...form, calories: e.target.value })} /><NumberField label="Đạm" suffix="g" min="0" value={form.protein_g} onChange={(e) => setForm({ ...form, protein_g: e.target.value })} /><NumberField label="Tinh bột" suffix="g" min="0" value={form.carbs_g} onChange={(e) => setForm({ ...form, carbs_g: e.target.value })} /><NumberField label="Chất béo" suffix="g" min="0" value={form.fat_g} onChange={(e) => setForm({ ...form, fat_g: e.target.value })} /><NumberField label="Chất xơ" suffix="g" min="0" value={form.fiber_g} onChange={(e) => setForm({ ...form, fiber_g: e.target.value })} /></div></section>
          <section className="border-t border-sand-200 pt-5"><h3 className="font-semibold text-gray-900">Thêm mốc giá</h3><p className="mt-1 text-sm text-gray-600">Lưu một mốc mới, không ghi đè lịch sử giá trước đó.</p><div className="mt-3 grid gap-4 sm:grid-cols-2"><MoneyField label="Giá gốc" min="0" value={form.price} onValueChange={(price) => setForm({ ...form, price })} /><TextField label="Đơn vị giá" value={form.price_unit} onChange={(e) => setForm({ ...form, price_unit: e.target.value })} /><MoneyField label={`Giá quy đổi / ${form.default_unit || "đơn vị"}`} min="0" value={form.price_per_default_unit} maxFractionDigits={4} hint="Dùng để tính chi phí món; không phải giá niêm yết." onValueChange={(price_per_default_unit) => setForm({ ...form, price_per_default_unit })} /><TextField label="Nguồn giá" value={form.price_source} placeholder="Chợ, siêu thị, khảo sát..." onChange={(e) => setForm({ ...form, price_source: e.target.value })} /></div></section>
          <section className="border-t border-sand-200 pt-5">
            <h3 className="font-semibold text-gray-900">Mua và bảo quản</h3>
            <p className="mt-1 text-sm text-gray-600">Quy tắc này quyết định số tiền thật phải mua và thời gian planner được tận dụng phần dư.</p>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <SelectField
                label="Chế độ mua"
                value={form.purchase_mode}
                options={[
                  { value: "regular", label: "Mua theo block" },
                  { value: "pantry", label: "Pantry — giả định có sẵn" },
                  { value: "ignored", label: "Không mua / không hiển thị" },
                ]}
                onChange={(e) => setForm({ ...form, purchase_mode: e.target.value as IngredientPurchaseMode })}
              />
              {form.purchase_mode === "regular" && <NumberField label={`Bước mua (${form.default_unit || "đơn vị"})`} min="0.01" step="0.01" value={form.purchase_increment} onChange={(e) => setForm({ ...form, purchase_increment: e.target.value })} />}
            </div>
            {form.purchase_mode === "regular" && <>
              {form.purchase_increment && form.price_per_default_unit && <p className="mt-3 rounded-xl bg-brand-50 px-3 py-2 text-sm text-brand-800">Giá mỗi block: {formatVND(Number(form.purchase_increment) * Number(form.price_per_default_unit))}</p>}
              <div className="mt-3 grid gap-4 sm:grid-cols-3">
                <NumberField label="Nhiệt độ phòng" suffix="ngày" min="0" step="1" value={form.room_shelf_life_days} onChange={(e) => setForm({ ...form, room_shelf_life_days: e.target.value })} />
                <NumberField label="Ngăn mát" suffix="ngày" min="0" step="1" value={form.fridge_shelf_life_days} onChange={(e) => setForm({ ...form, fridge_shelf_life_days: e.target.value })} />
                <NumberField label="Ngăn đông" suffix="ngày" min="0" step="1" value={form.freezer_shelf_life_days} onChange={(e) => setForm({ ...form, freezer_shelf_life_days: e.target.value })} />
              </div>
              <div className="mt-3 grid gap-4 sm:grid-cols-2">
                <TextField label="Nguồn hạn bảo quản" value={form.shelf_life_source} onChange={(e) => setForm({ ...form, shelf_life_source: e.target.value })} />
                <TextField type="date" label="Ngày xác minh" value={form.shelf_life_reviewed_at} onChange={(e) => setForm({ ...form, shelf_life_reviewed_at: e.target.value })} />
              </div>
            </>}
          </section>
        </form>
      </Modal>
      <ConfirmDialog open={!!deleting} onClose={() => setDeleting(null)} onConfirm={deleteIngredient} loading={deletingId === deleting?.id} title="Xóa nguyên liệu" message={deleting ? `Xóa vĩnh viễn “${deleting.name}”? Không thể hoàn tác.` : ""} confirmLabel="Xóa nguyên liệu" />
    </div>
  );
}
