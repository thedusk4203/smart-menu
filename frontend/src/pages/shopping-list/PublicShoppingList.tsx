import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ShoppingCart } from "lucide-react";
import { publicShoppingListApi, type PublicShoppingListResponse } from "../../api/mealPlanApi";
import { ApiError } from "../../lib/apiClient";
import { formatDate, formatNumber, formatVND } from "../../lib/format";

export function PublicShoppingList() {
  const { token = "" } = useParams();
  const [data, setData] = useState<PublicShoppingListResponse | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setData(await publicShoppingListApi.get(token));
      setError("");
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 410
          ? "Liên kết này đã hết hạn hoặc đã bị thu hồi."
          : "Không thể mở danh sách đi chợ.",
      );
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

  const toggle = async (id: number | null | undefined, current: boolean) => {
    if (!id) return;
    setData((value) =>
      value
        ? {
            ...value,
            items: value.items.map((item) =>
              item.id === id ? { ...item, is_purchased: !current } : item,
            ),
          }
        : value,
    );
    try {
      setData(await publicShoppingListApi.updateItem(token, id, !current));
    } catch {
      await load();
    }
  };

  if (error) {
    return (
      <main className="mx-auto max-w-xl p-6">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-900">
          <h1 className="text-lg font-semibold">Không mở được danh sách</h1>
          <p className="mt-2 text-sm">{error}</p>
        </div>
      </main>
    );
  }
  if (!data) {
    return <main className="mx-auto max-w-xl p-6 text-sm text-gray-600">Đang mở danh sách đi chợ…</main>;
  }

  const done = data.items.filter((item) => item.is_purchased).length;
  const dayLabel = data.day
    ? `Ngày ${data.day}${data.date ? ` · ${formatDate(data.date)}` : ""}`
    : "Toàn bộ thực đơn";
  const scopeLabel = data.scope === "purchase_day"
    ? `Lịch mua · ${dayLabel}`
    : data.scope === "usage_day"
      ? `Dòng tồn kho · ${dayLabel}`
      : dayLabel;

  return (
    <main className="mx-auto min-h-screen max-w-2xl bg-sand-50 p-4 sm:p-8">
      <header className="mb-5">
        <div className="flex items-center gap-2 text-brand-700">
          <ShoppingCart className="h-5 w-5" />
          <span className="font-bold">Smart Menu</span>
        </div>
        <h1 className="mt-4 text-2xl font-bold text-gray-900">Danh sách đi chợ – {data.plan_name}</h1>
        <p className="mt-1 text-sm font-medium text-brand-700">{scopeLabel}</p>
        <p className="mt-1 text-sm text-gray-700">
          {done}/{data.items.length} đã mua · {formatVND(data.total_estimated_cost)}
        </p>
        <p className="mt-1 text-xs text-gray-600">
          Liên kết hết hạn lúc {new Date(data.expires_at).toLocaleString("vi-VN")}
        </p>
      </header>

      {data.warnings.length > 0 && (
        <div className="mb-4 space-y-2">
          {data.warnings.map((warning) => (
            <p key={warning.code} className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {warning.message}
            </p>
          ))}
        </div>
      )}

      {data.items.length > 0 && <section aria-label="Nguyên liệu cần mua" className="overflow-hidden rounded-2xl border border-sand-200 bg-white">
        <ul className="divide-y divide-sand-100">
          {data.items.map((item) => {
            const purchase = data.purchase_items.find((value) => value.item_key === item.item_key);
            return (
              <li key={item.item_key ?? item.id ?? `${item.ingredient_id}-${item.unit}`} className="flex items-start gap-3 px-4 py-3">
                <input
                  type="checkbox"
                  checked={item.is_purchased}
                  onChange={() => toggle(item.id, item.is_purchased)}
                  aria-label={`${item.is_purchased ? "Bỏ đánh dấu" : "Đánh dấu đã có"} ${item.name}`}
                  className="mt-1 h-4 w-4 rounded border-sand-300 text-brand-600 focus:ring-brand-400"
                />
                <div className="min-w-0 flex-1">
                  <p className={`text-sm font-medium ${item.is_purchased ? "text-gray-500 line-through" : "text-gray-900"}`}>
                    {item.name}
                    {item.item_kind === "pantry" && (
                      <span className="ml-2 rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-800">
                        kiểm tra trong bếp
                      </span>
                    )}
                  </p>
                  <p className="mt-1 text-xs text-gray-600">
                    {purchase
                      ? `Cần ${formatNumber(purchase.required_quantity, 1)} ${purchase.unit} · mua ${formatNumber(purchase.purchase_quantity, 1)} ${purchase.unit} (${purchase.block_count} block)`
                      : `${formatNumber(item.quantity, 1)} ${item.unit}`}
                  </p>
                </div>
                <span className="text-sm font-medium tabular-nums text-gray-700">
                  {item.item_kind === "pantry" ? "Có sẵn" : formatVND(item.estimated_cost)}
                </span>
              </li>
            );
          })}
        </ul>
      </section>}

      {data.daily_ledger.length > 0 && data.scope !== "purchase_day" && (
        <div className="space-y-4">
          {data.daily_ledger.map((day) => <section key={day.day} className="overflow-hidden rounded-2xl border border-sand-200 bg-white"><div className="flex items-center justify-between bg-sand-50 px-4 py-3"><h2 className="font-semibold text-gray-900">Dòng tồn kho · Ngày {day.day}</h2><span className="text-xs font-medium text-sky-700">Tồn cuối {formatVND(day.totals.closing_value ?? 0)}</span></div><ul className="divide-y divide-sand-100">{day.items.map((row) => <li key={row.item_key} className="px-4 py-3"><div className="flex items-center justify-between gap-3"><span className="font-medium text-gray-900">{row.name}</span><span className="font-semibold text-brand-800">{formatNumber(row.closing_quantity, 1)} {row.unit} còn lại</span></div><p className="mt-1 text-xs text-gray-600">Đầu {formatNumber(row.opening_quantity, 1)} + mua {formatNumber(row.purchase_quantity, 1)} − dùng {formatNumber(row.usage_quantity, 1)} − hết hạn {formatNumber(row.expired_quantity, 1)} {row.unit}</p></li>)}</ul></section>)}
        </div>
      )}

      {data.carryover_usage.length > 0 && (
        <section className="mt-4 rounded-2xl border border-sky-200 bg-sky-50 p-4" aria-labelledby="carryover-title">
          <h2 id="carryover-title" className="font-semibold text-sky-950">Dùng lại từ lần mua trước</h2>
          <ul className="mt-2 space-y-2">
            {data.carryover_usage.map((item, index) => (
              <li key={`${item.ingredient_id}-${item.purchase_day}-${index}`} className="text-sm text-sky-900">
                <span className="font-medium">{item.name}</span>
                {` · ${formatNumber(item.quantity, 1)} ${item.unit} · mua ngày ${item.purchase_day} · bảo quản ${item.storage_mode} đến ngày ${item.expiry_day}`}
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.leftovers.length > 0 && (
        <section className="mt-4 rounded-2xl border border-sand-200 bg-white p-4" aria-labelledby="leftover-title">
          <h2 id="leftover-title" className="font-semibold text-gray-900">Phần còn sau kế hoạch</h2>
          <ul className="mt-2 space-y-2">
            {data.leftovers.map((item, index) => (
              <li key={`${item.ingredient_id}-${item.status}-${index}`} className="text-sm text-gray-700">
                <span className="font-medium text-gray-900">{item.name}</span>
                {` · ${formatNumber(item.quantity, 1)} ${item.unit} · ${item.status === "expired_waste" ? "dự kiến hết hạn" : "còn dùng tiếp"}`}
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
