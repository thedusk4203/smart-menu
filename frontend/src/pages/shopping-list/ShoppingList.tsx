import { Fragment, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowRight, CalendarDays, ShoppingCart, Printer, History, Share2, Copy, X } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi } from "../../api/mealPlanApi";
import type { CarryoverUsage, DailyLedgerDay, ShoppingListItem, ShoppingPurchaseItem, ShoppingScope } from "../../api/mealPlanApi";
import {
  PageHeader, Card, SelectField, Spinner, EmptyState, Badge, Button, Modal, TextField,
} from "../../components/ui";
import { formatDate, formatNumber, formatVND } from "../../lib/format";
import { ApiError } from "../../lib/apiClient";
import type { MealPlan } from "../../types";

const STALE_BACKEND_MESSAGE = "Backend local đang chạy sai phiên bản. Hãy dừng các backend cũ và chạy lại duy nhất cổng 8001.";

export function ShoppingList() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [selectedId, setSelectedId] = useState("");
  const [selectedDay, setSelectedDay] = useState("all");
  const [viewMode, setViewMode] = useState<"ledger" | "purchase">("ledger");
  const [ledgerAvailable, setLedgerAvailable] = useState(false);
  const [items, setItems] = useState<ShoppingListItem[]>([]);
  const [purchaseItems, setPurchaseItems] = useState<ShoppingPurchaseItem[]>([]);
  const [carryoverUsage, setCarryoverUsage] = useState<CarryoverUsage[]>([]);
  const [leftovers, setLeftovers] = useState<Array<{ ingredient_id: number; name: string; quantity: number; unit: string; purchase_day: number; status: "carryover" | "closing_stock" | "expired_waste" }>>([]);
  const [dailyLedger, setDailyLedger] = useState<DailyLedgerDay[]>([]);
  const [warnings, setWarnings] = useState<Array<{ code: string; message: string }>>([]);
  const [totalEstimatedCost, setTotalEstimatedCost] = useState(0);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [building, setBuilding] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [shareLink, setShareLink] = useState("");
  const [shareExpiresAt, setShareExpiresAt] = useState("");
  const buildRequest = useRef(0);

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

  const buildList = async (planId: number, day?: number, scope?: ShoppingScope) => {
    const requestId = ++buildRequest.current;
    setBuilding(true);
    setItems([]);
    setWarnings([]);
    setTotalEstimatedCost(0);
    try {
      const shoppingList = await mealPlanApi.shoppingList(planId, day, scope);
      if (requestId !== buildRequest.current) return;
      if (day !== undefined && shoppingList.day !== day) {
        throw new ApiError(409, STALE_BACKEND_MESSAGE);
      }
      setItems(shoppingList.items);
      setChecked(Object.fromEntries(shoppingList.items.map((item) => [item.item_key ?? `${item.ingredient_id}__${item.unit}`, item.is_purchased])));
      setPurchaseItems(shoppingList.purchase_items ?? []);
      setCarryoverUsage(shoppingList.carryover_usage ?? []);
      setLeftovers(shoppingList.leftovers ?? []);
      setDailyLedger(shoppingList.daily_ledger ?? []);
      const supportsLedger = shoppingList.shopping_schema_version >= 3;
      setLedgerAvailable(supportsLedger);
      if (!supportsLedger) setViewMode("purchase");
      setWarnings(shoppingList.warnings);
      setTotalEstimatedCost(shoppingList.total_estimated_cost);
    } catch (err) {
      if (requestId !== buildRequest.current) return;
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      if (requestId === buildRequest.current) setBuilding(false);
    }
  };

  const onSelect = (value: string) => {
    setSelectedId(value);
    setSelectedDay("all");
    setViewMode("ledger");
    setLedgerAvailable(false);
    setShareLink("");
    setShareExpiresAt("");
    if (value) {
      buildList(Number(value));
    } else {
      buildRequest.current += 1;
      setItems([]);
      setPurchaseItems([]); setCarryoverUsage([]); setLeftovers([]); setDailyLedger([]);
      setLedgerAvailable(false);
      setWarnings([]);
      setTotalEstimatedCost(0);
      setChecked({});
      setBuilding(false);
    }
  };

  const onSelectDay = (value: string) => {
    setSelectedDay(value);
    setShareLink("");
    setShareExpiresAt("");
    if (selectedId) {
      const plan = plans.find((item) => String(item.id) === selectedId);
      const day = value === "all" ? undefined : Number(value);
      const scope = plan?.plan_data.schema_version === 3
        ? (day ? (viewMode === "ledger" ? "usage_day" : "purchase_day") : "all")
        : undefined;
      buildList(Number(selectedId), day, scope);
    }
  };

  const onSelectMode = (mode: "ledger" | "purchase") => {
    setViewMode(mode);
    if (!selectedId) return;
    const day = selectedDay === "all" ? undefined : Number(selectedDay);
    buildList(Number(selectedId), day, day ? (mode === "ledger" ? "usage_day" : "purchase_day") : "all");
  };

  const toggle = async (item: ShoppingListItem) => {
    if (!selectedId || !item.id) return;
    const key = item.item_key ?? `${item.ingredient_id}__${item.unit}`;
    const next = !checked[key];
    setChecked((current) => ({ ...current, [key]: next }));
    const day = selectedDay === "all" ? undefined : Number(selectedDay);
    const scope = selectedPlan?.plan_data.schema_version === 3 ? (day ? (viewMode === "ledger" ? "usage_day" : "purchase_day") : "all") : undefined;
    try { await mealPlanApi.updateShoppingItem(Number(selectedId), item.id, next, day, scope); }
    catch (err) { setChecked((current) => ({ ...current, [key]: !next })); toast.error(err instanceof ApiError ? err.message : "Không thể cập nhật danh sách"); }
  };

  const createShare = async () => {
    if (!selectedId) return;
    setSharing(true);
    try {
      const day = selectedDay === "all" ? undefined : Number(selectedDay);
      const scope = selectedPlan?.plan_data.schema_version === 3 ? (day ? (viewMode === "ledger" ? "usage_day" : "purchase_day") : "all") : undefined;
      const share = await mealPlanApi.shareShoppingList(Number(selectedId), day, scope);
      if (day !== undefined && share.day !== day) {
        throw new ApiError(409, STALE_BACKEND_MESSAGE);
      }
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

  const selectedPlan = plans.find((plan) => String(plan.id) === selectedId);
  const dayOptions = selectedPlan?.plan_data.days.map((day) => ({
    value: String(day.day),
    label: `Ngày ${day.day}${day.date ? ` · ${formatDate(day.date)}` : ""}`,
  })) ?? [];
  const selectedScopeLabel = selectedDay === "all"
    ? `Tất cả ${selectedPlan?.plan_data.days.length ?? 0} ngày`
    : dayOptions.find((option) => option.value === selectedDay)?.label ?? `Ngày ${selectedDay}`;
  const doneCount = items.filter((it) => checked[it.item_key ?? `${it.ingredient_id}__${it.unit}`]).length;
  const groupedItems: Array<{ key: string; label: string | null; items: ShoppingListItem[] }> = (() => {
    if (selectedPlan?.plan_data.schema_version !== 3 || selectedDay !== "all") {
      return [{ key: "visible", label: null, items }];
    }
    const groups = new Map<string, { key: string; label: string; items: ShoppingListItem[] }>();
    for (const item of items) {
      const key = item.scheduled_day ? `day-${item.scheduled_day}` : "pantry";
      const label = item.scheduled_day
        ? `Mua ngày ${item.scheduled_day}`
        : "Kiểm tra trong bếp trước khi đi chợ";
      const group = groups.get(key) ?? { key, label, items: [] };
      group.items.push(item);
      groups.set(key, group);
    }
    return [...groups.values()].sort((left, right) => {
      if (left.key === "pantry") return 1;
      if (right.key === "pantry") return -1;
      return left.key.localeCompare(right.key, "vi", { numeric: true });
    });
  })();

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
        description="Chọn thực đơn, sau đó xem nguyên liệu cho toàn bộ kế hoạch hoặc từng ngày."
        actions={
          items.length > 0 || dailyLedger.length > 0 ? (
            <div className="no-print flex flex-wrap gap-2"><Button variant="secondary" onClick={createShare}><Share2 className="h-4 w-4" /> Chia sẻ</Button><button onClick={() => window.print()} className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"><Printer className="h-4 w-4" /> In danh sách</button></div>
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
          <div className="no-print mb-3 grid max-w-3xl gap-3 sm:grid-cols-2">
            <SelectField
              label="Chọn thực đơn"
              value={selectedId}
              onChange={(e) => onSelect(e.target.value)}
              options={plans.map((p) => ({ value: String(p.id), label: p.name }))}
              placeholder="— Chọn một thực đơn —"
            />
            {selectedPlan && (
              <SelectField
                label="Chọn ngày theo dõi"
                value={selectedDay}
                onChange={(e) => onSelectDay(e.target.value)}
                options={[{ value: "all", label: `Tất cả ${selectedPlan.plan_data.days.length} ngày` }, ...dayOptions]}
                hint="Ledger hiển thị tồn thực tế cuối từng ngày; lịch mua chỉ hiển thị đồ cần mua."
              />
            )}
          </div>
          {selectedPlan?.plan_data.schema_version === 3 && ledgerAvailable && (
            <div className="no-print mb-5 inline-flex rounded-xl border border-sand-200 bg-white p-1" aria-label="Chế độ danh sách đi chợ">
              <button type="button" onClick={() => onSelectMode("ledger")} className={`inline-flex min-h-10 items-center gap-2 rounded-lg px-3 text-sm font-medium ${viewMode === "ledger" ? "bg-brand-600 text-white" : "text-gray-600 hover:bg-sand-50"}`}><CalendarDays className="h-4 w-4" /> Dòng tồn kho</button>
              <button type="button" onClick={() => onSelectMode("purchase")} className={`inline-flex min-h-10 items-center gap-2 rounded-lg px-3 text-sm font-medium ${viewMode === "purchase" ? "bg-brand-600 text-white" : "text-gray-600 hover:bg-sand-50"}`}><ShoppingCart className="h-4 w-4" /> Lịch mua</button>
            </div>
          )}

          {building ? (
            <div className="flex justify-center py-16">
              <Spinner className="h-7 w-7" />
            </div>
          ) : selectedId && items.length === 0 && dailyLedger.length === 0 ? (
            <><>{warnings.map((warning) => <div key={warning.code} className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{warning.message}</div>)}</><EmptyState icon={ShoppingCart} title="Không có nguyên liệu" description={`${selectedScopeLabel} chưa có nguyên liệu để gom.`} /></>
          ) : items.length > 0 || dailyLedger.length > 0 ? (
            <>
            {warnings.length > 0 && <div className="mb-4 space-y-2">{warnings.map((warning) => <div key={warning.code} className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{warning.message}</div>)}</div>}
            {viewMode === "ledger" && dailyLedger.length > 0 && (
              <div className="space-y-4">
                {dailyLedger.map((ledgerDay) => (
                  <Card key={ledgerDay.day} title={`Dòng tồn kho · Ngày ${ledgerDay.day}`} icon={<CalendarDays className="h-5 w-5" />} action={<Badge className="bg-sky-50 text-sky-700">Tồn cuối {formatVND(ledgerDay.totals.closing_value ?? 0)}</Badge>} bodyClassName="p-0">
                    <div className="overflow-x-auto">
                      <table className="min-w-[760px] w-full text-sm">
                        <thead className="bg-sand-50 text-left text-xs text-gray-600"><tr><th className="px-5 py-3 font-semibold">Nguyên liệu</th><th className="px-3 py-3 text-right font-semibold">Tồn đầu</th><th className="px-3 py-3 text-right font-semibold">Mua thêm</th><th className="px-3 py-3 text-right font-semibold">Dùng</th><th className="px-3 py-3 text-right font-semibold">Hết hạn</th><th className="px-5 py-3 text-right font-semibold">Tồn cuối</th></tr></thead>
                        <tbody className="divide-y divide-sand-100">{ledgerDay.items.map((row) => <tr key={row.item_key}><td className="px-5 py-3"><p className="font-medium text-gray-900">{row.name}</p><p className="mt-0.5 text-xs text-gray-500">{row.source_kind === "inventory" ? "Từ kho kế hoạch trước" : "Mua trong kế hoạch"}</p></td>{[row.opening_quantity, row.purchase_quantity, row.usage_quantity, row.expired_quantity].map((quantity, index) => <td key={index} className="px-3 py-3 text-right tabular-nums text-gray-600">{formatNumber(quantity, 1)} {row.unit}</td>)}<td className="px-5 py-3 text-right font-semibold tabular-nums text-brand-800">{formatNumber(row.closing_quantity, 1)} {row.unit}</td></tr>)}</tbody>
                      </table>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 border-t border-sand-100 px-5 py-3 text-xs text-gray-600"><span>{formatVND(ledgerDay.totals.opening_value ?? 0)} tồn đầu</span><ArrowRight className="h-3.5 w-3.5" /><span>+ {formatVND(ledgerDay.totals.purchase_cost ?? 0)} mua</span><ArrowRight className="h-3.5 w-3.5" /><span>− {formatVND(ledgerDay.totals.usage_value ?? 0)} dùng</span><ArrowRight className="h-3.5 w-3.5" /><span>= {formatVND(ledgerDay.totals.closing_value ?? 0)} tồn cuối</span></div>
                  </Card>
                ))}
              </div>
            )}
            {viewMode === "purchase" && items.length > 0 && (
            <Card
              title={`Lịch mua · ${selectedScopeLabel}`}
              icon={<ShoppingCart className="h-5 w-5" />}
              action={
                <Badge className="bg-brand-100 text-brand-700">
                  {doneCount}/{items.length} đã mua · {formatVND(totalEstimatedCost)}
                </Badge>
              }
              bodyClassName="p-0"
            >
              <ul className="divide-y divide-sand-100">
                {groupedItems.map((group) => <Fragment key={group.key}>
                {group.label && <li className="bg-sand-50 px-5 py-2 text-xs font-semibold text-gray-700">{group.label}</li>}
                {group.items.map((it) => {
                  const key = it.item_key ?? `${it.ingredient_id}__${it.unit}`;
                  const isChecked = !!checked[key];
                  const purchase = purchaseItems.find((item) => item.item_key === it.item_key);
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
                        {it.name}{it.item_kind === "pantry" ? " · kiểm tra trong bếp" : ""}
                      </span>
                      <span className="text-sm text-gray-500">
                        {purchase
                          ? `Dùng ${formatNumber(purchase.required_quantity, 1)}${purchase.unit} · Mua ${formatNumber(purchase.purchase_quantity, 1)}${purchase.unit} · ${formatVND(purchase.purchase_cost)}`
                          : `${formatNumber(it.quantity, 1)} ${it.unit} · ${formatVND(it.estimated_cost)}`}
                      </span>
                    </li>
                  );
                })}
                </Fragment>)}
              </ul>
            </Card>
            )}
            {viewMode === "purchase" && carryoverUsage.length > 0 && <Card title="Dùng lại từ tồn đầu ngày" bodyClassName="p-0"><ul className="divide-y divide-sand-100">{carryoverUsage.map((item, index) => <li key={`${item.ingredient_id}-${item.purchase_day}-${item.use_day}-${index}`} className="px-5 py-3 text-sm"><span className="font-medium text-gray-800">{item.name}</span><span className="ml-2 text-gray-500">{formatNumber(item.quantity, 1)} {item.unit} · {item.storage_mode} đến ngày {item.expiry_day}</span></li>)}</ul></Card>}
            {viewMode === "ledger" && leftovers.length > 0 && <Card title={selectedDay === "all" ? "Tồn cuối kế hoạch" : "Tồn cuối ngày"} bodyClassName="p-0"><ul className="divide-y divide-sand-100">{leftovers.map((item, index) => <li key={`${item.ingredient_id}-${item.purchase_day}-${item.status}-${index}`} className="px-5 py-3 text-sm"><span className="font-medium text-gray-800">{item.name}</span><span className={`ml-2 ${item.status === "expired_waste" ? "text-amber-700" : "text-sky-700"}`}>{formatNumber(item.quantity, 1)} {item.unit} · {item.status === "expired_waste" ? "dự kiến hết hạn" : "còn dùng tiếp"}</span></li>)}</ul></Card>}
            </>
          ) : (
            <p className="text-sm text-gray-500">Chọn một thực đơn để bắt đầu.</p>
          )}
        </>
      )}
      <Modal open={!!shareLink || sharing} onClose={() => !sharing && setShareLink("")} title="Chia sẻ danh sách đi chợ" size="sm" footer={<Button variant="ghost" onClick={() => setShareLink("")}>Đóng</Button>}>
        {sharing ? <div className="flex justify-center py-8"><Spinner className="h-6 w-6" /></div> : <div className="space-y-4"><p className="text-sm text-gray-700">Liên kết chỉ hiển thị phạm vi “{selectedScopeLabel}”. Bất kỳ ai có liên kết đều có thể xem và tích các nguyên liệu đã mua. Liên kết hết hạn sau 7 ngày.</p><TextField label="Liên kết chia sẻ" value={shareLink} readOnly /><p className="text-xs text-gray-500">Hết hạn: {shareExpiresAt ? new Date(shareExpiresAt).toLocaleString("vi-VN") : "—"}</p><p className="text-xs text-gray-500">Thu hồi sẽ vô hiệu hóa mọi liên kết đi chợ của thực đơn này.</p><div className="flex flex-wrap gap-2"><Button onClick={copyShareLink}><Copy className="h-4 w-4" /> Sao chép link</Button><Button variant="danger" onClick={revokeShare}><X className="h-4 w-4" /> Thu hồi</Button></div></div>}
      </Modal>
    </div>
  );
}
