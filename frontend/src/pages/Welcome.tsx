import { Link, Navigate } from "react-router-dom";
import {
  Leaf, Wallet, Flame, Salad, ShoppingCart, Sparkles, UtensilsCrossed, ArrowRight,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { FullPageSpinner } from "../components/ui";

const FEATURES = [
  { icon: Wallet, title: "Bám sát ngân sách", desc: "Lập thực đơn vừa túi tiền, kiểm soát chi phí từng ngày." },
  { icon: Flame, title: "Đúng nhu cầu dinh dưỡng", desc: "Ước tính năng lượng, đạm, chất béo và tinh bột theo mục tiêu cá nhân." },
  { icon: UtensilsCrossed, title: "Thực đơn tự động", desc: "Tạo thực đơn nhiều ngày chỉ với vài thao tác." },
  { icon: Salad, title: "Nguyên liệu & món ăn", desc: "Kho nguyên liệu và món ăn phong phú, dễ tra cứu." },
  { icon: ShoppingCart, title: "Danh sách đi chợ", desc: "Tự gom nguyên liệu từ thực đơn, tiện in mang theo." },
  { icon: Sparkles, title: "Trợ lý Menuto", desc: "Gợi ý đổi món và giải đáp dinh dưỡng." },
];

export function Welcome() {
  const { user, loading } = useAuth();
  if (loading) return <FullPageSpinner />;
  if (user) return <Navigate to="/dashboard" replace />;

  return (
    <div className="bg-hero min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Leaf className="h-5 w-5" />
          </span>
          <span className="text-lg font-bold text-gray-900">Smart Menu</span>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/login"
            className="rounded-xl px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-white/60"
          >
            Đăng nhập
          </Link>
          <Link
            to="/register"
            className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700"
          >
            Bắt đầu
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-4 pb-8 pt-12 text-center sm:pt-20">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-700">
          <Leaf className="h-3.5 w-3.5" /> Ăn ngon, đủ chất, đúng ngân sách
        </span>
        <h1 className="mt-5 text-4xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-5xl">
          Lập thực đơn thông minh<br />
          <span className="text-brand-600">theo ngân sách &amp; dinh dưỡng</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base text-gray-600 sm:text-lg">
          Smart Menu giúp bạn xây dựng thực đơn cân bằng dinh dưỡng, phù hợp mục tiêu sức khỏe và
          tối ưu chi phí — chỉ trong vài phút.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            to="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700"
          >
            Tạo tài khoản miễn phí <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 rounded-xl border border-sand-200 bg-white px-6 py-3 text-sm font-semibold text-gray-700 transition hover:bg-sand-100"
          >
            Tôi đã có tài khoản
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-20">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-2xl border border-sand-200 bg-white/80 p-5 shadow-sm">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-100 text-brand-600">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-3 font-semibold text-gray-800">{f.title}</h3>
              <p className="mt-1 text-sm text-gray-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
