// File: frontend/src/app/providers.tsx
// Nơi đặt các provider dùng chung toàn app (Toaster, và sau này có thể thêm
// Context, React Query...). Bọc quanh RouterProvider.
import { RouterProvider } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { router } from "./router";

export default function AppProviders() {
  return (
    <>
      <Toaster position="top-center" />
      <RouterProvider router={router} />
    </>
  );
}