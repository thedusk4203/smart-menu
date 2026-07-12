import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../../context/AuthContext";
import { Button, TextField } from "../../components/ui";
import { ApiError } from "../../lib/apiClient";

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  const passwordError = confirm && confirm !== password ? "Mật khẩu xác nhận không khớp" : undefined;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      toast.error("Mật khẩu xác nhận không khớp");
      return;
    }
    if (password.length < 8) {
      toast.error("Mật khẩu cần tối thiểu 8 ký tự");
      return;
    }
    setLoading(true);
    try {
      await register({ email, password, full_name: fullName || undefined });
      toast.success("Tạo tài khoản thành công!");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Tạo tài khoản</h1>
      <p className="mt-1 text-sm text-gray-500">Bắt đầu hành trình ăn uống khoa học.</p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <TextField
          label="Họ và tên"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Nguyễn Văn A"
        />
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          required
          minLength={8}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="ban@email.com"
        />
        <TextField
          label="Mật khẩu"
          type="password"
          autoComplete="new-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Tối thiểu 8 ký tự"
        />
        <TextField
          label="Xác nhận mật khẩu"
          type="password"
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={passwordError}
          placeholder="Nhập lại mật khẩu"
        />
        <Button type="submit" loading={loading} className="w-full">
          Đăng ký
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        Đã có tài khoản?{" "}
        <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
          Đăng nhập
        </Link>
      </p>
    </div>
  );
}
