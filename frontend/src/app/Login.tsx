import { useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();

  return (
    /* Nền màu chuyển sắc (Gradient) */
    <div className="min-h-screen bg-gradient-to-br from-emerald-400 via-green-500 to-teal-600 flex items-center justify-center p-4">
      
      {/* Khung hiệu ứng kính (Glassmorphism): nền trắng hơi trong suốt, làm mờ phía sau */}
      <div className="bg-white/80 backdrop-blur-md p-8 rounded-3xl shadow-2xl w-full max-w-sm border border-white/50">
        
        <h2 className="text-3xl font-bold text-center text-green-700 mb-8">
          Smart Menu
        </h2>

        <div className="mb-5">
          <label className="block text-gray-700 text-sm font-bold mb-2">Email của bạn</label>
          <input 
            type="email" 
            placeholder="nguyentheduc@gmail.com" 
            className="w-full border-none bg-white/90 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-green-300 transition-all shadow-inner"
          />
        </div>

        <div className="mb-8">
          <label className="block text-gray-700 text-sm font-bold mb-2">Mật khẩu</label>
          <input 
            type="password" 
            placeholder="••••••••" 
            className="w-full border-none bg-white/90 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-green-300 transition-all shadow-inner"
          />
        </div>

        {/* Nút bấm có hiệu ứng Gradient, nảy lên khi hover và lún xuống khi click */}
        <button 
          onClick={() => navigate("/create-menu")}
          className="w-full bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white font-bold py-3.5 rounded-xl transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg active:scale-95"
        >
          Vào Hệ Thống
        </button>

        <p className="text-center text-sm text-gray-600 mt-6">
          Chưa có tài khoản? <span onClick={() => navigate("/register")} className="text-green-700 font-bold cursor-pointer hover:underline">Đăng ký ngay</span>
        </p>

      </div>
    </div>
  );
}