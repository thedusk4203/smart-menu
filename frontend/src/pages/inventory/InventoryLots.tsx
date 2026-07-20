import { useEffect, useState } from "react";
import { Archive, Pencil, Snowflake, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { inventoryApi } from "../../api/inventoryApi";
import type { InventoryLot } from "../../api/inventoryApi";
import { Badge, Button, Card, ConfirmDialog, EmptyState, FeedbackBanner, Modal, PageHeader, SelectField, Spinner, TextField } from "../../components/ui";
import { formatDate, formatNumber, formatVND } from "../../lib/format";
import { toUserFeedback, type UserFeedback } from "../../lib/userFeedback";

const STORAGE_LABELS: Record<InventoryLot["storage_mode"], string> = {
  room: "Nhiệt độ phòng",
  fridge: "Ngăn mát",
  freezer: "Ngăn đông",
  same_day: "Dùng trong ngày",
};

export function InventoryLots() {
  const [lots, setLots] = useState<InventoryLot[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<InventoryLot | null>(null);
  const [quantity, setQuantity] = useState("");
  const [expiresOn, setExpiresOn] = useState("");
  const [storageMode, setStorageMode] = useState<InventoryLot["storage_mode"]>("fridge");
  const [saving, setSaving] = useState(false);
  const [discarding, setDiscarding] = useState<InventoryLot | null>(null);
  const [feedback, setFeedback] = useState<UserFeedback | null>(null);

  const load = async () => {
    setLoading(true);
    try { setLots(await inventoryApi.list()); setFeedback(null); }
    catch (error) { setFeedback(toUserFeedback(error, "load_inventory")); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);

  const openEdit = (lot: InventoryLot) => {
    setEditing(lot);
    setQuantity(String(lot.quantity_remaining));
    setExpiresOn(lot.expires_on);
    setStorageMode(lot.storage_mode);
  };
  const save = async () => {
    if (!editing) return;
    setSaving(true);
    try {
      const updated = await inventoryApi.update(editing.id, {
        quantity_remaining: Number(quantity), expires_on: expiresOn, storage_mode: storageMode,
      });
      setLots((current) => current.map((lot) => lot.id === updated.id ? updated : lot));
      setEditing(null);
      toast.success("Đã cập nhật nguyên liệu còn lại.");
    } catch (error) { setFeedback(toUserFeedback(error, "update_inventory")); }
    finally { setSaving(false); }
  };
  const discard = async (lot: InventoryLot) => {
    try {
      const updated = await inventoryApi.update(lot.id, { status: "discarded" });
      setLots((current) => current.map((value) => value.id === updated.id ? updated : value));
      setDiscarding(null);
      toast.success("Đã đánh dấu loại bỏ phần dư.");
    } catch (error) { setDiscarding(null); setFeedback(toUserFeedback(error, "discard_inventory")); }
  };

  return <div>
    <PageHeader title="Nguyên liệu còn lại" description="Theo dõi phần nguyên liệu có thể dùng cho thực đơn sau. Smart Menu ưu tiên phần sắp hết hạn trước." />
    {feedback && <FeedbackBanner feedback={feedback} onRetry={load} onDismiss={() => setFeedback(null)} className="mb-5" />}
    {loading ? <div className="flex justify-center py-16"><Spinner className="h-7 w-7" /></div> : lots.length === 0 ? <EmptyState icon={Archive} title="Chưa có phần nguyên liệu còn lại" description="Phần nguyên liệu còn dùng được sau ngày cuối của thực đơn sẽ xuất hiện tại đây." /> : <Card bodyClassName="p-0"><div className="overflow-x-auto"><table className="min-w-[820px] w-full text-left text-sm"><thead className="bg-sand-50 text-xs text-gray-600"><tr><th className="px-5 py-3 font-semibold">Nguyên liệu</th><th className="px-3 py-3 font-semibold">Có thể dùng</th><th className="px-3 py-3 font-semibold">Bảo quản</th><th className="px-3 py-3 font-semibold">Nguồn</th><th className="px-5 py-3 text-right font-semibold">Thao tác</th></tr></thead><tbody className="divide-y divide-sand-100">{lots.map((lot) => <tr key={lot.id} className={lot.status === "discarded" || lot.status === "expired" ? "opacity-55" : ""}><td className="px-5 py-3"><p className="font-semibold text-gray-900">{lot.name}</p><p className="mt-0.5 text-xs text-gray-500">Giá trị ước tính {formatVND(lot.quantity_remaining * lot.cost_basis_per_unit)}</p></td><td className="px-3 py-3"><p className="font-medium tabular-nums text-gray-900">{formatNumber(lot.quantity_remaining, 1)} {lot.unit}</p>{lot.reserved_quantity > 0 && <p className="mt-0.5 text-xs text-amber-700">Đã dành {formatNumber(lot.reserved_quantity, 1)} {lot.unit} cho thực đơn khác</p>}</td><td className="px-3 py-3"><p className="text-gray-800">{STORAGE_LABELS[lot.storage_mode]}</p><p className="mt-0.5 text-xs text-gray-500">Hạn {formatDate(lot.expires_on)}</p></td><td className="px-3 py-3"><Badge className={lot.status === "available" ? "bg-emerald-50 text-emerald-700" : "bg-sand-100 text-gray-700"}>{lot.status === "projected" ? "Dự kiến" : lot.status === "available" ? "Có thể dùng" : lot.status === "expired" ? "Đã hết hạn" : lot.status === "discarded" ? "Đã loại bỏ" : "Đã dùng hết"}</Badge><p className="mt-1 text-xs text-gray-500">{lot.source_plan_name || "Điều chỉnh thủ công"}</p></td><td className="px-5 py-3"><div className="flex justify-end gap-1"><button type="button" onClick={() => openEdit(lot)} disabled={lot.status === "discarded"} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-gray-600 hover:bg-brand-50 hover:text-brand-800 disabled:opacity-40" aria-label={`Sửa ${lot.name}`}><Pencil className="h-4 w-4" /></button><button type="button" onClick={() => setDiscarding(lot)} disabled={lot.status === "discarded" || lot.reserved_quantity > 0} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-red-700 hover:bg-red-50 disabled:opacity-40" aria-label={`Loại bỏ ${lot.name}`}><Trash2 className="h-4 w-4" /></button></div></td></tr>)}</tbody></table></div></Card>}
    <Modal open={!!editing} onClose={() => !saving && setEditing(null)} title={editing ? `Cập nhật ${editing.name}` : "Cập nhật nguyên liệu còn lại"} size="sm" footer={<><Button variant="ghost" onClick={() => setEditing(null)} disabled={saving}>Hủy</Button><Button onClick={() => void save()} loading={saving}>Lưu thay đổi</Button></>}>
      <div className="space-y-4"><TextField label="Số lượng còn thực tế" type="number" min="0" step="0.01" value={quantity} onChange={(event) => setQuantity(event.target.value)} hint={editing?.reserved_quantity ? `Đang dành ${formatNumber(editing.reserved_quantity, 1)} ${editing.unit} cho thực đơn khác; chưa thể giảm xuống dưới số lượng này.` : undefined} /><TextField label="Hạn dùng" type="date" value={expiresOn} onChange={(event) => setExpiresOn(event.target.value)} /><SelectField label="Cách bảo quản" value={storageMode} onChange={(event) => setStorageMode(event.target.value as InventoryLot["storage_mode"])} options={Object.entries(STORAGE_LABELS).map(([value, label]) => ({ value, label }))} /><p className="flex items-start gap-2 rounded-xl bg-sky-50 px-3 py-3 text-sm text-sky-800"><Snowflake className="mt-0.5 h-4 w-4 shrink-0" /> Thay đổi này sẽ được dùng khi Smart Menu tạo các thực đơn tiếp theo.</p></div>
    </Modal>
    <ConfirmDialog open={!!discarding} onClose={() => setDiscarding(null)} onConfirm={() => discarding && void discard(discarding)} title="Loại bỏ nguyên liệu còn lại" message={`“${discarding?.name ?? "Nguyên liệu này"}” sẽ không còn được dùng cho các thực đơn sau. Bạn vẫn có thể xem trạng thái đã loại bỏ trong danh sách.`} confirmLabel="Loại bỏ" cancelLabel="Giữ lại" />
  </div>;
}
