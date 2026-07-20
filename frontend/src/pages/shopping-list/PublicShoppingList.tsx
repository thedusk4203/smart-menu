import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { publicShoppingListApi, type PublicShoppingListResponse } from "../../api/mealPlanApi";
import { FeedbackBanner } from "../../components/ui";
import { formatDate } from "../../lib/format";
import { isUserVisiblePlanNotice, planNoticeText } from "../../lib/domainMessages";
import { toUserFeedback, type UserFeedback } from "../../lib/userFeedback";
import {
  CarryoverSection,
  ShoppingDocumentHeader,
  ShoppingLedgerSections,
  ShoppingRows,
} from "./ShoppingListDocument";
import { buildShoppingRows, type ShoppingDisplayRow } from "./shoppingListView";

export function PublicShoppingList() {
  const { token = "" } = useParams();
  const [data, setData] = useState<PublicShoppingListResponse | null>(null);
  const [error, setError] = useState<UserFeedback | null>(null);

  const load = useCallback(async () => {
    try {
      setData(await publicShoppingListApi.get(token));
      setError(null);
    } catch (err) {
      setError(toUserFeedback(err, "load_shopping"));
    }
  }, [token]);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 5000);
    const refreshOnFocus = () => load();
    window.addEventListener("focus", refreshOnFocus);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", refreshOnFocus);
    };
  }, [load]);

  const toggle = async (row: ShoppingDisplayRow) => {
    if (row.sourceItemIds.length === 0) return;
    const next = !row.isPurchased;
    const sourceIds = new Set(row.sourceItemIds);
    setData((value) => value ? {
      ...value,
      items: value.items.map((item) =>
        item.id != null && sourceIds.has(item.id) ? { ...item, is_purchased: next } : item,
      ),
    } : value);
    try {
      setData(await publicShoppingListApi.updateItems(token, row.sourceItemIds, next));
    } catch {
      await load();
    }
  };

  if (error) {
    return <main className="mx-auto max-w-xl p-6"><FeedbackBanner feedback={error} onRetry={load} /></main>;
  }
  if (!data) {
    return <main className="mx-auto max-w-xl p-6 text-sm text-gray-600">Đang mở danh sách đi chợ…</main>;
  }

  const rows = buildShoppingRows(data.items, data.purchase_items, data.day == null);
  const done = rows.filter((row) => row.isPurchased).length;
  const dayLabel = data.day
    ? `Ngày ${data.day}${data.date ? ` · ${formatDate(data.date)}` : ""}`
    : "Toàn bộ thực đơn";
  const scopeLabel = data.scope === "purchase_day"
    ? `Cần mua · ${dayLabel}`
    : data.scope === "usage_day"
      ? `Tồn theo ngày · ${dayLabel}`
      : `Cần mua · ${dayLabel}`;
  const visibleWarnings = data.warnings.filter(isUserVisiblePlanNotice);

  return (
    <main className="mx-auto min-h-screen max-w-2xl bg-sand-50 p-4 sm:p-8">
      <ShoppingDocumentHeader
        planName={data.plan_name}
        scopeLabel={scopeLabel}
        done={done}
        rowCount={rows.length}
        totalCost={data.total_estimated_cost}
        meta={`Liên kết hết hạn lúc ${new Date(data.expires_at).toLocaleString("vi-VN")}`}
      />

      {visibleWarnings.length > 0 && (
        <div className="mb-4 space-y-2">
          {visibleWarnings.map((warning) => (
            <p key={warning.code} className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {planNoticeText(warning)}
            </p>
          ))}
        </div>
      )}

      {rows.length > 0 && (
        <section aria-label="Nguyên liệu cần mua" className="overflow-hidden rounded-2xl border border-sand-200 bg-white">
          <ShoppingRows rows={rows} onToggle={toggle} />
        </section>
      )}
      {data.daily_ledger.length > 0 && data.scope === "usage_day" && (
        <ShoppingLedgerSections days={data.daily_ledger} />
      )}
      <CarryoverSection items={data.carryover_usage} />
    </main>
  );
}
