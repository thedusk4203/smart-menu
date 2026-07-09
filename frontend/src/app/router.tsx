import { createBrowserRouter, Navigate } from "react-router-dom";
import { AuthLayout } from "./layouts/AuthLayout";
import { MainLayout } from "./layouts/MainLayout";
import { AdminLayout } from "./layouts/AdminLayout";
import { Welcome } from "../pages/Welcome";
import { Login } from "../pages/auth/Login";
import { Register } from "../pages/auth/Register";
import { Dashboard } from "../pages/Dashboard";
import { Profile } from "../pages/Profile";
import { CreateMenu } from "../pages/meal-planning/CreateMenu";
import { MenuResult } from "../pages/meal-planning/MenuResult";
import { MenuHistory } from "../pages/meal-planning/MenuHistory";
import { Ingredients } from "../pages/ingredients/Ingredients";
import { Meals } from "../pages/meals/Meals";
import { MealDetail } from "../pages/meals/MealDetail";
import { ShoppingList } from "../pages/shopping-list/ShoppingList";
import { Assistant } from "../pages/ai/Assistant";
import { Users } from "../pages/admin/Users";

export const router = createBrowserRouter([
  { path: "/", element: <Welcome /> },
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <Login /> },
      { path: "/register", element: <Register /> },
    ],
  },
  {
    element: <MainLayout />,
    children: [
      { path: "/dashboard", element: <Dashboard /> },
      { path: "/profile", element: <Profile /> },
      { path: "/create-menu", element: <CreateMenu /> },
      { path: "/menu-result", element: <MenuResult /> },
      { path: "/history", element: <MenuHistory /> },
      { path: "/ingredients", element: <Ingredients /> },
      { path: "/meals", element: <Meals /> },
      { path: "/meals/:id", element: <MealDetail /> },
      { path: "/shopping-list", element: <ShoppingList /> },
      { path: "/ai-chat", element: <Assistant /> },
      {
        element: <AdminLayout />,
        children: [{ path: "/admin/users", element: <Users /> }],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
