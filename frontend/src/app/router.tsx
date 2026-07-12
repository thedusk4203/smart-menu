import { lazy } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { AuthLayout } from "./layouts/AuthLayout";
import { MainLayout } from "./layouts/MainLayout";
import { AdminLayout } from "./layouts/AdminLayout";
import { AdminRoute } from "../components/route/AdminRoute";
import { UserRoute } from "../components/route/UserRoute";
const Welcome = lazy(() => import("../pages/Welcome").then(({ Welcome }) => ({ default: Welcome })));
const Login = lazy(() => import("../pages/auth/Login").then(({ Login }) => ({ default: Login })));
const Register = lazy(() => import("../pages/auth/Register").then(({ Register }) => ({ default: Register })));
const Dashboard = lazy(() => import("../pages/Dashboard").then(({ Dashboard }) => ({ default: Dashboard })));
const Profile = lazy(() => import("../pages/Profile").then(({ Profile }) => ({ default: Profile })));
const CreateMenu = lazy(() => import("../pages/meal-planning/CreateMenu").then(({ CreateMenu }) => ({ default: CreateMenu })));
const MenuResult = lazy(() => import("../pages/meal-planning/MenuResult").then(({ MenuResult }) => ({ default: MenuResult })));
const MenuHistory = lazy(() => import("../pages/meal-planning/MenuHistory").then(({ MenuHistory }) => ({ default: MenuHistory })));
const Ingredients = lazy(() => import("../pages/ingredients/Ingredients").then(({ Ingredients }) => ({ default: Ingredients })));
const Meals = lazy(() => import("../pages/meals/Meals").then(({ Meals }) => ({ default: Meals })));
const MealDetail = lazy(() => import("../pages/meals/MealDetail").then(({ MealDetail }) => ({ default: MealDetail })));
const ShoppingList = lazy(() => import("../pages/shopping-list/ShoppingList").then(({ ShoppingList }) => ({ default: ShoppingList })));
const PublicShoppingList = lazy(() => import("../pages/shopping-list/PublicShoppingList").then(({ PublicShoppingList }) => ({ default: PublicShoppingList })));
const Assistant = lazy(() => import("../pages/ai/Assistant").then(({ Assistant }) => ({ default: Assistant })));
const Users = lazy(() => import("../pages/admin/Users").then(({ Users }) => ({ default: Users })));
const AdminDashboard = lazy(() => import("../pages/admin/Dashboard").then(({ AdminDashboard }) => ({ default: AdminDashboard })));
const AdminIngredients = lazy(() => import("../pages/admin/Ingredients").then(({ AdminIngredients }) => ({ default: AdminIngredients })));
const AdminDishes = lazy(() => import("../pages/admin/Dishes").then(({ AdminDishes }) => ({ default: AdminDishes })));
const AdminQuality = lazy(() => import("../pages/admin/Quality").then(({ AdminQuality }) => ({ default: AdminQuality })));
const AdminImports = lazy(() => import("../pages/admin/Imports").then(({ AdminImports }) => ({ default: AdminImports })));
const AISettings = lazy(() => import("../pages/admin/AISettings").then(({ AISettings }) => ({ default: AISettings })));
const AdminTags = lazy(() => import("../pages/admin/Tags").then(({ AdminTags }) => ({ default: AdminTags })));

export const router = createBrowserRouter([
  { path: "/", element: <Welcome /> },
  { path: "/share/shopping-list/:token", element: <PublicShoppingList /> },
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
          { path: "/admin/tags", element: <AdminTags /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
