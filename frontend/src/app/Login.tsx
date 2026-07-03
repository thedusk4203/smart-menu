import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { login } from "../api/authApi";
import toast from "react-hot-toast";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      toast.error("Vui lòng nhập email và mật khẩu");
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Đăng nhập thành công!");
      navigate("/create-menu");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-400 via-green-500 to-teal-600 flex items-center justify-center p-4">
      <div className="bg-white/80 backdrop-blur-md p-8 rounded-3xl shadow-2xl w-full max-w-sm border border-white/50">
        <h2 className="text-3xl font-bold text-center text-green-700 mb-8">Smart Menu</h2>

        <div className="mb-5">
          <label className="block text-gray-700 text-sm font-bold mb-2">Email của bạn</label>
          <input
            type="email"
            placeholder="nguyentheduc@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border-none bg-white/90 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-green-300 transition-all shadow-inner"
          />
        </div>

        <div className="mb-8">
          <label className="block text-gray-700 text-sm font-bold mb-2">Mật khẩu</label>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            className="w-full border-none bg-white/90 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-green-300 transition-all shadow-inner"
          />
        </div>

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white font-bold py-3.5 rounded-xl transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Đang đăng nhập..." : "Vào Hệ Thống"}
        </button>

        <p className="text-center text-sm text-gray-600 mt-6">
          Chưa có tài khoản?{" "}
          <span onClick={() => navigate("/register")} className="text-green-700 font-bold cursor-pointer hover:underline">
            Đăng ký ngay
          </span>
        </p>
      </div>
    </div>
  );
}