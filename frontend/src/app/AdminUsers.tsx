import { useEffect, useMemo, useState } from "react";
import { Users, Trash2, Shield, User as UserIcon, Plus, X, Search, Lock, Unlock } from "lucide-react";
import toast from "react-hot-toast";
import { getAllUsers, deleteUser, createUser, updateUser } from "../api/authApi";
import type { UserInfo } from "../api/authApi";

export default function AdminUsers() {
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterRole, setFilterRole] = useState<"all" | "user" | "admin">("all");
  const [showForm, setShowForm] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"user" | "admin">("user");
  // Lấy id của tài khoản đang đăng nhập từ JWT token
  const myId = (() => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) return null;
      return Number(JSON.parse(atob(token.split(".")[1])).sub);
    } catch { return null; }
  })();
  const load = () => {
    setLoading(true);
    getAllUsers()
      .then(setUsers)
      .catch((e) => toast.error(e instanceof Error ? e.message : "Không tải được"))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  // Lọc theo tìm kiếm + role
  const filtered = useMemo(() => {
    return users.filter((u) => {
      if (filterRole !== "all" && u.role !== filterRole) return false;
      if (search && !u.email.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [users, search, filterRole]);

  const handleCreate = async () => {
    if (!email.trim() || !password.trim()) { toast.error("Nhập email và mật khẩu"); return; }
    if (password.length < 6) { toast.error("Mật khẩu ít nhất 6 ký tự"); return; }
    try {
      await createUser(email.trim(), password, role);
      toast.success("Đã tạo tài khoản");
      setEmail(""); setPassword(""); setShowForm(false); load();
    } catch (e) { toast.error(e instanceof Error ? e.message : "Tạo thất bại"); }
  };

  const handleToggleRole = async (u: UserInfo) => {
    const newRole = u.role === "admin" ? "user" : "admin";
    if (!confirm(`Đổi vai trò ${u.email} thành ${newRole === "admin" ? "Quản trị" : "Người dùng"}?`)) return;
    try {
      await updateUser(u.id, { role: newRole });
      setUsers((prev) => prev.map((x) => x.id === u.id ? { ...x, role: newRole } : x));
      toast.success("Đã đổi vai trò");
    } catch (e) { toast.error(e instanceof Error ? e.message : "Đổi thất bại"); }
  };

  const handleToggleActive = async (u: UserInfo) => {
    try {
      await updateUser(u.id, { is_active: !u.is_active });
      setUsers((prev) => prev.map((x) => x.id === u.id ? { ...x, is_active: !u.is_active } : x));
      toast.success(u.is_active ? "Đã khoá tài khoản" : "Đã mở khoá tài khoản");
    } catch (e) { toast.error(e instanceof Error ? e.message : "Thao tác thất bại"); }
  };

  const handleDelete = async (u: UserInfo) => {
    if (!confirm(`Xoá tài khoản ${u.email}?`)) return;
    try {
      await deleteUser(u.id);
      setUsers((prev) => prev.filter((x) => x.id !== u.id));
      toast.success("Đã xoá");
    } catch (e) { toast.error(e instanceof Error ? e.message : "Xoá thất bại"); }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 md:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Đầu trang */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-emerald-700 flex items-center gap-2">
            <Users className="w-8 h-8" /> Quản Lý Tài Khoản
          </h1>
          <button onClick={() => setShowForm(!showForm)}
            className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-4 py-2.5 rounded-xl flex items-center gap-1 cursor-pointer transition-colors">
            {showForm ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
            {showForm ? "Đóng" : "Tạo tài khoản"}
          </button>
        </div>

        {/* Form tạo */}
        {showForm && (
          <div className="bg-white rounded-2xl border border-slate-100 p-5 mb-6 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
              <input type="email" placeholder="Email" value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200" />
              <input type="password" placeholder="Mật khẩu (≥6 ký tự)" value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200" />
              <select value={role} onChange={(e) => setRole(e.target.value as "user" | "admin")}
                className="bg-slate-50 border border-slate-200 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 cursor-pointer">
                <option value="user">Người dùng</option>
                <option value="admin">Quản trị</option>
              </select>
            </div>
            <button onClick={handleCreate}
              className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-6 py-2.5 rounded-xl cursor-pointer transition-colors">
              Lưu tài khoản
            </button>
          </div>
        )}

        {/* Tìm kiếm + lọc */}
        <div className="flex flex-col sm:flex-row gap-3 mb-5">
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input type="text" placeholder="Tìm theo email..."
              value={search} onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-white border border-slate-200 pl-11 pr-4 py-2.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200" />
          </div>
          <select value={filterRole} onChange={(e) => setFilterRole(e.target.value as "all" | "user" | "admin")}
            className="bg-white border border-slate-200 px-4 py-2.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 cursor-pointer">
            <option value="all">Tất cả vai trò</option>
            <option value="user">Người dùng</option>
            <option value="admin">Quản trị</option>
          </select>
        </div>

        <p className="text-sm text-slate-500 mb-3">Hiển thị {filtered.length} / {users.length} tài khoản</p>

        {/* Bảng */}
        {loading ? (
          <p className="text-center text-emerald-600 font-semibold py-12">Đang tải...</p>
        ) : filtered.length === 0 ? (
          <p className="text-center text-slate-500 py-12">Không có tài khoản nào khớp.</p>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-emerald-600 text-white">
                <tr>
                  <th className="p-4">ID</th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Vai trò</th>
                  <th className="p-4">Trạng thái</th>
                  <th className="p-4 text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <tr key={u.id} className={`border-t border-slate-100 hover:bg-slate-50 ${!u.is_active ? "opacity-60" : ""}`}>
                    <td className="p-4 text-slate-600">{u.id}</td>
                    <td className="p-4 font-medium text-slate-800">{u.email}</td>
                    <td className="p-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                        u.role === "admin" ? "bg-purple-100 text-purple-700" : "bg-slate-100 text-slate-600"
                      }`}>
                        {u.role === "admin" ? <Shield className="w-3 h-3" /> : <UserIcon className="w-3 h-3" />}
                        {u.role === "admin" ? "Quản trị" : "Người dùng"}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-bold ${
                        u.is_active ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
                      }`}>
                        {u.is_active ? "Đang hoạt động" : "Đã khoá"}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center justify-center gap-1">
                        <button onClick={() => handleToggleRole(u)}
                          disabled={u.id === myId}
                          title={u.id === myId ? "Không thể đổi vai trò chính mình" : "Đổi vai trò"}
                          className="text-purple-500 hover:bg-purple-50 p-2 rounded-lg cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed">
                          <Shield className="w-5 h-5" />
                        </button>
                        <button onClick={() => handleToggleActive(u)}
                          disabled={u.id === myId}
                          title={u.id === myId ? "Không thể khoá chính mình" : (u.is_active ? "Khoá tài khoản" : "Mở khoá")}
                          className={`p-2 rounded-lg cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed ${u.is_active ? "text-orange-500 hover:bg-orange-50" : "text-emerald-500 hover:bg-emerald-50"}`}>
                          {u.is_active ? <Lock className="w-5 h-5" /> : <Unlock className="w-5 h-5" />}
                        </button>
                        <button onClick={() => handleDelete(u)}
                          disabled={u.role === "admin" || u.id === myId}
                          title={u.id === myId ? "Không thể xoá chính mình" : (u.role === "admin" ? "Không thể xoá admin" : "Xoá")}
                          className="text-red-500 hover:bg-red-50 p-2 rounded-lg cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed">
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}