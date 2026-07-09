// File: frontend/src/app/router.tsx
import { createBrowserRouter } from "react-router-dom";

import AuthLayout from "./layouts/AuthLayout";
import MainLayout from "./layouts/MainLayout";

import Welcome from "./Welcome";
import Login from "./Login";
import Register from "./Register";
import Profile from "./Profile";
import CreateMenu from "./CreateMenu";
import MenuResult from "./MenuResult";
import ShoppingList from "./ShoppingList";
import FoodDetail from "./FoodDetail";
import MenuHistory from "./MenuHistory";
import IngredientList from "./IngredientList";
import AdminUsers from "./AdminUsers";
import AdminIngredients from "./AdminIngredients";
import AdminMeals from "./AdminMeals";
import AdminDashboard from "./AdminDashboard";
export const router = createBrowserRouter([
  // Trang giới thiệu — ai cũng xem được, không menu
  { path: "/", element: <Welcome /> },

  // Trang đăng nhập/đăng ký — không menu
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <Login /> },
      { path: "/register", element: <Register /> },
    ],
  },

  // Trang bên trong — có menu, phải đăng nhập
  {
    element: <MainLayout />,
    children: [
      { path: "/profile", element: <Profile /> },
      { path: "/history", element: <MenuHistory /> },
      { path: "/create-menu", element: <CreateMenu /> },
      { path: "/menu-result", element: <MenuResult /> },
      { path: "/shopping-list", element: <ShoppingList /> },
      { path: "/food-detail", element: <FoodDetail /> },
      { path: "/food-detail", element: <FoodDetail /> },
      { path: "/ingredients", element: <IngredientList /> },
      { path: "/admin/users", element: <AdminUsers /> },
      { path: "/admin/ingredients", element: <AdminIngredients /> },
      { path: "/admin/meals", element: <AdminMeals /> },
      { path: "/admin/dashboard", element: <AdminDashboard /> },
    ],
  },
]);