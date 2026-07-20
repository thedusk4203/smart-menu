import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowRight, CalendarDays, ShoppingCart, Printer, History, Share2, Copy, X } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi } from "../../api/mealPlanApi";
import type { CarryoverUsage, DailyLedgerDay, ShoppingListItem, ShoppingPurchaseItem, ShoppingScope } from "../../api/mealPlanApi";
import {
  PageHeader, Card, SelectField, Spinner, EmptyState, Badge, Button, Modal, TextField, FeedbackBanner, ConfirmDialog,
} from "../../components/ui";
import { formatDate, formatNumber, formatVND } from "../../lib/format";
import { ApiError } from "../../lib/apiClient";
import { isUserVisiblePlanNotice, planNoticeText } from "../../lib/domainMessages";
import { feedbackMessage, toUserFeedback, type UserFeedback } from "../../lib/userFeedback";
import type { MealPlan } from "../../types";
import {
  CarryoverSection,
  ShoppingDocumentHeader,
  ShoppingLedgerSections,
  ShoppingRows,
} from "./ShoppingListDocument";
import { buildShoppingRows, type ShoppingDisplayRow } from "./shoppingListView";

const STALE_DATA_MESSAGE = "Dữ liệu danh sách chưa khớp với ngày đã chọn. Hãy tải lại rồi thử lại.";

export function ShoppingList() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [selectedId, setSelectedId] = useState("");
  const [selectedDay, setSelectedDay] = useState("all");
  const [viewMode, setViewMode] = useState<"ledger" | "purchase">("ledger");
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
  const [feedback, setFeedback] = useState<UserFeedback | null>(null);
  const [confirmRevoke, setConfirmRevoke] = useState(false);
  const [printedAt, setPrintedAt] = useState("");
  const buildRequest = useRef(0);

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const list = await mealPlanApi.list();
        setPlans(list);
      } catch (err) {
        setFeedback(toUserFeedback(err, "load_history"));
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
    setFeedback(null);
    try {
      const shoppingList = await mealPlanApi.shoppingList(planId, day, scope);
      if (requestId !== buildRequest.current) return;
      if (day !== undefined && shoppingList.day !== day) {
        throw new ApiError(409, STALE_DATA_MESSAGE, { code: "SHOPPING_DATA_STALE", retryable: true });
      }
      setItems(shoppingList.items);
      setChecked(Object.fromEntries(shoppingList.items.map((item) => [item.item_key ?? `${item.ingredient_id}__${item.unit}`, item.is_purchased])));
      setPurchaseItems(shoppingList.purchase_items ?? []);
      setCarryoverUsage(shoppingList.carryover_usage ?? []);
      setLeftovers(shoppingList.leftovers ?? []);
      setDailyLedger(shoppingList.daily_ledger ?? []);
      setWarnings(shoppingList.warnings);
      setTotalEstimatedCost(shoppingList.total_estimated_cost);
    } catch (err) {
      if (requestId !== buildRequest.current) return;
      setFeedback(toUserFeedback(err, "load_shopping"));
    } finally {
      if (requestId === buildRequest.current) setBuilding(false);
    }
  };

  const onSelect = (value: string) => {
    setSelectedId(value);
    setSelectedDay("all");
    setViewMode("ledger");
    setShareLink("");
    setShareExpiresAt("");
    if (value) {
      buildList(Number(value));
    } else {
      buildRequest.current += 1;
      setItems([]);
      setPurchaseItems([]); setCarryoverUsage([]); setLeftovers([]); setDailyLedger([]);
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
      const day = value === "all" ? undefined : Number(value);
      const scope = day ? (viewMode === "ledger" ? "usage_day" : "purchase_day") : "all";
      buildList(Number(selectedId), day, scope);
    }
  };

  const onSelectMode = (mode: "ledger" | "purchase") => {
    setViewMode(mode);
    if (!selectedId) return;
    const day = selectedDay === "all" ? undefined : Number(selectedDay);
    buildList(Number(selectedId), day, day ? (mode === "ledger" ? "usage_day" : "purchase_day") : "all");
  };

  const toggleRow = async (row: ShoppingDisplayRow) => {
    if (!selectedId || row.sourceItemIds.length === 0) return;
    const next = !row.isPurchased;
    setChecked((current) => ({
      ...current,
      ...Object.fromEntries(row.sourceItemKeys.map((key) => [key, next])),
    }));
    const day = selectedDay === "all" ? undefined : Number(selectedDay);
    const scope = day ? (viewMode === "ledger" ? "usage_day" : "purchase_day") : "all";
    try {
      await mealPlanApi.updateShoppingItems(Number(selectedId), row.sourceItemIds, next, day, scope);
    } catch (err) {
      await buildList(Number(selectedId), day, scope);
      toast.error(feedbackMessage(err, "update_shopping"));
    }
  };

  const printList = () => {
    const host = window.location.host.replace(/^https?:\/\//i, "").replace(/\/+$/, "");
    setPrintedAt(new Date().toLocaleString("vi-VN"));
    const printStyle = document.createElement("style");
    printStyle.dataset.shoppingPrintFooter = "true";
    printStyle.textContent = `@page { @bottom-left { content: ${JSON.stringify(host)}; font-size: 9pt; color: #4b5563; } }`;
    document.head.appendChild(printStyle);
    window.addEventListener("afterprint", () => printStyle.remove(), { once: true });
    window.setTimeout(() => window.print(), 0);
  };

  const createShare = async () => {
    if (!selectedId) return;
    setSharing(true);
    try {
      const day = selectedDay === "all" ? undefined : Number(selectedDay);
      const scope = day ? (viewMode === "ledger" ? "usage_day" : "purchase_day") : "all";
      const share = await mealPlanApi.shareShoppingList(Number(selectedId), day, scope);
      if (day !== undefined && share.day !== day) {
        throw new ApiError(409, STALE_DATA_MESSAGE, { code: "SHOPPING_DATA_STALE", retryable: true });
      }
      setShareLink(`${window.location.origin}/share/shopping-list/${share.token}`);
      setShareExpiresAt(share.expires_at);
    } catch (err) { setFeedback(toUserFeedback(err, "share_shopping")); }
    finally { setSharing(false); }
  };

  const copyShareLink = async () => {
    try { await navigator.clipboard.writeText(shareLink); toast.success("Đã sao chép liên kết."); }
    catch { toast.error("Không thể sao chép tự động. Hãy chọn và sao chép liên kết bên dưới."); }
  };

  const revokeShare = async () => {
    if (!selectedId) return;
    try { await mealPlanApi.revokeShoppingShare(Number(selectedId)); setShareLink(""); setShareExpiresAt(""); setConfirmRevoke(false); toast.success("Đã thu hồi liên kết."); }
    catch (err) { setConfirmRevoke(false); setFeedback(toUserFeedback(err, "revoke_share")); }
  };

  const selectedPlan = plans.find((plan) => String(plan.id) === selectedId);
  const dayOptions = selectedPlan?.plan_data.days.map((day) => ({
    value: String(day.day),
    label: `Ngày ${day.day}${day.date ? ` · ${formatDate(day.date)}` : ""}`,
  })) ?? [];
  const selectedScopeLabel = selectedDay === "all"
    ? `Tất cả ${selectedPlan?.plan_data.days.length ?? 0} ngày`
    : dayOptions.find((option) => option.value === selectedDay)?.label ?? `Ngày ${selectedDay}`;
  const visibleItems = items.map((item) => ({
    ...item,
    is_purchased: checked[item.item_key ?? `${item.ingredient_id}__${item.unit}`] ?? item.is_purchased,
  }));
  const shoppingRows = buildShoppingRows(visibleItems, purchaseItems, selectedDay === "all");
  const doneCount = shoppingRows.filter((row) => row.isPurchased).length;
  const visibleWarnings = warnings.filter(isUserVisiblePlanNotice);
  const documentScopeLabel = `${viewMode === "purchase" ? "Cần mua" : "Tồn theo ngày"} · ${selectedScopeLabel}`;

  if (loadingPlans) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }

  return (
    <>
    <div className="no-print">
      <PageHeader
        title="Danh sách đi chợ"
        description="Chọn thực đơn, sau đó xem nguyên liệu cho toàn bộ kế hoạch hoặc từng ngày."
        actions={
          items.length > 0 || dailyLedger.length > 0 ? (
            <div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={createShare}><Share2 className="h-4 w-4" /> Chia sẻ</Button><button onClick={printList} className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"><Printer className="h-4 w-4" /> In danh sách</button></div>
          ) : undefined
        }
      />

      {feedback && <FeedbackBanner feedback={feedback} onDismiss={() => setFeedback(null)} className="mb-5" />}

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
                hint="“Tồn theo ngày” cho biết lượng còn lại sau mỗi ngày; “Cần mua” chỉ hiển thị những món cần đi chợ."
              />
            )}
          </div>
          {selectedPlan && (
            <div className="no-print mb-5 inline-flex rounded-xl border border-sand-200 bg-white p-1" aria-label="Chế độ danh sách đi chợ">
              <button type="button" onClick={() => onSelectMode("ledger")} className={`inline-flex min-h-10 items-center gap-2 rounded-lg px-3 text-sm font-medium ${viewMode === "ledger" ? "bg-brand-600 text-white" : "text-gray-600 hover:bg-sand-50"}`}><CalendarDays className="h-4 w-4" /> Tồn theo ngày</button>
              <button type="button" onClick={() => onSelectMode("purchase")} className={`inline-flex min-h-10 items-center gap-2 rounded-lg px-3 text-sm font-medium ${viewMode === "purchase" ? "bg-brand-600 text-white" : "text-gray-600 hover:bg-sand-50"}`}><ShoppingCart className="h-4 w-4" /> Cần mua</button>
            </div>
          )}

          {building ? (
            <div className="flex justify-center py-16">
              <Spinner className="h-7 w-7" />
            </div>
          ) : selectedId && items.length === 0 && dailyLedger.length === 0 ? (
            <><>{visibleWarnings.map((warning) => <div key={warning.code} className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{planNoticeText(warning)}</div>)}</><EmptyState icon={ShoppingCart} title="Không có nguyên liệu" description={`${selectedScopeLabel} chưa có nguyên liệu cần tổng hợp.`} /></>
          ) : items.length > 0 || dailyLedger.length > 0 ? (
            <>
            {visibleWarnings.length > 0 && <div className="mb-4 space-y-2">{visibleWarnings.map((warning) => <div key={warning.code} className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{planNoticeText(warning)}</div>)}</div>}
            {viewMode === "ledger" && dailyLedger.length > 0 && (
              <div className="space-y-4">
                {dailyLedger.map((ledgerDay) => (
                  <Card key={ledgerDay.day} title={`Tồn theo ngày · Ngày ${ledgerDay.day}`} icon={<CalendarDays className="h-5 w-5" />} action={<Badge className="bg-sky-50 text-sky-700">Tồn cuối {formatVND(ledgerDay.totals.closing_value ?? 0)}</Badge>} bodyClassName="p-0">
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
              title={`Cần mua · ${selectedScopeLabel}`}
              icon={<ShoppingCart className="h-5 w-5" />}
              action={
                <Badge className="bg-brand-100 text-brand-700">
                  {doneCount}/{shoppingRows.length} đã mua · {formatVND(totalEstimatedCost)}
                </Badge>
              }
              bodyClassName="p-0"
            >
              <ShoppingRows rows={shoppingRows} onToggle={toggleRow} />
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
        {sharing ? <div className="flex justify-center py-8"><Spinner className="h-6 w-6" /></div> : <div className="space-y-4"><p className="text-sm text-gray-700">Liên kết chỉ hiển thị phạm vi “{selectedScopeLabel}”. Bất kỳ ai có liên kết đều có thể xem và tích các nguyên liệu đã mua. Liên kết hết hạn sau 7 ngày.</p><TextField label="Liên kết chia sẻ" value={shareLink} readOnly /><p className="text-xs text-gray-500">Hết hạn: {shareExpiresAt ? new Date(shareExpiresAt).toLocaleString("vi-VN") : "—"}</p><p className="text-xs text-gray-500">Thu hồi sẽ làm mọi liên kết đi chợ của thực đơn này ngừng hoạt động ngay.</p><div className="flex flex-wrap gap-2"><Button onClick={copyShareLink}><Copy className="h-4 w-4" /> Sao chép liên kết</Button><Button variant="danger" onClick={() => setConfirmRevoke(true)}><X className="h-4 w-4" /> Thu hồi</Button></div></div>}
      </Modal>
      <ConfirmDialog open={confirmRevoke} onClose={() => setConfirmRevoke(false)} onConfirm={revokeShare} title="Thu hồi liên kết chia sẻ" message="Tất cả liên kết đi chợ của thực đơn này sẽ ngừng hoạt động ngay. Người đang mở liên kết cũng sẽ không thể cập nhật danh sách." confirmLabel="Thu hồi liên kết" cancelLabel="Giữ liên kết" />
    </div>
    <div className="print-only mx-auto max-w-2xl bg-white">
      <ShoppingDocumentHeader
        planName={selectedPlan?.name}
        scopeLabel={documentScopeLabel}
        done={doneCount}
        rowCount={shoppingRows.length}
        totalCost={totalEstimatedCost}
        printedAt={printedAt}
      />
      {visibleWarnings.length > 0 && <div className="mb-4 space-y-2">{visibleWarnings.map((warning) => <p key={warning.code} className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">{planNoticeText(warning)}</p>)}</div>}
      {viewMode === "purchase" && shoppingRows.length > 0 && <section className="overflow-hidden rounded-2xl border border-sand-200 bg-white"><ShoppingRows rows={shoppingRows} /></section>}
      {viewMode === "ledger" && <ShoppingLedgerSections days={dailyLedger} />}
      {viewMode === "purchase" && <CarryoverSection items={carryoverUsage} />}
    </div>
    </>
  );
}
