import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { Eye, EyeOff } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { Button, TextField } from "../../components/ui";
import { ApiError } from "../../lib/apiClient";
import { isAdminRole } from "../../lib/roles";
import type { User } from "../../types";
import { GoogleLoginButton } from "../../components/auth/GoogleLoginButton";

interface LocationState {
  from?: { pathname?: string };
}

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const getRedirectTo = (user: User) => {
    const from = (location.state as LocationState | null)?.from?.pathname;
    if (isAdminRole(user.role)) return from?.startsWith("/admin") ? from : "/admin";
    return from && !from.startsWith("/admin") ? from : "/dashboard";
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success("Đăng nhập thành công!");
      navigate(getRedirectTo(user), { replace: true });
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Đăng nhập</h1>
      <p className="mt-1 text-sm text-gray-500">Chào mừng trở lại với Smart Menu.</p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="ban@email.com"
        />
        <TextField
          label="Mật khẩu"
          type={showPassword ? "text" : "password"}
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
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
        <Button type="submit" loading={loading} className="w-full">
          Đăng nhập
        </Button>
      </form>

      <GoogleLoginButton onAuthenticated={(user) => {
        toast.success("Đăng nhập thành công!");
        navigate(getRedirectTo(user), { replace: true });
      }} />

      <p className="mt-6 text-center text-sm text-gray-500">
        Chưa có tài khoản?{" "}
        <Link to="/register" className="font-medium text-brand-600 hover:text-brand-700">
          Đăng ký ngay
        </Link>
      </p>
    </div>
  );
}
