import { ShoppingCart, Beef, Carrot, CheckCircle2 } from "lucide-react";

export default function ShoppingList() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-emerald-50 p-4 md:p-8">
      <div className="max-w-2xl mx-auto bg-white p-6 md:p-8 rounded-3xl shadow-xl border-t-4 border-emerald-500">
        
        <div className="flex flex-col items-center justify-center mb-8">
          <div className="bg-emerald-100 p-3 rounded-full mb-4">
            <ShoppingCart className="w-8 h-8 text-emerald-600" />
          </div>
          <h2 className="text-3xl font-bold text-center text-gray-800">
            Danh Sách Đi Chợ
          </h2>
          <p className="text-gray-500 text-sm text-center mt-2 flex items-center">
            <CheckCircle2 className="w-4 h-4 mr-1 text-emerald-500" /> Hãy tick vào ô vuông khi bạn đã mua xong
          </p>
        </div>

        {/* Nhóm Thịt cá */}
        <div className="mb-8">
          <h3 className="font-bold text-lg text-emerald-700 border-b-2 border-emerald-100 pb-2 mb-4 flex items-center">
            <Beef className="w-5 h-5 mr-2" /> Thịt & Hải sản
          </h3>
          <ul className="space-y-3">
            <li className="group flex justify-between items-center bg-gray-50 hover:bg-emerald-50 p-4 rounded-xl transition-colors cursor-pointer border border-transparent hover:border-emerald-100">
              <label className="flex items-center cursor-pointer flex-1">
                <input type="checkbox" className="w-5 h-5 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500 mr-3 cursor-pointer" />
                <span className="text-gray-700 font-medium group-hover:text-emerald-800 transition-colors">Sườn sụn non (500g)</span>
              </label>
              <span className="text-sm font-bold text-gray-400 group-hover:text-emerald-600 transition-colors">~ 70.000đ</span>
            </li>
            <li className="group flex justify-between items-center bg-gray-50 hover:bg-emerald-50 p-4 rounded-xl transition-colors cursor-pointer border border-transparent hover:border-emerald-100">
              <label className="flex items-center cursor-pointer flex-1">
                <input type="checkbox" className="w-5 h-5 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500 mr-3 cursor-pointer" />
                <span className="text-gray-700 font-medium group-hover:text-emerald-800 transition-colors">Cá rô phi (1 con / 800g)</span>
              </label>
              <span className="text-sm font-bold text-gray-400 group-hover:text-emerald-600 transition-colors">~ 45.000đ</span>
            </li>
          </ul>
        </div>

        {/* Nhóm Rau củ */}
        <div className="mb-6">
          <h3 className="font-bold text-lg text-emerald-700 border-b-2 border-emerald-100 pb-2 mb-4 flex items-center">
            <Carrot className="w-5 h-5 mr-2" /> Rau củ & Quả
          </h3>
          <ul className="space-y-3">
            <li className="group flex justify-between items-center bg-gray-50 hover:bg-emerald-50 p-4 rounded-xl transition-colors cursor-pointer border border-transparent hover:border-emerald-100">
              <label className="flex items-center cursor-pointer flex-1">
                <input type="checkbox" className="w-5 h-5 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500 mr-3 cursor-pointer" />
                <span className="text-gray-700 font-medium group-hover:text-emerald-800 transition-colors">Rau ngót (1 mớ)</span>
              </label>
              <span className="text-sm font-bold text-gray-400 group-hover:text-emerald-600 transition-colors">~ 10.000đ</span>
            </li>
            <li className="group flex justify-between items-center bg-gray-50 hover:bg-emerald-50 p-4 rounded-xl transition-colors cursor-pointer border border-transparent hover:border-emerald-100">
              <label className="flex items-center cursor-pointer flex-1">
                <input type="checkbox" className="w-5 h-5 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500 mr-3 cursor-pointer" />
                <span className="text-gray-700 font-medium group-hover:text-emerald-800 transition-colors">Bí đao (1 quả nhỏ)</span>
              </label>
              <span className="text-sm font-bold text-gray-400 group-hover:text-emerald-600 transition-colors">~ 15.000đ</span>
            </li>
          </ul>
        </div>

        {/* Tổng kết */}
        <div className="mt-8 bg-emerald-600 rounded-2xl p-6 text-white flex justify-between items-center shadow-lg">
          <span className="font-bold uppercase tracking-wider text-sm">Tổng dự kiến</span>
          <span className="text-3xl font-bold">140.000đ</span>
        </div>

      </div>
    </div>
  );
}