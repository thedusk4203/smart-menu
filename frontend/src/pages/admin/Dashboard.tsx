import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight, ChefHat, CircleAlert, Clock3, FileUp, Salad, ShieldCheck, Users,
} from "lucide-react";
import { adminApi } from "../../api/adminApi";
import { useAuth } from "../../context/AuthContext";
import { toUserFeedback, type UserFeedback } from "../../lib/userFeedback";
import { formatDate } from "../../lib/format";
import { PageHeader } from "../../components/ui";
import { AdminErrorState, AdminTableSkeleton } from "../../components/admin/AdminStates";
import type { AdminDashboardSummary } from "../../types/admin";

interface MetricProps {
  label: string;
  value: number;
  note: string;
  icon: typeof Users;
  to: string;
}

function Metric({ label, value, note, icon: Icon, to }: MetricProps) {
  return (
    <Link
      to={to}
      className="group min-w-0 px-5 py-4 transition hover:bg-sand-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-400"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-600">{label}</p>
          <p className="mt-2 text-2xl font-bold tabular-nums text-gray-950">{value.toLocaleString("vi-VN")}</p>
          <p className="mt-1 truncate text-xs text-gray-500">{note}</p>
        </div>
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700 group-hover:bg-brand-100">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>
    </Link>
  );
}

export function AdminDashboard() {
  const { user } = useAuth();
  const [data, setData] = useState<AdminDashboardSummary | null>(null);
  const [error, setError] = useState<UserFeedback | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await adminApi.dashboard());
    } catch (err) {
      setError(toUserFeedback(err, "admin_action", "admin"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const isSuper = user?.role === "admin" || user?.role === "super_admin";

  return (
    <div>
      <PageHeader
        title="Tổng quan quản trị"
        description="Theo dõi dữ liệu ảnh hưởng trực tiếp tới chất lượng thực đơn."
        actions={
          <Link
            to="/admin/imports"
            className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-brand-700 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2"
          >
            <FileUp className="h-4 w-4" aria-hidden="true" /> Nhập dữ liệu (import)
          </Link>
        }
      />

      {loading ? (
        <div className="overflow-hidden rounded-2xl border border-sand-200 bg-white"><AdminTableSkeleton rows={8} /></div>
      ) : error || !data ? (
        <div className="rounded-2xl border border-sand-200 bg-white">
          <AdminErrorState feedback={error ?? undefined} onRetry={load} />
        </div>
      ) : (
        <>
          <section aria-label="Số liệu chính" className="grid overflow-hidden rounded-2xl border border-sand-200 bg-white shadow-sm sm:grid-cols-2 xl:grid-cols-4 sm:[&>*:nth-child(odd)]:border-r xl:[&>*]:border-r xl:[&>*:last-child]:border-r-0 [&>*]:border-b [&>*]:border-sand-200 xl:[&>*]:border-b-0">
            {isSuper && (
              <Metric label="Người dùng" value={data.users_total} note={`${data.users_locked} tài khoản bị khóa`} icon={Users} to="/admin/users" />
            )}
            <Metric label="Nguyên liệu" value={data.ingredients_total} note={`${data.ingredients_active} đang được sử dụng`} icon={Salad} to="/admin/ingredients" />
            <Metric label="Món thành phần" value={data.dishes_total} note={`${data.incomplete_dishes} món cần bổ sung`} icon={ChefHat} to="/admin/dishes" />
            <Metric label="Món sẵn sàng để lập thực đơn" value={data.planner_ready_dishes} note={`Sáng ${data.breakfast_count} · Tinh bột ${data.staple_count} · Mặn ${data.savory_count} · Rau/Canh ${data.vegetable_count + data.soup_count}`} icon={ChefHat} to="/admin/dishes" />
          </section>

          <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,0.7fr)]">
            <section className="overflow-hidden rounded-2xl border border-sand-200 bg-white shadow-sm" aria-labelledby="quality-title">
              <div className="flex items-start justify-between gap-4 border-b border-sand-200 px-5 py-4">
                <div>
                  <h2 id="quality-title" className="font-semibold text-gray-950">Việc cần xử lý</h2>
                  <p className="mt-1 text-sm text-gray-600">Các lỗi có thể làm hệ thống tính sai hoặc không tìm được bữa phù hợp.</p>
                </div>
                <span className="rounded-full bg-red-50 px-3 py-1 text-sm font-semibold tabular-nums text-red-800">
                  {data.open_quality_issues}
                </span>
              </div>
              <div className="divide-y divide-sand-100">
                {[
                  ["Nguyên liệu thiếu giá", data.missing_price, "/admin/quality?code=missing_price", "Không thể tính đúng chi phí món"],
                  ["Nguyên liệu thiếu dinh dưỡng", data.missing_nutrition, "/admin/quality?code=missing_nutrition", "Làm thiếu tổng năng lượng và các chất chính"],
                  ["Cần kiểm tra quy đổi", data.missing_conversion, "/admin/quality?code=missing_conversion", "Đơn vị khác gram nhưng hệ số đang bằng 1"],
                  ["Món thiếu công thức hoặc dữ liệu", data.incomplete_dishes, "/admin/quality?entity_type=dish", "Cần bổ sung trước khi dùng để lập thực đơn"],
                  ["Tên có khả năng trùng", data.duplicate_names, "/admin/quality?code=duplicate_name", "Kiểm tra trước khi gộp dữ liệu"],
                ].map(([label, value, to, detail]) => (
                  <Link key={String(label)} to={String(to)} className="group flex min-h-16 items-center gap-4 px-5 py-3 transition hover:bg-sand-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-400">
                    <CircleAlert className={`h-5 w-5 shrink-0 ${Number(value) > 0 ? "text-red-600" : "text-brand-600"}`} aria-hidden="true" />
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-900">{label}</p>
                      <p className="truncate text-sm text-gray-500">{detail}</p>
                    </div>
                    <span className="font-semibold tabular-nums text-gray-900">{value}</span>
                    <ArrowRight className="h-4 w-4 text-gray-400 transition group-hover:translate-x-0.5 group-hover:text-brand-700" aria-hidden="true" />
                  </Link>
                ))}
              </div>
            </section>

            <aside className="space-y-4">
              <div className="rounded-2xl border border-brand-200 bg-brand-50 p-5">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-brand-700 shadow-sm">
                  <ShieldCheck className="h-5 w-5" aria-hidden="true" />
                </span>
                <h2 className="mt-4 font-semibold text-brand-950">Dữ liệu chuẩn (canonical)</h2>
                <p className="mt-1 text-sm leading-6 text-brand-900">
                  Hệ thống ghép trực tiếp món thành phần (dish) theo vai trò dinh dưỡng. Mọi thay đổi hợp lệ tại đây được dùng ở lần tạo thực đơn tiếp theo.
                </p>
              </div>
              <div className="rounded-2xl border border-sand-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-900">
                  <Clock3 className="h-4 w-4 text-gray-500" aria-hidden="true" /> Lần nhập dữ liệu (import) gần nhất
                </div>
                <p className="mt-3 text-sm text-gray-600">
                  {data.last_import_at ? formatDate(data.last_import_at) : "Chưa có lần nhập dữ liệu nào."}
                </p>
                <Link to="/admin/imports" className="mt-4 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-brand-700 hover:text-brand-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400">
                  Xem lịch sử <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </Link>
              </div>
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
