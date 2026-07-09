import { useNavigate } from "react-router-dom";
import { ChefHat, Wallet, HeartPulse, Sparkles, UserPlus, SlidersHorizontal, UtensilsCrossed } from "lucide-react";

export default function Welcome() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-400 via-green-500 to-teal-600 text-white">
      {/* ── Phần đầu (Hero) ── */}
      <div className="max-w-3xl mx-auto text-center px-4 pt-16 pb-12">
        <div className="flex justify-center mb-6">
          <div className="bg-white/20 backdrop-blur-md p-5 rounded-3xl shadow-lg">
            <ChefHat className="w-16 h-16 text-white" />
          </div>
        </div>

        <h1 className="text-5xl md:text-6xl font-bold mb-4 tracking-tight">Smart Menu</h1>
        <p className="text-xl text-white/90 mb-3">Lập thực đơn theo ngân sách & dinh dưỡng</p>
        <p className="text-white/70 mb-10 max-w-md mx-auto leading-relaxed">
          Ứng dụng giúp bạn lên thực đơn hằng tuần vừa đủ chất, vừa hợp túi tiền —
          nhanh chóng và thông minh.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => navigate("/login")}
            className="bg-white text-emerald-600 font-bold py-3.5 px-10 rounded-xl shadow-lg transform hover:-translate-y-1 active:scale-95 transition-all duration-300"
          >
            Đăng Nhập
          </button>
          <button
            onClick={() => navigate("/register")}
            className="bg-white/20 backdrop-blur-md border-2 border-white/50 text-white font-bold py-3.5 px-10 rounded-xl transform hover:-translate-y-1 active:scale-95 transition-all duration-300"
          >
            Đăng Ký
          </button>
        </div>
      </div>

      {/* ── Phần tính năng (nền trắng) ── */}
      <div className="bg-white text-gray-800 rounded-t-[3rem] px-4 py-14">
        <div className="max-w-5xl mx-auto">
          {/* 3 tính năng nổi bật */}
          <h2 className="text-3xl font-bold text-center text-emerald-700 mb-2">Vì sao chọn Smart Menu?</h2>
          <p className="text-center text-gray-500 mb-10">Ba lợi ích chính giúp bữa ăn của bạn tốt hơn mỗi ngày</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            <div className="bg-emerald-50 rounded-2xl p-6 text-center">
              <div className="bg-emerald-500 w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Wallet className="w-7 h-7 text-white" />
              </div>
              <h3 className="font-bold text-lg mb-2">Tiết kiệm chi phí</h3>
              <p className="text-sm text-gray-600 leading-relaxed">Thực đơn luôn nằm trong ngân sách bạn đặt ra, không lo vượt tiền chợ.</p>
            </div>
            <div className="bg-teal-50 rounded-2xl p-6 text-center">
              <div className="bg-teal-500 w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <HeartPulse className="w-7 h-7 text-white" />
              </div>
              <h3 className="font-bold text-lg mb-2">Đủ dinh dưỡng</h3>
              <p className="text-sm text-gray-600 leading-relaxed">Cân đối calo và đạm theo mục tiêu: giảm cân, tăng cơ hay duy trì.</p>
            </div>
            <div className="bg-green-50 rounded-2xl p-6 text-center">
              <div className="bg-green-500 w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-7 h-7 text-white" />
              </div>
              <h3 className="font-bold text-lg mb-2">Nhanh gọn</h3>
              <p className="text-sm text-gray-600 leading-relaxed">Lên thực đơn cả tuần chỉ trong vài phút, không cần nghĩ hôm nay ăn gì.</p>
            </div>
          </div>

          {/* Cách dùng 3 bước */}
          <h2 className="text-3xl font-bold text-center text-emerald-700 mb-2">Cách sử dụng</h2>
          <p className="text-center text-gray-500 mb-10">Chỉ 3 bước đơn giản để có thực đơn phù hợp</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="relative bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <div className="absolute -top-4 left-6 bg-emerald-500 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">1</div>
              <UserPlus className="w-8 h-8 text-emerald-500 mt-3 mb-3" />
              <h3 className="font-bold mb-2">Tạo tài khoản</h3>
              <p className="text-sm text-gray-600 leading-relaxed">Đăng ký và điền hồ sơ: chiều cao, cân nặng, mục tiêu thể chất của bạn.</p>
            </div>
            <div className="relative bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <div className="absolute -top-4 left-6 bg-teal-500 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">2</div>
              <SlidersHorizontal className="w-8 h-8 text-teal-500 mt-3 mb-3" />
              <h3 className="font-bold mb-2">Nhập ngân sách</h3>
              <p className="text-sm text-gray-600 leading-relaxed">Cho biết số tiền dự kiến và các nguyên liệu bạn dị ứng hoặc không ăn.</p>
            </div>
            <div className="relative bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
              <div className="absolute -top-4 left-6 bg-green-500 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">3</div>
              <UtensilsCrossed className="w-8 h-8 text-green-500 mt-3 mb-3" />
              <h3 className="font-bold mb-2">Nhận thực đơn</h3>
              <p className="text-sm text-gray-600 leading-relaxed">Hệ thống tự lập thực đơn phù hợp, bạn xem và lưu lại để dùng dần.</p>
            </div>
          </div>

          {/* Nút kêu gọi cuối trang */}
          <div className="text-center mt-14">
            <button
              onClick={() => navigate("/register")}
              className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold py-4 px-12 rounded-xl shadow-lg transform hover:-translate-y-1 active:scale-95 transition-all duration-300"
            >
              Bắt đầu ngay
            </button>
          </div>
        </div>
      </div>

      {/* ── Chân trang ── */}
      <div className="bg-white text-center text-gray-400 text-sm pb-8">
        © 2026 Smart Menu — Đồ án tốt nghiệp
      </div>
    </div>
  );
}