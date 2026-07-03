import { useNavigate } from "react-router-dom";
import { ChefHat, Wallet, HeartPulse, Sparkles } from "lucide-react";

export default function Welcome() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-400 via-green-500 to-teal-600 flex flex-col items-center justify-center p-4 text-white">
      <div className="max-w-2xl w-full text-center">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <div className="bg-white/20 backdrop-blur-md p-5 rounded-3xl">
            <ChefHat className="w-16 h-16 text-white" />
          </div>
        </div>

        <h1 className="text-5xl md:text-6xl font-bold mb-4">Smart Menu</h1>
        <p className="text-xl text-white/90 mb-2">Lập thực đơn theo ngân sách & dinh dưỡng</p>
        <p className="text-white/70 mb-10 max-w-md mx-auto">
          Ứng dụng giúp bạn lên thực đơn hằng tuần vừa đủ chất, vừa hợp túi tiền — nhanh chóng và thông minh.
        </p>

        {/* 3 điểm nổi bật */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
          <div className="bg-white/15 backdrop-blur-md rounded-2xl p-5">
            <Wallet className="w-8 h-8 mx-auto mb-2" />
            <h3 className="font-bold mb-1">Tiết kiệm</h3>
            <p className="text-sm text-white/80">Thực đơn trong ngân sách bạn đặt ra</p>
          </div>
          <div className="bg-white/15 backdrop-blur-md rounded-2xl p-5">
            <HeartPulse className="w-8 h-8 mx-auto mb-2" />
            <h3 className="font-bold mb-1">Đủ dinh dưỡng</h3>
            <p className="text-sm text-white/80">Cân đối calo, đạm theo mục tiêu</p>
          </div>
          <div className="bg-white/15 backdrop-blur-md rounded-2xl p-5">
            <Sparkles className="w-8 h-8 mx-auto mb-2" />
            <h3 className="font-bold mb-1">Nhanh gọn</h3>
            <p className="text-sm text-white/80">Lên thực đơn cả tuần chỉ vài phút</p>
          </div>
        </div>

        {/* Nút hành động */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => navigate("/login")}
            className="bg-white text-emerald-600 font-bold py-3.5 px-8 rounded-xl shadow-lg transform hover:-translate-y-1 active:scale-95 transition-all duration-300"
          >
            Đăng Nhập
          </button>
          <button
            onClick={() => navigate("/register")}
            className="bg-white/20 backdrop-blur-md border-2 border-white/50 text-white font-bold py-3.5 px-8 rounded-xl transform hover:-translate-y-1 active:scale-95 transition-all duration-300"
          >
            Đăng Ký
          </button>
        </div>
      </div>
    </div>
  );
}