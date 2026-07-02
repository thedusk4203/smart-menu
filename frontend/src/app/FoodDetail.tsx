import { Clock, Flame, Utensils, CheckCircle2 } from "lucide-react";

export default function FoodDetail() {
  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 md:px-8">
      <div className="max-w-3xl mx-auto bg-white rounded-3xl shadow-xl overflow-hidden border border-gray-100">
        
        {/* Hình ảnh món ăn */}
        <div className="relative h-64 md:h-80 w-full">
          <img 
            src="https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1200&q=80" 
            alt="Food" 
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
          <div className="absolute bottom-6 left-6 md:left-8">
            <span className="bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider mb-2 inline-block shadow-md">
              Bữa Sáng
            </span>
            <h1 className="text-3xl md:text-4xl font-bold text-white shadow-sm">Bún mọc sườn sụn</h1>
          </div>
        </div>

        <div className="p-6 md:p-8">
          
          {/* Tóm tắt */}
          <div className="flex flex-wrap gap-4 mb-8 pb-6 border-b border-gray-100">
            <div className="flex items-center text-gray-600 bg-gray-50 px-4 py-2 rounded-xl">
              <Clock className="w-5 h-5 mr-2 text-emerald-500" />
              <span className="font-medium">30 Phút</span>
            </div>
            <div className="flex items-center text-gray-600 bg-gray-50 px-4 py-2 rounded-xl">
              <Utensils className="w-5 h-5 mr-2 text-orange-500" />
              <span className="font-medium">Dễ nấu</span>
            </div>
            <div className="flex items-center text-gray-600 bg-gray-50 px-4 py-2 rounded-xl">
              <span className="font-bold text-emerald-600">~ 35.000đ</span>
            </div>
          </div>

          {/* Dinh dưỡng */}
          <div className="grid grid-cols-4 gap-3 md:gap-4 text-center mb-10">
            <div className="bg-orange-50 rounded-2xl p-4 border border-orange-100 shadow-sm">
              <Flame className="w-6 h-6 mx-auto text-orange-500 mb-2" />
              <p className="text-xs text-orange-600 uppercase font-bold mb-1">Calo</p>
              <p className="font-bold text-gray-800 text-lg">450</p>
            </div>
            <div className="bg-blue-50 rounded-2xl p-4 border border-blue-100 shadow-sm">
              <p className="text-xs text-blue-600 uppercase font-bold mb-1 mt-6">Protein</p>
              <p className="font-bold text-gray-800 text-lg">25g</p>
            </div>
            <div className="bg-yellow-50 rounded-2xl p-4 border border-yellow-100 shadow-sm">
              <p className="text-xs text-yellow-600 uppercase font-bold mb-1 mt-6">Fat</p>
              <p className="font-bold text-gray-800 text-lg">15g</p>
            </div>
            <div className="bg-green-50 rounded-2xl p-4 border border-green-100 shadow-sm">
              <p className="text-xs text-green-600 uppercase font-bold mb-1 mt-6">Carb</p>
              <p className="font-bold text-gray-800 text-lg">55g</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-10">
            {/* Nguyên liệu */}
            <div>
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                🛒 Cần chuẩn bị
              </h3>
              <ul className="space-y-3">
                <li className="flex justify-between items-center bg-gray-50 p-3 rounded-xl">
                  <span className="text-gray-700">Bún tươi</span>
                  <span className="font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-lg">200g</span>
                </li>
                <li className="flex justify-between items-center bg-gray-50 p-3 rounded-xl">
                  <span className="text-gray-700">Sườn sụn</span>
                  <span className="font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-lg">150g</span>
                </li>
                <li className="flex justify-between items-center bg-gray-50 p-3 rounded-xl">
                  <span className="text-gray-700">Mọc (giò sống)</span>
                  <span className="font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-lg">50g</span>
                </li>
              </ul>
            </div>

            {/* Cách làm */}
            <div>
              <h3 className="text-xl font-bold text-gray-800 mb-5 flex items-center">
                👨‍🍳 Cách nấu
              </h3>
              {/* Đã sửa dòng kẻ: Cố định vị trí bên trái (left-3) nối các điểm lại với nhau */}
              <div className="space-y-6 relative before:absolute before:inset-y-0 before:left-3 before:w-0.5 before:bg-gray-200">
                
                <div className="relative flex items-start space-x-4">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-600 font-bold text-sm ring-4 ring-white z-10 shrink-0">1</div>
                  <p className="text-gray-600 leading-relaxed pt-0.5">Rửa sạch sườn sụn, chần qua nước sôi rồi ninh nhỏ lửa trong 20 phút để lấy nước dùng ngọt.</p>
                </div>
                
                <div className="relative flex items-start space-x-4">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-600 font-bold text-sm ring-4 ring-white z-10 shrink-0">2</div>
                  <p className="text-gray-600 leading-relaxed pt-0.5">Viên giò sống thành từng viên nhỏ vừa ăn, thả vào nồi nước dùng đang sôi.</p>
                </div>

                <div className="relative flex items-start space-x-4">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-600 font-bold text-sm ring-4 ring-white z-10 shrink-0">3</div>
                  <p className="text-gray-600 leading-relaxed pt-0.5">Khi mọc nổi lên mặt nước là chín. Nêm nếm mắm muối gia vị vừa miệng.</p>
                </div>

                <div className="relative flex items-start space-x-4">
                  <div className="flex justify-center items-center w-6 h-6 rounded-full bg-emerald-500 text-white font-bold ring-4 ring-white z-10 shrink-0">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <p className="text-gray-800 font-medium leading-relaxed pt-0.5">Chần bún nóng cho vào bát. Xếp sườn, mọc, hành lá lên và chan nước dùng. Thưởng thức!</p>
                </div>

              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}