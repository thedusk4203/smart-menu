import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Download, Eye, EyeOff, Pencil, Plus, Search, Trash2, UtensilsCrossed } from "lucide-react";
import toast from "react-hot-toast";
import { useSearchParams } from "react-router-dom";
import { adminApi } from "../../api/adminApi";
import { IngredientPicker } from "../../components/domain/IngredientPicker";
import { AdminEmptyState, AdminErrorState, AdminTableSkeleton } from "../../components/admin/AdminStates";
import { AdminExportDialog } from "../../components/admin/AdminExportDialog";
import { AdminPagination } from "../../components/admin/AdminPagination";
import { DataStateBadge } from "../../components/admin/QualityBadges";
import { Badge, Button, Card, ConfirmDialog, Modal, PageHeader, SelectField, Textarea, TextField } from "../../components/ui";
import { ApiError } from "../../lib/apiClient";
import { COOKING_METHOD_LABELS, DISH_TYPE_LABELS } from "../../lib/labels";
import { formatDate, formatKcal, formatVND } from "../../lib/format";
import type { AdminDish } from "../../types/admin";
import type { CookingMethod, DishType } from "../../types";
import { IngredientEditorRow } from "./DishIngredientEditorRow";
import { EMPTY_FORM, dishToForm as toForm, dishToPayload as toPayload } from "./dishForm";
import type { DishForm, FormIngredient } from "./dishForm";

const LIMIT = 20;
const DISH_TYPE_OPTIONS = Object.entries(DISH_TYPE_LABELS).map(([value, label]) => ({ value, label }));
const METHOD_OPTIONS = Object.entries(COOKING_METHOD_LABELS).map(([value, label]) => ({ value, label }));


export function AdminDishes() {
  const [params, setParams] = useSearchParams();
  const editId = params.get("edit");
  const [items, setItems] = useState<AdminDish[]>([]); const [total, setTotal] = useState(0);
  const [search, setSearch] = useState(""); const [dishType, setDishType] = useState(""); const [status, setStatus] = useState(""); const [quality, setQuality] = useState(""); const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const [editing, setEditing] = useState<AdminDish | null>(null); const [form, setForm] = useState<DishForm>(EMPTY_FORM); const [open, setOpen] = useState(false); const [saving, setSaving] = useState(false); const [savingId, setSavingId] = useState<number | null>(null); const [deleting, setDeleting] = useState<AdminDish | null>(null); const [deletingId, setDeletingId] = useState<number | null>(null);
  const [downloadingSuggestions, setDownloadingSuggestions] = useState(false);
  const load = useCallback(async () => { setLoading(true); setError(""); try { const page = await adminApi.dishes({ search: search.trim() || undefined, dish_type: dishType, status, quality, limit: LIMIT, offset }); setItems(page.items); setTotal(page.total); } catch (err) { setError(err instanceof ApiError ? err.message : "Không thể tải món thành phần."); } finally { setLoading(false); } }, [dishType, offset, quality, search, status]);
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
    adminApi.dish(id)
      .then((detail) => {
        if (!active) return;
        setEditing(detail);
        setForm(toForm(detail));
        setOpen(true);
      })
      .catch((err) => {
        if (active) toast.error(err instanceof ApiError ? err.message : "Không thể tải công thức.");
      })
      .finally(() => {
        if (active) clearEditParam();
      });
    return () => { active = false; };
  }, [editId, setParams]);
  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setOpen(true); };
  const openEdit = async (item: AdminDish) => { try { const detail = await adminApi.dish(item.id); setEditing(detail); setForm(toForm(detail)); setOpen(true); } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể tải công thức."); } };
  const addIngredient = (id: number, name: string, unit: string) => { if (form.ingredients.some((item) => item.ingredient_id === id)) return; setForm((current) => ({ ...current, ingredients: [...current.ingredients, { ingredient_id: id, name, quantity: "1", unit, max_extra_quantity: "0", extra_step_quantity: "" }] })); };
  const updateIngredient = (id: number, patch: Partial<FormIngredient>) => setForm((current) => ({ ...current, ingredients: current.ingredients.map((item) => item.ingredient_id === id ? { ...item, ...patch } : item) }));
  const removeIngredient = (id: number) => setForm((current) => ({ ...current, ingredients: current.ingredients.filter((item) => item.ingredient_id !== id) }));
  const save = async (event: FormEvent) => { event.preventDefault(); setSaving(true); try { const payload = toPayload(form); const result = editing ? await adminApi.updateDish(editing.id, payload) : await adminApi.createDish(payload); setItems((current) => editing ? current.map((item) => item.id === result.id ? result : item) : [result, ...current]); if (!editing) setTotal((value) => value + 1); setOpen(false); toast.success(editing ? "Đã cập nhật công thức." : "Đã tạo món thành phần."); } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể lưu món."); } finally { setSaving(false); } };
  const toggle = async (item: AdminDish) => { setSavingId(item.id); try { const result = await adminApi.setDishActive(item.id, !item.is_active); setItems((current) => current.map((value) => value.id === item.id ? result : value)); toast.success(result.is_active ? "Đã kích hoạt món." : "Đã ẩn món khỏi planner."); } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể đổi trạng thái."); } finally { setSavingId(null); } };
  const deleteDish = async () => { if (!deleting) return; setDeletingId(deleting.id); try { await adminApi.deleteDish(deleting.id); setItems((current) => current.filter((item) => item.id !== deleting.id)); setTotal((value) => Math.max(0, value - 1)); setOpen(false); setEditing(null); setDeleting(null); toast.success("Đã xóa món thành phần."); } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể xóa món thành phần."); } finally { setDeletingId(null); } };
  const downloadFlexSuggestions = async () => {
    setDownloadingSuggestions(true);
    try {
      const result = await adminApi.exportDishFlexSuggestions("xlsx");
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.filename || "smart-menu-dish-flex-suggestions.xlsx";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast.success("Đã tải file gợi ý. Hãy review trước khi import lại.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể tạo file gợi ý.");
    } finally {
      setDownloadingSuggestions(false);
    }
  };

  return <div>
    <PageHeader title="Món thành phần" description="Công thức chuẩn mà planner dùng để ghép thành bữa/mâm món." actions={<div className="flex flex-wrap gap-2"><Button variant="secondary" loading={downloadingSuggestions} onClick={() => void downloadFlexSuggestions()}><Download className="h-4 w-4" /> Gợi ý tận dụng phần dư</Button><AdminExportDialog entityType="dishes" filteredParams={{ search: search.trim() || undefined, dish_type: dishType, status, quality }} filteredTotal={total} /><Button onClick={openCreate}><Plus className="h-4 w-4" /> Thêm món</Button></div>} />
    <div className="mb-4 grid gap-3 rounded-2xl border border-sand-200 bg-white p-3 shadow-sm lg:grid-cols-[minmax(0,1fr)_10rem_10rem_13rem]"><label className="relative block"><span className="sr-only">Tìm món</span><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" /><input value={search} onChange={(e) => { setSearch(e.target.value); setOffset(0); }} placeholder="Tìm món thành phần" className="min-h-11 w-full rounded-xl border border-sand-200 px-3 pl-9 text-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-400" /></label><SelectField value={dishType} onChange={(e) => { setDishType(e.target.value); setOffset(0); }} placeholder="Tất cả loại" options={DISH_TYPE_OPTIONS} /><SelectField value={status} onChange={(e) => { setStatus(e.target.value); setOffset(0); }} placeholder="Tất cả trạng thái" options={[{ value: "active", label: "Đang dùng" }, { value: "inactive", label: "Đã ẩn" }]} /><SelectField value={quality} onChange={(e) => { setQuality(e.target.value); setOffset(0); }} placeholder="Tất cả chất lượng" options={[{ value: "missing_recipe", label: "Thiếu công thức" }, { value: "missing_price", label: "Thiếu giá" }, { value: "missing_nutrition", label: "Thiếu dinh dưỡng" }]} /></div>
    <Card bodyClassName="p-0">{loading ? <AdminTableSkeleton /> : error ? <AdminErrorState message={error} onRetry={load} /> : items.length === 0 ? <AdminEmptyState icon={UtensilsCrossed} title="Không tìm thấy món thành phần" description="Thêm món đầu tiên hoặc đổi bộ lọc để tiếp tục." action={<Button size="sm" onClick={openCreate}><Plus className="h-4 w-4" /> Thêm món</Button>} /> : <div className="overflow-x-auto"><table className="min-w-[920px] w-full text-left text-sm"><thead className="bg-sand-50 text-xs text-gray-600"><tr className="border-b border-sand-200"><th className="px-5 py-3 font-semibold">Món</th><th className="px-5 py-3 font-semibold">Đầy đủ dữ liệu</th><th className="px-5 py-3 font-semibold">Dinh dưỡng & chi phí</th><th className="px-5 py-3 font-semibold">Cập nhật</th><th className="px-5 py-3 text-right font-semibold">Thao tác</th></tr></thead><tbody className="divide-y divide-sand-100">{items.map((item) => <tr key={item.id} className="hover:bg-sand-50"><td className="px-5 py-3.5"><div className="flex items-center gap-2"><p className="font-semibold text-gray-900">{item.name}</p>{!item.is_active && <Badge className="bg-sand-200 text-gray-700">Đã ẩn</Badge>}</div><p className="mt-1 text-xs text-gray-600">{DISH_TYPE_LABELS[item.dish_type]}{item.cooking_method ? ` · ${COOKING_METHOD_LABELS[item.cooking_method]}` : ""} · {item.ingredient_count} nguyên liệu</p></td><td className="px-5 py-3.5"><div className="flex flex-wrap gap-1.5">{item.missing_recipe ? <DataStateBadge state="error" label="Thiếu công thức" /> : <DataStateBadge state="ok" label="Công thức" />}{item.missing_price && <DataStateBadge state="error" label="Thiếu giá" />}{item.missing_nutrition && <DataStateBadge state="error" label="Thiếu dinh dưỡng" />}</div></td><td className="px-5 py-3.5"><p className="font-semibold tabular-nums text-gray-900">{formatKcal(item.total_calories)} · {formatVND(item.estimated_cost)}</p><p className="mt-0.5 text-xs text-gray-600">Đạm {item.total_protein_g.toFixed(1)}g · Carb {item.total_carbs_g.toFixed(1)}g</p></td><td className="px-5 py-3.5 text-gray-600">{formatDate(item.updated_at)}</td><td className="px-5 py-3.5"><div className="flex justify-end gap-1"><button type="button" onClick={() => openEdit(item)} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-gray-600 transition hover:bg-brand-50 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400" aria-label={`Sửa ${item.name}`}><Pencil className="h-4 w-4" /></button><button type="button" disabled={savingId === item.id} onClick={() => toggle(item)} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-gray-600 transition hover:bg-sand-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:opacity-50" aria-label={item.is_active ? `Ẩn ${item.name}` : `Khôi phục ${item.name}`}>{item.is_active ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button></div></td></tr>)}</tbody></table></div>}{!loading && !error && <AdminPagination offset={offset} limit={LIMIT} total={total} onChange={setOffset} />}</Card>
    <Modal open={open} onClose={() => setOpen(false)} title={editing ? `Sửa ${editing.name}` : "Thêm món thành phần"} size="lg" footer={<>{editing && <Button type="button" variant="danger" onClick={() => setDeleting(editing)}><Trash2 className="h-4 w-4" /> Xóa món</Button>}<Button variant="ghost" onClick={() => setOpen(false)}>Hủy</Button><Button form="admin-dish-form" type="submit" loading={saving}>Lưu công thức</Button></>}><form id="admin-dish-form" onSubmit={save} className="space-y-6"><section><h3 className="font-semibold text-gray-900">Thông tin món</h3><div className="mt-3 grid gap-4 sm:grid-cols-2"><TextField className="sm:col-span-2" label="Tên món" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /><SelectField label="Loại món" value={form.dish_type} options={DISH_TYPE_OPTIONS} onChange={(e) => setForm({ ...form, dish_type: e.target.value as DishType })} /><SelectField label="Cách chế biến" value={form.cooking_method} placeholder="Chưa xác định" options={METHOD_OPTIONS} onChange={(e) => setForm({ ...form, cooking_method: e.target.value as CookingMethod | "" })} /><TextField className="sm:col-span-2" label="Thẻ" value={form.tags} hint="Cách nhau bằng dấu phẩy." onChange={(e) => setForm({ ...form, tags: e.target.value })} /><Textarea className="sm:col-span-2" label="Mô tả" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /><Textarea className="sm:col-span-2" label="Hướng dẫn chế biến" rows={4} value={form.instructions} hint="Món chưa có hướng dẫn sẽ được đánh dấu cần bổ sung." onChange={(e) => setForm({ ...form, instructions: e.target.value })} /></div></section><section className="border-t border-sand-200 pt-5"><div className="flex items-baseline justify-between gap-4"><div><h3 className="font-semibold text-gray-900">Công thức</h3><p className="mt-1 text-sm text-gray-600">Giá và dinh dưỡng được tính tự động từ danh sách này.</p></div><span className="text-sm text-gray-600">{form.ingredients.length} nguyên liệu</span></div><div className="mt-3"><IngredientPicker placeholder="Tìm và thêm nguyên liệu" onSelect={(item) => addIngredient(item.id, item.name, item.default_unit)} /></div>{form.ingredients.length > 0 ? <ul className="mt-3 divide-y divide-sand-100 rounded-xl border border-sand-200">{form.ingredients.map((item) => <IngredientEditorRow key={item.ingredient_id} item={item} onChange={(patch) => updateIngredient(item.ingredient_id, patch)} onRemove={() => removeIngredient(item.ingredient_id)} />)}</ul> : <p className="mt-3 rounded-xl bg-sand-50 px-3 py-3 text-sm text-gray-600">Thêm ít nhất một nguyên liệu trước khi kích hoạt món.</p>}</section></form></Modal>
    <ConfirmDialog open={!!deleting} onClose={() => setDeleting(null)} onConfirm={deleteDish} loading={deletingId === deleting?.id} title="Xóa món thành phần" message={deleting ? `Xóa vĩnh viễn “${deleting.name}”? Công thức của món cũng sẽ bị xóa.` : ""} confirmLabel="Xóa món" />
  </div>;
}
