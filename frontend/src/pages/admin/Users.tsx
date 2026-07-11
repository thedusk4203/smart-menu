import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { LockKeyhole, Plus, Search, ShieldCheck, UnlockKeyhole, UserPlus } from "lucide-react";
import toast from "react-hot-toast";
import { adminApi } from "../../api/adminApi";
import { useAuth } from "../../context/AuthContext";
import { ApiError } from "../../lib/apiClient";
import { ROLE_LABELS } from "../../lib/labels";
import { Button, Card, Modal, PageHeader, SelectField, TextField } from "../../components/ui";
import { AdminEmptyState, AdminErrorState, AdminTableSkeleton } from "../../components/admin/AdminStates";
import { AdminPagination } from "../../components/admin/AdminPagination";
import { DataStateBadge } from "../../components/admin/QualityBadges";
import type { AdminUser } from "../../types/admin";
import type { UserRole } from "../../types";

const LIMIT = 20;
const ROLE_OPTIONS = [
  { value: "user", label: ROLE_LABELS.user },
  { value: "data_editor", label: ROLE_LABELS.data_editor },
  { value: "super_admin", label: ROLE_LABELS.super_admin },
];

export function Users() {
  const { user: me } = useAuth();
  const [items, setItems] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", full_name: "", role: "user" as UserRole });

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const page = await adminApi.users({ search: search.trim() || undefined, role, is_active: status || undefined, limit: LIMIT, offset });
      setItems(page.items);
      setTotal(page.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải danh sách người dùng.");
    } finally {
      setLoading(false);
    }
  }, [offset, role, search, status]);

  useEffect(() => {
    const timer = window.setTimeout(load, 250);
    return () => window.clearTimeout(timer);
  }, [load]);

  const changeRole = async (target: AdminUser, nextRole: UserRole) => {
    setSavingId(target.id);
    try {
      const updated = await adminApi.updateUserRole(target.id, nextRole);
      setItems((current) => current.map((item) => item.id === target.id ? updated : item));
      toast.success(`Đã đổi vai trò của ${target.email}.`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể đổi vai trò.");
    } finally {
      setSavingId(null);
    }
  };

  const changeStatus = async (target: AdminUser) => {
    setSavingId(target.id);
    try {
      const updated = await adminApi.updateUserStatus(target.id, !target.is_active);
      setItems((current) => current.map((item) => item.id === target.id ? updated : item));
      toast.success(updated.is_active ? "Đã mở khóa tài khoản." : "Đã khóa tài khoản.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể cập nhật trạng thái.");
    } finally {
      setSavingId(null);
    }
  };

  const create = async (event: FormEvent) => {
    event.preventDefault();
    setCreating(true);
    try {
      const created = await adminApi.createUser({
        email: form.email,
        password: form.password,
        full_name: form.full_name || undefined,
        role: form.role,
      });
      setItems((current) => [created, ...current]);
      setTotal((value) => value + 1);
      setCreateOpen(false);
      setForm({ email: "", password: "", full_name: "", role: "user" });
      toast.success("Đã tạo người dùng mới.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể tạo người dùng.");
    } finally {
      setCreating(false);
    }
  };

  const isSuper = me?.role === "admin" || me?.role === "super_admin";
  if (!isSuper) {
    return (
      <div className="rounded-2xl border border-sand-200 bg-white">
        <AdminEmptyState icon={ShieldCheck} title="Khu vực dành cho quản trị viên hệ thống" description="Bạn vẫn có thể quản lý dữ liệu nguyên liệu, món và chất lượng dữ liệu." />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Người dùng"
        description="Tạo tài khoản, phân quyền và khóa/mở khóa truy cập một cách an toàn."
        actions={<Button onClick={() => setCreateOpen(true)}><Plus className="h-4 w-4" /> Tạo người dùng</Button>}
      />

      <div className="mb-4 grid gap-3 rounded-2xl border border-sand-200 bg-white p-3 shadow-sm md:grid-cols-[minmax(0,1fr)_11rem_11rem]">
        <label className="relative block">
          <span className="sr-only">Tìm người dùng</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" aria-hidden="true" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setOffset(0); }} placeholder="Tìm email hoặc họ tên" className="min-h-11 w-full rounded-xl border border-sand-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </label>
        <SelectField value={role} onChange={(e) => { setRole(e.target.value); setOffset(0); }} placeholder="Tất cả vai trò" options={ROLE_OPTIONS} />
        <SelectField value={status} onChange={(e) => { setStatus(e.target.value); setOffset(0); }} placeholder="Tất cả trạng thái" options={[{ value: "true", label: "Đang hoạt động" }, { value: "false", label: "Đã khóa" }]} />
      </div>

      <Card bodyClassName="p-0">
        {loading ? <AdminTableSkeleton /> : error ? <AdminErrorState message={error} onRetry={load} /> : items.length === 0 ? (
          <AdminEmptyState icon={UserPlus} title="Không tìm thấy người dùng" description="Thử đổi từ khóa hoặc bộ lọc để xem dữ liệu khác." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[760px] w-full text-left text-sm">
              <thead className="bg-sand-50 text-xs text-gray-600">
                <tr className="border-b border-sand-200">
                  <th className="px-5 py-3 font-semibold">Người dùng</th>
                  <th className="px-5 py-3 font-semibold">Vai trò</th>
                  <th className="px-5 py-3 font-semibold">Trạng thái</th>
                  <th className="px-5 py-3 text-right font-semibold">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sand-100">
                {items.map((item) => {
                  const isMe = item.id === me?.id;
                  const waiting = savingId === item.id;
                  return (
                    <tr key={item.id} className="hover:bg-sand-50">
                      <td className="px-5 py-3.5">
                        <p className="font-semibold text-gray-900">{item.email}</p>
                        <p className="mt-0.5 text-xs text-gray-600">{item.full_name || "Chưa có họ tên"}{isMe ? " · Bạn" : ""}</p>
                      </td>
                      <td className="px-5 py-3.5">
                        <select aria-label={`Vai trò của ${item.email}`} value={item.role === "admin" ? "super_admin" : item.role} disabled={isMe || waiting} onChange={(e) => changeRole(item, e.target.value as UserRole)} className="min-h-10 rounded-lg border border-sand-200 bg-white px-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:cursor-not-allowed disabled:bg-sand-100">
                          {ROLE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                        </select>
                      </td>
                      <td className="px-5 py-3.5">
                        <DataStateBadge state={item.is_active ? "ok" : "warning"} label={item.is_active ? "Hoạt động" : "Đã khóa"} />
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button type="button" disabled={isMe || waiting} onClick={() => changeStatus(item)} className="inline-flex min-h-10 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-gray-700 transition hover:bg-sand-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:cursor-not-allowed disabled:opacity-50">
                          {item.is_active ? <LockKeyhole className="h-4 w-4" aria-hidden="true" /> : <UnlockKeyhole className="h-4 w-4" aria-hidden="true" />}
                          {item.is_active ? "Khóa" : "Mở khóa"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {!loading && !error && <AdminPagination offset={offset} limit={LIMIT} total={total} onChange={setOffset} />}
      </Card>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Tạo người dùng" footer={<><Button variant="ghost" onClick={() => setCreateOpen(false)}>Hủy</Button><Button form="create-admin-user" type="submit" loading={creating}>Tạo người dùng</Button></>}>
        <form id="create-admin-user" onSubmit={create} className="space-y-4">
          <TextField label="Email" type="email" required autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <TextField label="Họ và tên" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          <TextField label="Mật khẩu" type="password" required minLength={8} autoComplete="new-password" hint="Ít nhất 8 ký tự." value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <SelectField label="Vai trò" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })} options={ROLE_OPTIONS} />
        </form>
      </Modal>
    </div>
  );
}
