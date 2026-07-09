import { Link, Outlet } from "react-router-dom";
import { Leaf } from "lucide-react";

export function AuthLayout() {
  return (
    <div className="bg-hero flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <Link to="/" className="mb-6 inline-flex items-center gap-2">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm">
          <Leaf className="h-5 w-5" />
        </span>
        <span className="text-xl font-bold text-gray-900">Smart Menu</span>
      </Link>
      <div className="w-full max-w-md rounded-2xl border border-sand-200 bg-white p-6 shadow-sm sm:p-8">
        <Outlet />
      </div>
      <p className="mt-6 text-xs text-gray-400">Thực đơn thông minh theo ngân sách &amp; dinh dưỡng</p>
    </div>
  );
}
