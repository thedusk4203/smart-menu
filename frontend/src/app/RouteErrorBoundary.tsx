import { AlertTriangle, Home, RefreshCw } from "lucide-react";
import { isRouteErrorResponse, useRouteError } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { isDynamicImportError } from "./lazyImportRecovery";

export function RouteErrorBoundary() {
  const error = useRouteError();
  const isLazyLoadFailure = isDynamicImportError(error);
  const status = isRouteErrorResponse(error) ? error.status : null;

  return (
    <main className="bg-hero flex min-h-screen items-center justify-center px-4 py-10">
      <section className="w-full max-w-lg rounded-2xl border border-sand-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
          <AlertTriangle className="h-6 w-6" aria-hidden="true" />
        </div>
        <p className="mb-2 text-sm font-semibold uppercase tracking-wide text-brand-700">
          Smart Menu chưa tải được trang
        </p>
        <h1 className="text-2xl font-semibold text-gray-900">
          {isLazyLoadFailure ? "Ứng dụng vừa bị gián đoạn khi cập nhật" : "Đã có lỗi xảy ra"}
        </h1>
        <p className="mt-3 leading-7 text-gray-600">
          {isLazyLoadFailure
            ? "Dữ liệu của bạn vẫn an toàn. Hãy tải lại để nhận phiên bản giao diện mới nhất."
            : status === 404
              ? "Trang bạn tìm không tồn tại hoặc đã được chuyển sang địa chỉ khác."
              : "Không thể hiển thị trang này lúc này. Bạn có thể tải lại hoặc quay về trang chủ."}
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Button type="button" onClick={() => window.location.reload()}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Tải lại trang
          </Button>
          <a
            href="/"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-sand-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-800 transition-colors hover:bg-sand-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-1"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            Về trang chủ
          </a>
        </div>
      </section>
    </main>
  );
}
