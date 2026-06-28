import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
export default function Register() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-400 via-green-500 to-teal-600 flex items-center justify-center p-4">
      
      <div className="bg-white/80 backdrop-blur-md p-8 rounded-3xl shadow-2xl w-full max-w-sm border border-white/50">
        
        <h2 className="text-3xl font-bold text-center text-green-700 mb-2">Tạo Tài Khoản</h2>
        <p className="text-center text-sm text-gray-600 mb-8">Bắt đầu hành trình ăn khỏe sống đẹp</p>

        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">Họ và Tên</label>
          <input 
            type="text" 
            placeholder="Ví dụ: Nguyễn Thế Đức" 
            className="w-full border-none bg-white/90 p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-green-300 transition-all shadow-inner"
          />
        </div>

        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
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

       {/* Nút Đăng Ký đã được gắn hiệu ứng Toast */}
        <button 
          onClick={() => {
            // 1. Bắn thông báo thành công
            toast.success("Tạo tài khoản thành công! Hoàn thiện hồ sơ nhé 🎉", {
              style: {
                borderRadius: '12px',
                background: '#10b981', // Màu xanh lục của Tailwind
                color: '#fff',
                fontWeight: 'bold'
              },
            });
            // 2. Chuyển sang trang hồ sơ
            navigate("/profile");
          }}
          className="w-full bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white font-bold py-3.5 rounded-xl transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg active:scale-95"
        >
          Đăng Ký & Tạo Hồ Sơ
        </button>

        <p className="text-center text-sm text-gray-600 mt-6">
          Đã có tài khoản? <span onClick={() => navigate("/")} className="text-green-700 font-bold cursor-pointer hover:underline">Đăng nhập</span>
        </p>

      </div>
    </div>
  );
}