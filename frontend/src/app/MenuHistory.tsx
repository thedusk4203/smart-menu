import { useNavigate } from "react-router-dom";
import { Calendar, ChevronRight, CheckCircle2 } from "lucide-react";

export default function MenuHistory() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50 p-4 md:p-8">
      <div className="max-w-3xl mx-auto">
        
        <div className="text-center mb-10 mt-4">
          <h2 className="text-3xl font-bold text-emerald-700 mb-2">Lịch Sử Thực Đơn</h2>
          <p className="text-gray-500">Xem lại những thực đơn bạn đã tạo trước đây</p>
        </div>

        <div className="space-y-5">
          
          {/* Thẻ Lịch sử 1 */}
          <div 
            onClick={() => navigate("/menu-result")}
            className="group bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row justify-between items-center cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
          >
            <div className="mb-4 md:mb-0">
              <h3 className="font-bold text-xl text-gray-800 flex items-center mb-2">
                <Calendar className="w-5 h-5 mr-2 text-emerald-500" /> Tuần 01/06 - 07/06/2026
              </h3>
              <div className="flex gap-3 text-sm">
                <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full font-medium flex items-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Giảm cân
                </span>
                <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full font-medium">
                  Ngân sách: 650.000đ
                </span>
              </div>
            </div>
            {/* Mũi tên chuyển màu xanh khi đưa chuột vào ô */}
            <div className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-emerald-100 transition-colors">
              <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-600" />
            </div>
          </div>

          {/* Thẻ Lịch sử 2 */}
          <div 
            onClick={() => navigate("/menu-result")}
            className="group bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row justify-between items-center cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
          >
            <div className="mb-4 md:mb-0">
              <h3 className="font-bold text-xl text-gray-800 flex items-center mb-2">
                <Calendar className="w-5 h-5 mr-2 text-gray-400" /> Tuần 25/05 - 31/05/2026
              </h3>
              <div className="flex gap-3 text-sm">
                <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-medium flex items-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Tiết kiệm
                </span>
                <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full font-medium">
                  Ngân sách: 500.000đ
                </span>
              </div>
            </div>
            <div className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-emerald-100 transition-colors">
              <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-600" />
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}