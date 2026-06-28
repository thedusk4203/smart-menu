import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ShoppingCart, Sunrise, Sun, Moon, Flame, Wallet, X, Send } from "lucide-react";

export default function MenuResult() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const navigate = useNavigate();

  // TUYỆT CHIÊU: Tạo một danh sách dữ liệu 7 ngày. Sau này khi có API, phần này sẽ do máy chủ gửi về.
  const weeklyMenu = [
    { 
      id: 1, title: "Ngày 1 - Thứ Hai", 
      breakfast: { name: "Bún mọc sườn sụn", cals: 450, price: "35.000đ" },
      lunch: { name: "Cơm gạo lứt, Thịt luộc, Canh rau ngót", cals: 700, price: "40.000đ" },
      dinner: { name: "Cơm trắng, Cá rô phi rán, Rau muống", cals: 650, price: "45.000đ" }
    },
    { 
      id: 2, title: "Ngày 2 - Thứ Ba", 
      breakfast: { name: "Bánh mì ốp la (2 trứng)", cals: 400, price: "15.000đ" },
      lunch: { name: "Cơm, Gà kho gừng, Canh bí đao", cals: 750, price: "50.000đ" },
      dinner: { name: "Cơm, Đậu hũ sốt cà chua, Rau luộc", cals: 550, price: "25.000đ" }
    },
    { 
      id: 3, title: "Ngày 3 - Thứ Tư", 
      breakfast: { name: "Xôi xéo chả lụa", cals: 500, price: "20.000đ" },
      lunch: { name: "Cơm, Thịt băm rang, Canh mồng tơi", cals: 680, price: "45.000đ" },
      dinner: { name: "Cơm, Trứng rán ngải cứu, Su hào luộc", cals: 500, price: "20.000đ" }
    },
    { 
      id: 4, title: "Ngày 4 - Thứ Năm", 
      breakfast: { name: "Phở bò tái nạm", cals: 500, price: "40.000đ" },
      lunch: { name: "Cơm, Cá kho tộ, Canh chua dứa", cals: 720, price: "60.000đ" },
      dinner: { name: "Cơm, Bò xào hành tây, Xà lách", cals: 600, price: "55.000đ" }
    },
    { 
      id: 5, title: "Ngày 5 - Thứ Sáu", 
      breakfast: { name: "Bún chả Hà Nội", cals: 550, price: "35.000đ" },
      lunch: { name: "Cơm, Sườn chua ngọt, Canh bí đỏ", cals: 750, price: "55.000đ" },
      dinner: { name: "Cơm, Mực xào cần tỏi, Rau dền", cals: 620, price: "60.000đ" }
    },
    { 
      id: 6, title: "Ngày 6 - Thứ Bảy", 
      breakfast: { name: "Bánh cuốn chả quế", cals: 400, price: "25.000đ" },
      lunch: { name: "Cơm, Tôm rang ba chỉ, Canh cải", cals: 700, price: "65.000đ" },
      dinner: { name: "Bún riêu cua bắp bò", cals: 500, price: "40.000đ" }
    },
    { 
      id: 7, title: "Ngày 7 - Chủ Nhật", 
      breakfast: { name: "Bún bò Huế", cals: 550, price: "45.000đ" },
      lunch: { name: "Gà nướng tiêu xanh, Salad", cals: 650, price: "70.000đ" },
      dinner: { name: "Cháo sườn sụn quẩy giòn", cals: 450, price: "30.000đ" }
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-emerald-50 p-4 md:p-8 relative pb-24">
      
      <div className="text-center mb-10 mt-4">
        <h1 className="text-3xl md:text-4xl font-bold text-emerald-700 mb-3">Thực Đơn Tuần Này</h1>
        <p className="text-gray-500">Được tối ưu riêng cho bạn bởi AI</p>
      </div>

      {/* Thẻ Thống kê Tổng quan */}
      <div className="bg-white/80 backdrop-blur-lg p-6 md:p-8 rounded-3xl shadow-xl mb-10 max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center border border-white">
        <div className="flex items-center gap-4 mb-4 md:mb-0">
          <div className="bg-green-100 p-4 rounded-full"><Wallet className="w-8 h-8 text-green-600" /></div>
          <div>
            <p className="text-gray-500 text-sm font-bold uppercase tracking-wide">Tổng chi phí</p>
            <p className="text-3xl font-bold text-green-600">920.000đ</p>
          </div>
        </div>
        
        <button 
          onClick={() => navigate("/shopping-list")}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-8 rounded-xl shadow-lg transform hover:-translate-y-1 transition-all flex items-center"
        >
          <ShoppingCart className="w-5 h-5 mr-2" /> Xem Danh Sách Đi Chợ
        </button>

        <div className="flex items-center gap-4 mt-4 md:mt-0">
          <div className="text-right">
            <p className="text-gray-500 text-sm font-bold uppercase tracking-wide">Trung bình/ngày</p>
            <p className="text-3xl font-bold text-orange-500">1700 kcal</p>
          </div>
          <div className="bg-orange-100 p-4 rounded-full"><Flame className="w-8 h-8 text-orange-500" /></div>
        </div>
      </div>

      {/* Lưới hiển thị 7 ngày (Sử dụng lệnh map để tự động vẽ) */}
      <div className="max-w-4xl mx-auto grid gap-8 md:grid-cols-2">
        
        {weeklyMenu.map((day) => (
          <div key={day.id} className="bg-white rounded-3xl overflow-hidden shadow-lg border border-gray-100 hover:shadow-2xl transition-shadow duration-300">
            <div className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white p-4 font-bold text-lg text-center shadow-inner">
              {day.title}
            </div>
            <div className="p-6 space-y-5">
              
              {/* Bữa Sáng */}
              <div className="group cursor-pointer" onClick={() => navigate("/food-detail")}>
                <span className="inline-flex items-center bg-orange-50 text-orange-600 text-xs font-bold px-3 py-1 rounded-full mb-2">
                  <Sunrise className="w-3.5 h-3.5 mr-1" /> Bữa Sáng
                </span>
                <h3 className="font-bold text-gray-800 text-lg group-hover:text-emerald-600 transition-colors">{day.breakfast.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{day.breakfast.cals} kcal • {day.breakfast.price}</p>
              </div>
              
              {/* Bữa Trưa */}
              <div className="border-t border-gray-100 pt-4 group cursor-pointer" onClick={() => navigate("/food-detail")}>
                <span className="inline-flex items-center bg-blue-50 text-blue-600 text-xs font-bold px-3 py-1 rounded-full mb-2">
                  <Sun className="w-3.5 h-3.5 mr-1" /> Bữa Trưa
                </span>
                <h3 className="font-bold text-gray-800 text-lg group-hover:text-emerald-600 transition-colors">{day.lunch.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{day.lunch.cals} kcal • {day.lunch.price}</p>
              </div>
              
              {/* Bữa Tối */}
              <div className="border-t border-gray-100 pt-4 group cursor-pointer" onClick={() => navigate("/food-detail")}>
                <span className="inline-flex items-center bg-indigo-50 text-indigo-600 text-xs font-bold px-3 py-1 rounded-full mb-2">
                  <Moon className="w-3.5 h-3.5 mr-1" /> Bữa Tối
                </span>
                <h3 className="font-bold text-gray-800 text-lg group-hover:text-emerald-600 transition-colors">{day.dinner.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{day.dinner.cals} kcal • {day.dinner.price}</p>
              </div>

            </div>
          </div>
        ))}

      </div>

      {/* --- KHU VỰC AI ASSISTANT --- */}
      <button 
        onClick={() => setIsChatOpen(true)} 
        className={`${isChatOpen ? 'hidden' : 'flex'} animate-bounce fixed bottom-8 right-8 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white w-16 h-16 rounded-full shadow-2xl items-center justify-center transition-all hover:scale-110 z-20`}
      >
        <Sparkles className="w-7 h-7" />
      </button>

      {isChatOpen && (
        <div className="fixed bottom-8 right-8 w-80 md:w-96 bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden z-30 animate-in slide-in-from-bottom-5">
          <div className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white p-4 flex justify-between items-center shadow-md">
            <h3 className="font-bold flex items-center"><Sparkles className="w-5 h-5 mr-2" /> Trợ lý AI Smart Menu</h3>
            <button onClick={() => setIsChatOpen(false)} className="text-white/80 hover:text-white transition bg-white/10 rounded-full p-1"><X className="w-5 h-5" /></button>
          </div>
          <div className="p-5 h-64 overflow-y-auto bg-gray-50 text-sm space-y-4">
            <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-gray-100 text-gray-700">
              Xin chào! Tôi đã xếp thực đơn 7 ngày này dựa trên yêu cầu của bạn:
              <ul className="list-disc pl-5 mt-2 space-y-1 text-emerald-800">
                <li>Ưu tiên các món thanh mát, dễ nấu.</li>
                <li>Đảm bảo dinh dưỡng với chi phí hợp lý.</li>
              </ul>
            </div>
          </div>
          <div className="p-3 bg-white border-t border-gray-100 flex gap-2">
            <input type="text" placeholder="Nhắn AI đổi món..." className="w-full bg-gray-50 px-4 py-2.5 rounded-full outline-none focus:ring-2 focus:ring-emerald-200 text-sm" />
            <button className="bg-emerald-500 hover:bg-emerald-600 text-white p-2.5 rounded-full transition-transform active:scale-95"><Send className="w-4 h-4" /></button>
          </div>
        </div>
      )}

    </div>
  );
}