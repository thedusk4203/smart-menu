import { Suspense } from "react";
import { RouterProvider } from "react-router-dom";
import { Providers } from "./providers";
import { router } from "./router";

export default function App() {
  return (
    <Providers>
      <Suspense fallback={<div className="grid min-h-screen place-items-center text-sm text-gray-600">Đang tải…</div>}>
        <RouterProvider router={router} />
      </Suspense>
    </Providers>
  );
}
