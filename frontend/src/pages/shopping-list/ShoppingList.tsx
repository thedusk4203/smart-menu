import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { ShoppingCart, Printer, History, Share2, Copy, X } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi } from "../../api/mealPlanApi";
import type { ShoppingListItem } from "../../api/mealPlanApi";
import {
  PageHeader, Card, SelectField, Spinner, EmptyState, Badge, Button, Modal, TextField,
} from "../../components/ui";
import { formatNumber, formatVND } from "../../lib/format";
import { ApiError } from "../../lib/apiClient";
import type { MealPlan } from "../../types";

export function ShoppingList() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [selectedId, setSelectedId] = useState("");
  const [items, setItems] = useState<ShoppingListItem[]>([]);
  const [warnings, setWarnings] = useState<Array<{ code: string; message: string }>>([]);
  const [totalEstimatedCost, setTotalEstimatedCost] = useState(0);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [building, setBuilding] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [shareLink, setShareLink] = useState("");
  const [shareExpiresAt, setShareExpiresAt] = useState("");

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const list = await mealPlanApi.list();
        setPlans(list);
      } catch (err) {
        toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
      } finally {
        setLoadingPlans(false);
      }
    })();
  }, [user]);

  const buildList = async (planId: number) => {
    setBuilding(true);
    setItems([]);
    setWarnings([]);
    setTotalEstimatedCost(0);
    try {
      const shoppingList = await mealPlanApi.shoppingList(planId);
      setItems(shoppingList.items);
      setChecked(Object.fromEntries(shoppingList.items.map((item) => [`${item.ingredient_id}__${item.unit}`, item.is_purchased])));
      setWarnings(shoppingList.warnings);
      setTotalEstimatedCost(shoppingList.total_estimated_cost);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setBuilding(false);
    }
  };

  const onSelect = (value: string) => {
    setSelectedId(value);
    if (value) buildList(Number(value));
  };

  const toggle = async (item: ShoppingListItem) => {
    if (!selectedId || !item.id) return;
    const key = `${item.ingredient_id}__${item.unit}`;
    const next = !checked[key];
    setChecked((current) => ({ ...current, [key]: next }));
    try { await mealPlanApi.updateShoppingItem(Number(selectedId), item.id, next); }
    catch (err) { setChecked((current) => ({ ...current, [key]: !next })); toast.error(err instanceof ApiError ? err.message : "Không thể cập nhật danh sách"); }
  };

  const createShare = async () => {
    if (!selectedId) return;
    setSharing(true);
    try {
      const share = await mealPlanApi.shareShoppingList(Number(selectedId));
      setShareLink(`${window.location.origin}/share/shopping-list/${share.token}`);
      setShareExpiresAt(share.expires_at);
    } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể tạo liên kết chia sẻ"); }
    finally { setSharing(false); }
  };

  const copyShareLink = async () => {
    try { await navigator.clipboard.writeText(shareLink); toast.success("Đã sao chép liên kết."); }
    catch { toast.error("Không thể sao chép tự động. Hãy chọn và sao chép liên kết bên dưới."); }
  };

  const revokeShare = async () => {
    if (!selectedId) return;
    try { await mealPlanApi.revokeShoppingShare(Number(selectedId)); setShareLink(""); setShareExpiresAt(""); toast.success("Đã thu hồi liên kết."); }
    catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể thu hồi liên kết"); }
  };

  const doneCount = items.filter((it) => checked[`${it.ingredient_id}__${it.unit}`]).length;

  if (loadingPlans) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Danh sách đi chợ"
        description="Chọn một thực đơn đã lưu để tự động gom nguyên liệu cần mua."
        actions={
          items.length > 0 ? (
            <div className="no-print flex gap-2"><Button variant="secondary" onClick={createShare}><Share2 className="h-4 w-4" /> Chia sẻ</Button><button onClick={() => window.print()} className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"><Printer className="h-4 w-4" /> In danh sách</button></div>
          ) : undefined
        }
      />

      {plans.length === 0 ? (
        <EmptyState
          icon={History}
          title="Chưa có thực đơn đã lưu"
          description="Hãy tạo và lưu thực đơn trước, sau đó quay lại để lập danh sách đi chợ."
          action={
            <Link
              to="/create-menu"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700"
            >
              Tạo thực đơn
            </Link>
          }
        />
      ) : (
        <>
          <div className="no-print mb-5 max-w-md">
            <SelectField
              label="Chọn thực đơn"
              value={selectedId}
              onChange={(e) => onSelect(e.target.value)}
              options={plans.map((p) => ({ value: String(p.id), label: p.name }))}
              placeholder="— Chọn một thực đơn —"
            />
          </div>

          {building ? (
            <div className="flex justify-center py-16">
              <Spinner className="h-7 w-7" />
            </div>
          ) : selectedId && items.length === 0 ? (
            <><>{warnings.map((warning) => <div key={warning.code} className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{warning.message}</div>)}</><EmptyState icon={ShoppingCart} title="Không có nguyên liệu" description="Thực đơn này chưa có nguyên liệu để gom." /></>
          ) : items.length > 0 ? (
            <>
            {warnings.length > 0 && <div className="mb-4 space-y-2">{warnings.map((warning) => <div key={warning.code} className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{warning.message}</div>)}</div>}
            <Card
              title="Nguyên liệu cần mua"
              icon={<ShoppingCart className="h-5 w-5" />}
              action={
                <Badge className="bg-brand-100 text-brand-700">
                  {doneCount}/{items.length} đã mua · {formatVND(totalEstimatedCost)}
                </Badge>
              }
              bodyClassName="p-0"
            >
              <ul className="divide-y divide-sand-100">
                {items.map((it) => {
                  const key = `${it.ingredient_id}__${it.unit}`;
                  const isChecked = !!checked[key];
                  return (
                    <li key={key} className="flex items-center gap-3 px-5 py-3">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggle(it)}
                        className="h-4 w-4 rounded border-sand-300 text-brand-600 focus:ring-brand-400"
                      />
                      <span
                        className={`flex-1 text-sm font-medium ${
                          isChecked ? "text-gray-400 line-through" : "text-gray-800"
                        }`}
                      >
                        {it.name}
                      </span>
                      <span className="text-sm text-gray-500">
                        {formatNumber(it.quantity, 1)} {it.unit} · {formatVND(it.estimated_cost)}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </Card>
            </>
          ) : (
            <p className="text-sm text-gray-500">Chọn một thực đơn để bắt đầu.</p>
          )}
        </>
      )}
      <Modal open={!!shareLink || sharing} onClose={() => !sharing && setShareLink("")} title="Chia sẻ danh sách đi chợ" size="sm" footer={<Button variant="ghost" onClick={() => setShareLink("")}>Đóng</Button>}>
        {sharing ? <div className="flex justify-center py-8"><Spinner className="h-6 w-6" /></div> : <div className="space-y-4"><p className="text-sm text-gray-700">Bất kỳ ai có liên kết đều có thể xem và tích các nguyên liệu đã mua. Liên kết hết hạn sau 7 ngày.</p><TextField label="Liên kết chia sẻ" value={shareLink} readOnly /><p className="text-xs text-gray-500">Hết hạn: {shareExpiresAt ? new Date(shareExpiresAt).toLocaleString("vi-VN") : "—"}</p><div className="flex flex-wrap gap-2"><Button onClick={copyShareLink}><Copy className="h-4 w-4" /> Sao chép link</Button><Button variant="danger" onClick={revokeShare}><X className="h-4 w-4" /> Thu hồi</Button></div></div>}
      </Modal>
    </div>
  );
}
