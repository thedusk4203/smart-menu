// File: frontend/src/app/router.tsx
// Định nghĩa toàn bộ route, chia theo 2 layout: Auth (công khai) và Main (cần đăng nhập).
import { createBrowserRouter } from "react-router-dom";

import AuthLayout from "./layouts/AuthLayout";
import MainLayout from "./layouts/MainLayout";

import Login from "./Login";
import Register from "./Register";
import Profile from "./Profile";
import CreateMenu from "./CreateMenu";
import MenuResult from "./MenuResult";
import ShoppingList from "./ShoppingList";
import FoodDetail from "./FoodDetail";
import MenuHistory from "./MenuHistory";

export const router = createBrowserRouter([
  {
    element: <AuthLayout />,
    children: [
      { path: "/", element: <Login /> },
      { path: "/register", element: <Register /> },
    ],
  },
  {
    element: <MainLayout />,
    children: [
      { path: "/profile", element: <Profile /> },
      { path: "/history", element: <MenuHistory /> },
      { path: "/create-menu", element: <CreateMenu /> },
      { path: "/menu-result", element: <MenuResult /> },
      { path: "/shopping-list", element: <ShoppingList /> },
      { path: "/food-detail", element: <FoodDetail /> },
    ],
  },
]);