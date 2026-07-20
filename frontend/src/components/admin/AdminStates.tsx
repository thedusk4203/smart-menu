import type { LucideIcon } from "lucide-react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import type { UserFeedback } from "../../lib/userFeedback";

export function AdminTableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="animate-pulse" aria-label="Đang tải dữ liệu" role="status">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex gap-4 border-b border-sand-100 px-5 py-4 last:border-0">
          <div className="h-4 w-1/3 rounded bg-sand-200" />
          <div className="h-4 w-1/5 rounded bg-sand-100" />
          <div className="ml-auto h-4 w-24 rounded bg-sand-100" />
        </div>
      ))}
    </div>
  );
}

export function AdminErrorState({ message, feedback, onRetry }: { message?: string | UserFeedback; feedback?: UserFeedback; onRetry: () => void }) {
  const detail = feedback ?? (typeof message === "object" ? message : undefined);
  const summary = detail?.message ?? (typeof message === "string" ? message : undefined) ?? "Máy chủ chưa trả về dữ liệu.";
  return (
    <div className="flex flex-col items-center px-5 py-14 text-center" role="alert">
      <span className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-red-50 text-red-700">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
      </span>
      <p className="font-semibold text-gray-900">Không tải được dữ liệu</p>
      <p className="mt-1 max-w-md text-sm text-gray-600">{summary}</p>
      {(detail?.code || detail?.technicalMessage) && (
        <p className="mt-3 max-w-xl break-words rounded-lg bg-red-50 px-3 py-2 text-left font-mono text-xs leading-5 text-red-900">
          {detail.code && <span>Mã: {detail.code}</span>}
          {detail.code && detail.technicalMessage && <span aria-hidden="true"> · </span>}
          {detail.technicalMessage && <span>Chi tiết: {detail.technicalMessage}</span>}
        </p>
      )}
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-xl border border-sand-200 bg-white px-4 text-sm font-medium text-gray-800 transition hover:bg-sand-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
      >
        <RefreshCw className="h-4 w-4" aria-hidden="true" /> Thử lại
      </button>
    </div>
  );
}

export function AdminEmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center px-5 py-14 text-center">
      <span className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-sand-100 text-gray-600">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </span>
      <p className="font-semibold text-gray-900">{title}</p>
      <p className="mt-1 max-w-md text-sm text-gray-600">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
