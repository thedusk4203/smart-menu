import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { Eye, EyeOff } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { Button, TextField } from "../../components/ui";
import { ApiError } from "../../lib/apiClient";
import { GoogleLoginButton } from "../../components/auth/GoogleLoginButton";

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
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
          type={showPassword ? "text" : "password"}
          autoComplete="new-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Tối thiểu 8 ký tự"
          trailingAction={
            <button
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
              className="rounded-md p-1 text-gray-400 transition-colors hover:text-brand-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
              aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              title={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          }
        />
        <TextField
          label="Xác nhận mật khẩu"
          type={showConfirm ? "text" : "password"}
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={passwordError}
          placeholder="Nhập lại mật khẩu"
          trailingAction={
            <button
              type="button"
              onClick={() => setShowConfirm((visible) => !visible)}
              className="rounded-md p-1 text-gray-400 transition-colors hover:text-brand-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
              aria-label={showConfirm ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              title={showConfirm ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
            >
              {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          }
        />
        <Button type="submit" loading={loading} className="w-full">
          Đăng ký
        </Button>
      </form>

      <GoogleLoginButton onAuthenticated={() => {
        toast.success("Tạo tài khoản thành công!");
        navigate("/dashboard", { replace: true });
      }} />

      <p className="mt-6 text-center text-sm text-gray-500">
        Đã có tài khoản?{" "}
        <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
          Đăng nhập
        </Link>
      </p>
    </div>
  );
}
