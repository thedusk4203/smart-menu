import { useNavigate } from "react-router-dom";
import { Wallet, Sparkles, ChefHat } from "lucide-react";

export default function CreateMenu() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-100 to-teal-50 flex flex-col items-center justify-center p-4">
      
      <div className="bg-white/90 backdrop-blur-xl p-8 rounded-3xl shadow-2xl w-full max-w-md text-center border border-white">
        
        <div className="flex justify-center mb-4">
          <div className="bg-emerald-100 p-4 rounded-full text-emerald-600">
            <ChefHat className="w-10 h-10" />
          </div>
        </div>

        <h1 className="text-3xl font-bold text-emerald-700 mb-2">Smart Menu AI</h1>
        <p className="text-gray-500 mb-8 text-sm">Lên thực đơn 7 ngày siêu tốc chuẩn dinh dưỡng</p>

        <div className="text-left mb-5">
          <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
            <Wallet className="w-4 h-4 mr-1 text-emerald-600" /> Ngân sách đi chợ (VNĐ)
          </label>
          <input type="number" placeholder="Ví dụ: 700000" className="w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner text-gray-800" />
        </div>

        <div className="text-left mb-8">
          <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
            <Sparkles className="w-4 h-4 mr-1 text-orange-500" /> Yêu cầu đặc biệt
          </label>
          <textarea placeholder="Ví dụ: Không ăn cá, ưu tiên món luộc, thích ăn cay..." className="w-full bg-gray-50 border-none p-3.5 rounded-xl h-28 focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner resize-none text-gray-800"></textarea>
        </div>

        <button 
          onClick={() => navigate("/menu-result")}
          className="w-full group bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold py-4 rounded-xl shadow-lg transform hover:-translate-y-1 active:scale-95 transition-all duration-300 flex items-center justify-center"
        >
          <Sparkles className="w-5 h-5 mr-2 group-hover:animate-pulse" />
          Tạo Thực Đơn Ngay
        </button>

      </div>
    </div>
  );
}