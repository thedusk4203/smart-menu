import { lazy } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { AuthLayout } from "./layouts/AuthLayout";
import { MainLayout } from "./layouts/MainLayout";
import { AdminLayout } from "./layouts/AdminLayout";
import { AdminRoute } from "../components/route/AdminRoute";
import { UserRoute } from "../components/route/UserRoute";
import { RouteErrorBoundary } from "./RouteErrorBoundary";
import { isDynamicImportError } from "./lazyImportRecovery";
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
const InventoryLots = lazy(() => import("../pages/inventory/InventoryLots").then(({ InventoryLots }) => ({ default: InventoryLots })));
const PublicShoppingList = lazy(() => import("../pages/shopping-list/PublicShoppingList").then(({ PublicShoppingList }) => ({ default: PublicShoppingList })));
const ASSISTANT_RETRY_KEY = "smart-menu:lazy-retry:assistant";
const Assistant = lazy(async () => {
  try {
    const module = await import("../pages/ai/Assistant");
    window.sessionStorage.removeItem(ASSISTANT_RETRY_KEY);
    return { default: module.Assistant };
  } catch (error) {
    if (isDynamicImportError(error) && !window.sessionStorage.getItem(ASSISTANT_RETRY_KEY)) {
      window.sessionStorage.setItem(ASSISTANT_RETRY_KEY, "1");
      window.location.reload();
      return new Promise<never>(() => undefined);
    }
    throw error;
  }
});
const Users = lazy(() => import("../pages/admin/Users").then(({ Users }) => ({ default: Users })));
const AdminDashboard = lazy(() => import("../pages/admin/Dashboard").then(({ AdminDashboard }) => ({ default: AdminDashboard })));
const AdminIngredients = lazy(() => import("../pages/admin/Ingredients").then(({ AdminIngredients }) => ({ default: AdminIngredients })));
const AdminDishes = lazy(() => import("../pages/admin/Dishes").then(({ AdminDishes }) => ({ default: AdminDishes })));
const AdminQuality = lazy(() => import("../pages/admin/Quality").then(({ AdminQuality }) => ({ default: AdminQuality })));
const AdminImports = lazy(() => import("../pages/admin/Imports").then(({ AdminImports }) => ({ default: AdminImports })));
const AISettings = lazy(() => import("../pages/admin/AISettings").then(({ AISettings }) => ({ default: AISettings })));
const AdminTags = lazy(() => import("../pages/admin/Tags").then(({ AdminTags }) => ({ default: AdminTags })));

export const router = createBrowserRouter([
  { path: "/", element: <Welcome />, errorElement: <RouteErrorBoundary /> },
  { path: "/share/shopping-list/:token", element: <PublicShoppingList />, errorElement: <RouteErrorBoundary /> },
  {
    element: <AuthLayout />,
    errorElement: <RouteErrorBoundary />,
    children: [
      { path: "/login", element: <Login /> },
      { path: "/register", element: <Register /> },
    ],
  },
  {
    element: <UserRoute />,
    errorElement: <RouteErrorBoundary />,
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
          { path: "/inventory", element: <InventoryLots /> },
          { path: "/ai-chat", element: <Assistant /> },
        ],
      },
    ],
  },
  {
    element: <AdminRoute />,
    errorElement: <RouteErrorBoundary />,
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
  { path: "*", element: <Navigate to="/" replace />, errorElement: <RouteErrorBoundary /> },
]);
