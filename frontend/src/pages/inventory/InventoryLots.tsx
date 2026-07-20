import { useEffect, useState } from "react";
import { Archive, Pencil, Snowflake, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { inventoryApi } from "../../api/inventoryApi";
import type { InventoryLot } from "../../api/inventoryApi";
import { Badge, Button, Card, EmptyState, Modal, PageHeader, SelectField, Spinner, TextField } from "../../components/ui";
import { ApiError } from "../../lib/apiClient";
import { formatDate, formatNumber, formatVND } from "../../lib/format";

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

  const load = async () => {
    setLoading(true);
    try { setLots(await inventoryApi.list()); }
    catch (error) { toast.error(error instanceof ApiError ? error.message : "Không thể tải kho nguyên liệu."); }
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
      toast.success("Đã cập nhật lot kho.");
    } catch (error) { toast.error(error instanceof ApiError ? error.message : "Không thể cập nhật lot kho."); }
    finally { setSaving(false); }
  };
  const discard = async (lot: InventoryLot) => {
    try {
      const updated = await inventoryApi.update(lot.id, { status: "discarded" });
      setLots((current) => current.map((value) => value.id === updated.id ? updated : value));
      toast.success("Đã đánh dấu loại bỏ phần dư.");
    } catch (error) { toast.error(error instanceof ApiError ? error.message : "Không thể loại bỏ lot kho."); }
  };

  return <div>
    <PageHeader title="Kho nguyên liệu" description="Phần dư có thể dùng cho thực đơn sau. Planner tự ưu tiên lot sắp hết hạn trước." />
    {loading ? <div className="flex justify-center py-16"><Spinner className="h-7 w-7" /></div> : lots.length === 0 ? <EmptyState icon={Archive} title="Chưa có phần dư" description="Khi một thực đơn V3 còn nguyên liệu dùng được sau ngày cuối, lot đó sẽ xuất hiện tại đây." /> : <Card bodyClassName="p-0"><div className="overflow-x-auto"><table className="min-w-[820px] w-full text-left text-sm"><thead className="bg-sand-50 text-xs text-gray-600"><tr><th className="px-5 py-3 font-semibold">Nguyên liệu</th><th className="px-3 py-3 font-semibold">Khả dụng</th><th className="px-3 py-3 font-semibold">Bảo quản</th><th className="px-3 py-3 font-semibold">Nguồn</th><th className="px-5 py-3 text-right font-semibold">Thao tác</th></tr></thead><tbody className="divide-y divide-sand-100">{lots.map((lot) => <tr key={lot.id} className={lot.status === "discarded" || lot.status === "expired" ? "opacity-55" : ""}><td className="px-5 py-3"><p className="font-semibold text-gray-900">{lot.name}</p><p className="mt-0.5 text-xs text-gray-500">Giá trị ước tính {formatVND(lot.quantity_remaining * lot.cost_basis_per_unit)}</p></td><td className="px-3 py-3"><p className="font-medium tabular-nums text-gray-900">{formatNumber(lot.quantity_remaining, 1)} {lot.unit}</p>{lot.reserved_quantity > 0 && <p className="mt-0.5 text-xs text-amber-700">Đã giữ {formatNumber(lot.reserved_quantity, 1)} {lot.unit}</p>}</td><td className="px-3 py-3"><p className="text-gray-800">{STORAGE_LABELS[lot.storage_mode]}</p><p className="mt-0.5 text-xs text-gray-500">Hạn {formatDate(lot.expires_on)}</p></td><td className="px-3 py-3"><Badge className={lot.status === "available" ? "bg-emerald-50 text-emerald-700" : "bg-sand-100 text-gray-700"}>{lot.status === "projected" ? "Dự kiến" : lot.status === "available" ? "Có thể dùng" : lot.status === "expired" ? "Đã hết hạn" : lot.status === "discarded" ? "Đã loại bỏ" : "Đã dùng hết"}</Badge><p className="mt-1 text-xs text-gray-500">{lot.source_plan_name || "Điều chỉnh thủ công"}</p></td><td className="px-5 py-3"><div className="flex justify-end gap-1"><button type="button" onClick={() => openEdit(lot)} disabled={lot.status === "discarded"} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-gray-600 hover:bg-brand-50 hover:text-brand-800 disabled:opacity-40" aria-label={`Sửa ${lot.name}`}><Pencil className="h-4 w-4" /></button><button type="button" onClick={() => void discard(lot)} disabled={lot.status === "discarded" || lot.reserved_quantity > 0} className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-red-700 hover:bg-red-50 disabled:opacity-40" aria-label={`Loại bỏ ${lot.name}`}><Trash2 className="h-4 w-4" /></button></div></td></tr>)}</tbody></table></div></Card>}
    <Modal open={!!editing} onClose={() => !saving && setEditing(null)} title={editing ? `Cập nhật ${editing.name}` : "Cập nhật lot"} size="sm" footer={<><Button variant="ghost" onClick={() => setEditing(null)} disabled={saving}>Hủy</Button><Button onClick={() => void save()} loading={saving}>Lưu thay đổi</Button></>}>
      <div className="space-y-4"><TextField label="Số lượng còn thực tế" type="number" min="0" step="0.01" value={quantity} onChange={(event) => setQuantity(event.target.value)} hint={editing?.reserved_quantity ? `Lot đang giữ ${formatNumber(editing.reserved_quantity, 1)} ${editing.unit}; không thể giảm khi còn được thực đơn khác sử dụng.` : undefined} /><TextField label="Hạn dùng" type="date" value={expiresOn} onChange={(event) => setExpiresOn(event.target.value)} /><SelectField label="Cách bảo quản" value={storageMode} onChange={(event) => setStorageMode(event.target.value as InventoryLot["storage_mode"])} options={Object.entries(STORAGE_LABELS).map(([value, label]) => ({ value, label }))} /><p className="flex items-start gap-2 rounded-xl bg-sky-50 px-3 py-3 text-sm text-sky-800"><Snowflake className="mt-0.5 h-4 w-4 shrink-0" /> Điều chỉnh ở đây sẽ làm thay đổi dữ liệu đầu vào của thực đơn được tạo sau đó.</p></div>
    </Modal>
  </div>;
}
