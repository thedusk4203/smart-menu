import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { LogIn, User, History, PlusCircle, Utensils, ShoppingCart, ChefHat } from "lucide-react";

import Login from "./pages/Login";
import Register from "./pages/Register"; // Nhúng trang Đăng ký mới
import Profile from "./pages/Profile";
import CreateMenu from "./pages/CreateMenu";
import MenuResult from "./pages/MenuResult";
import ShoppingList from "./pages/ShoppingList";
import FoodDetail from "./pages/FoodDetail";
import MenuHistory from "./pages/MenuHistory";
import { Toaster } from "react-hot-toast";

export default function App() {
  return (
    <BrowserRouter>
    <Toaster position="top-center" />
      {/* Thanh Menu điều hướng */}
      <nav className="bg-white shadow-md p-4 flex justify-center flex-wrap gap-6 md:gap-8 relative z-50">
        <Link to="/" className="flex items-center gap-2 text-gray-500 hover:text-green-600 font-semibold transition-colors">
          <LogIn className="w-5 h-5" /> <span className="hidden md:inline">Đăng Nhập</span>
        </Link>
        <Link to="/profile" className="flex items-center gap-2 text-gray-500 hover:text-green-600 font-semibold transition-colors">
          <User className="w-5 h-5" /> <span className="hidden md:inline">Hồ Sơ</span>
        </Link>
        <Link to="/history" className="flex items-center gap-2 text-gray-500 hover:text-green-600 font-semibold transition-colors">
          <History className="w-5 h-5" /> <span className="hidden md:inline">Lịch Sử</span>
        </Link>
        <Link to="/create-menu" className="flex items-center gap-2 text-gray-500 hover:text-green-600 font-semibold transition-colors">
          <PlusCircle className="w-5 h-5" /> <span className="hidden md:inline">Tạo Thực Đơn</span>
        </Link>
        <Link to="/menu-result" className="flex items-center gap-2 text-gray-500 hover:text-green-600 font-semibold transition-colors">
          <Utensils className="w-5 h-5" /> <span className="hidden md:inline">Kết Quả</span>
        </Link>
        <Link to="/shopping-list" className="flex items-center gap-2 text-gray-500 hover:text-green-600 font-semibold transition-colors">
          <ShoppingCart className="w-5 h-5" /> <span className="hidden md:inline">Đi Chợ</span>
        </Link>
        <Link to="/food-detail" className="flex items-center gap-2 text-gray-500 hover:text-green-600 font-semibold transition-colors">
          <ChefHat className="w-5 h-5" /> <span className="hidden md:inline">Món Ăn</span>
        </Link>
      </nav>

      {/* Khu vực định tuyến các trang */}
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} /> {/* Đường dẫn mới */}
        <Route path="/profile" element={<Profile />} />
        <Route path="/history" element={<MenuHistory />} />
        <Route path="/create-menu" element={<CreateMenu />} />
        <Route path="/menu-result" element={<MenuResult />} />
        <Route path="/shopping-list" element={<ShoppingList />} />
        <Route path="/food-detail" element={<FoodDetail />} />
      </Routes>
    </BrowserRouter>
  );
}