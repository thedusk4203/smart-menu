import { createBrowserRouter, Navigate } from "react-router-dom";
import { AuthLayout } from "./layouts/AuthLayout";
import { MainLayout } from "./layouts/MainLayout";
import { AdminLayout } from "./layouts/AdminLayout";
import { AdminRoute } from "../components/route/AdminRoute";
import { UserRoute } from "../components/route/UserRoute";
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
import { AdminDashboard } from "../pages/admin/Dashboard";
import { AdminIngredients } from "../pages/admin/Ingredients";
import { AdminDishes } from "../pages/admin/Dishes";
import { AdminQuality } from "../pages/admin/Quality";
import { AdminImports } from "../pages/admin/Imports";
import { AISettings } from "../pages/admin/AISettings";

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
    element: <UserRoute />,
    children: [
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
        ],
      },
    ],
  },
  {
    element: <AdminRoute />,
    children: [
      {
        element: <AdminLayout />,
        children: [
          { path: "/admin", element: <AdminDashboard /> },
          { path: "/admin/users", element: <Users /> },
          { path: "/admin/ingredients", element: <AdminIngredients /> },
          { path: "/admin/dishes", element: <AdminDishes /> },
          { path: "/admin/quality", element: <AdminQuality /> },
          { path: "/admin/imports", element: <AdminImports /> },
          { path: "/admin/ai", element: <AISettings /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
