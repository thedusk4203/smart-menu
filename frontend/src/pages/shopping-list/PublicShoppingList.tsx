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
    try { setData(await publicShoppingListApi.get(token)); setError(""); }
    catch (err) { setError(err instanceof ApiError && err.status === 410 ? "Liên kết này đã hết hạn hoặc đã bị thu hồi." : "Không thể mở danh sách đi chợ."); }
  }, [token]);
  useEffect(() => { load(); const timer = window.setInterval(load, 5000); const focus = () => load(); window.addEventListener("focus", focus); return () => { window.clearInterval(timer); window.removeEventListener("focus", focus); }; }, [load]);
  const toggle = async (id: number | null | undefined, current: boolean) => {
    if (!id) return;
    setData((value) => value ? { ...value, items: value.items.map((item) => item.id === id ? { ...item, is_purchased: !current } : item) } : value);
    try { setData(await publicShoppingListApi.updateItem(token, id, !current)); } catch { await load(); }
  };
  if (error) return <main className="mx-auto max-w-xl p-6"><div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-900"><h1 className="text-lg font-semibold">Không mở được danh sách</h1><p className="mt-2 text-sm">{error}</p></div></main>;
  if (!data) return <main className="mx-auto max-w-xl p-6 text-sm text-gray-600">Đang mở danh sách đi chợ…</main>;
  const done = data.items.filter((item) => item.is_purchased).length;
  const scopeLabel = data.day ? `Ngày ${data.day}${data.date ? ` · ${formatDate(data.date)}` : ""}` : "Toàn bộ thực đơn";
  return <main className="mx-auto min-h-screen max-w-xl bg-sand-50 p-4 sm:p-8"><header className="mb-5"><div className="flex items-center gap-2 text-brand-700"><ShoppingCart className="h-5 w-5" /><span className="font-bold">Smart Menu</span></div><h1 className="mt-4 text-2xl font-bold text-gray-900">Danh sách đi chợ – {data.plan_name}</h1><p className="mt-1 text-sm font-medium text-brand-700">{scopeLabel}</p><p className="mt-1 text-sm text-gray-600">{done}/{data.items.length} đã mua · {formatVND(data.total_estimated_cost)}</p><p className="mt-1 text-xs text-gray-500">Liên kết hết hạn lúc {new Date(data.expires_at).toLocaleString("vi-VN")}</p></header><section className="overflow-hidden rounded-2xl border border-sand-200 bg-white"><ul className="divide-y divide-sand-100">{data.items.map((item) => <li key={item.id} className="flex items-center gap-3 px-4 py-3"><input type="checkbox" checked={item.is_purchased} onChange={() => toggle(item.id, item.is_purchased)} className="h-4 w-4 rounded border-sand-300 text-brand-600 focus:ring-brand-400" /><span className={`flex-1 text-sm font-medium ${item.is_purchased ? "text-gray-400 line-through" : "text-gray-800"}`}>{item.name}</span><span className="text-xs text-gray-500">{formatNumber(item.quantity, 1)} {item.unit} · {formatVND(item.estimated_cost)}</span></li>)}</ul></section></main>;
}
