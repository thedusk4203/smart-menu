import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import toast from "react-hot-toast";
import { Plus, Pencil, Trash2, CheckCircle2, XCircle } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { userApi } from "../../api/userApi";
import {
  PageHeader, Card, Button, Badge, Modal, TextField, SelectField, FullPageSpinner,
} from "../../components/ui";
import { ROLE_LABELS } from "../../lib/labels";
import { ApiError } from "../../lib/apiClient";
import type { User, UserRole } from "../../types";

const ROLE_OPTIONS = Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }));
const STATUS_OPTIONS = [
  { value: "true", label: "Đang hoạt động" },
  { value: "false", label: "Đã khoá" },
];

interface FormState {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  is_active: string;
}

const EMPTY_FORM: FormState = {
  email: "", password: "", full_name: "", role: "user", is_active: "true",
};

export function Users() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const list = await userApi.list();
      setUsers(list);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  };

  const openEdit = (u: User) => {
    setEditingId(u.id);
    setForm({
      email: u.email,
      password: "",
      full_name: "",
      role: u.role,
      is_active: String(u.is_active),
    });
    setModalOpen(true);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingId != null) {
        await userApi.update(editingId, {
          email: form.email || undefined,
          password: form.password || undefined,
          role: form.role,
          is_active: form.is_active === "true",
        });
        toast.success("Đã cập nhật người dùng.");
      } else {
        await userApi.create({
          email: form.email,
          password: form.password,
          full_name: form.full_name || undefined,
          role: form.role,
        });
        toast.success("Đã tạo người dùng.");
      }
      setModalOpen(false);
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (u: User) => {
    if (me?.id === u.id) {
      toast.error("Không thể xoá chính tài khoản của bạn.");
      return;
    }
    if (!window.confirm(`Xoá người dùng "${u.email}"?`)) return;
    try {
      await userApi.remove(u.id);
      setUsers((prev) => prev.filter((x) => x.id !== u.id));
      toast.success("Đã xoá người dùng.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    }
  };

  if (loading) return <FullPageSpinner />;

  return (
    <div>
      <PageHeader
        title="Quản trị người dùng"
        description="Quản lý tài khoản, phân quyền và trạng thái hoạt động."
        actions={
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" /> Thêm người dùng
          </Button>
        }
      />

      <Card bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-sand-200 text-left text-xs uppercase tracking-wide text-gray-400">
                <th className="px-5 py-3 font-medium">ID</th>
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Vai trò</th>
                <th className="px-5 py-3 font-medium">Trạng thái</th>
                <th className="px-5 py-3 text-right font-medium">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sand-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-sand-50">
                  <td className="px-5 py-3 text-gray-500">#{u.id}</td>
                  <td className="px-5 py-3">
                    <span className="font-medium text-gray-800">{u.email}</span>
                    {me?.id === u.id && (
                      <Badge className="ml-2 bg-brand-100 text-brand-700">Bạn</Badge>
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <Badge
                      className={u.role === "admin" ? "bg-indigo-100 text-indigo-700" : "bg-sand-200 text-gray-700"}
                    >
                      {ROLE_LABELS[u.role]}
                    </Badge>
                  </td>
                  <td className="px-5 py-3">
                    {u.is_active ? (
                      <span className="inline-flex items-center gap-1 text-brand-600">
                        <CheckCircle2 className="h-4 w-4" /> Hoạt động
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-gray-400">
                        <XCircle className="h-4 w-4" /> Đã khoá
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => openEdit(u)}
                        className="rounded-lg p-1.5 text-gray-400 transition hover:bg-brand-50 hover:text-brand-600"
                        aria-label="Sửa"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => remove(u)}
                        disabled={me?.id === u.id}
                        className="rounded-lg p-1.5 text-gray-400 transition hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40"
                        aria-label="Xoá"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingId != null ? "Sửa người dùng" : "Thêm người dùng"}
        footer={
          <>
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Huỷ
            </Button>
            <Button form="user-form" type="submit" loading={saving}>
              Lưu
            </Button>
          </>
        }
      >
        <form id="user-form" onSubmit={submit} className="space-y-4">
          <TextField
            label="Email"
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          {editingId == null && (
            <TextField
              label="Họ và tên"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          )}
          <TextField
            label={editingId != null ? "Mật khẩu mới (để trống nếu không đổi)" : "Mật khẩu"}
            type="password"
            required={editingId == null}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              label="Vai trò"
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}
              options={ROLE_OPTIONS}
            />
            {editingId != null && (
              <SelectField
                label="Trạng thái"
                value={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.value })}
                options={STATUS_OPTIONS}
              />
            )}
          </div>
        </form>
      </Modal>
    </div>
  );
}
