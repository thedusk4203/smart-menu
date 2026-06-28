import { Ruler, Weight, Target, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";

export default function Profile() {
  return (
    /* Nền màu xanh mint rất nhẹ và sang trọng */
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 flex justify-center items-center p-4">
      
      {/* Khung kính trong trẻo */}
      <div className="bg-white/90 backdrop-blur-xl p-8 rounded-3xl shadow-xl w-full max-w-lg border border-white">
        
        <h2 className="text-3xl font-bold text-center text-emerald-700 mb-8">
          Hồ Sơ Dinh Dưỡng
        </h2>

        {/* Khung chia 2 cột cho Chiều cao & Cân nặng */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="relative">
            <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
              <Ruler className="w-4 h-4 mr-1 text-emerald-600" /> Chiều cao (cm)
            </label>
            <input type="number" placeholder="170" className="w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner" />
          </div>
          <div className="relative">
            <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
              <Weight className="w-4 h-4 mr-1 text-emerald-600" /> Cân nặng (kg)
            </label>
            <input type="number" placeholder="65" className="w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner" />
          </div>
        </div>

        {/* Khung chọn Mục tiêu */}
        <div className="mb-6">
          <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
            <Target className="w-4 h-4 mr-1 text-emerald-600" /> Mục tiêu thể chất
          </label>
          <select className="w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner text-gray-700 cursor-pointer">
            <option>Duy trì cân nặng</option>
            <option>Giảm cân an toàn</option>
            <option>Tăng cơ / Tăng cân</option>
            <option>Ăn chay / Healthy</option>
          </select>
        </div>

        {/* Khung nhập Dị ứng */}
        <div className="mb-8">
          <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
            <AlertCircle className="w-4 h-4 mr-1 text-orange-500" /> Thực phẩm dị ứng / Không ăn
          </label>
          <textarea placeholder="Ví dụ: Dị ứng đậu phộng, không ăn hành..." className="w-full bg-gray-50 border-none p-3.5 rounded-xl h-24 focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner resize-none"></textarea>
        </div>

        {/* Nút Lưu hiệu ứng nảy kèm thông báo Toast */}
        <button 
          onClick={() => {
            toast.success("Đã lưu hồ sơ thành công! 🌿", {
              style: {
                borderRadius: '12px',
                background: '#10b981', 
                color: '#fff',
                fontWeight: 'bold'
              },
            });
          }}
          className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold py-4 rounded-xl shadow-lg transform hover:-translate-y-1 active:scale-95 transition-all duration-300"
        >
          Cập Nhật Hồ Sơ
        </button>

      </div>
    </div>
  );
}