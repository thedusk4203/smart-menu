import { ChevronLeft, ChevronRight } from "lucide-react";

interface AdminPaginationProps {
  offset: number;
  limit: number;
  total: number;
  onChange: (offset: number) => void;
}

export function AdminPagination({ offset, limit, total, onChange }: AdminPaginationProps) {
  if (total <= limit && offset === 0) return null;
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);

  return (
    <div className="flex flex-col gap-3 border-t border-sand-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-gray-600" aria-live="polite">
        Hiển thị <span className="font-medium text-gray-900">{from}–{to}</span> trong {total}
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onChange(Math.max(0, offset - limit))}
          disabled={offset === 0}
          className="inline-flex min-h-11 items-center gap-1 rounded-xl border border-sand-200 bg-white px-3 text-sm font-medium text-gray-700 transition hover:bg-sand-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" /> Trước
        </button>
        <button
          type="button"
          onClick={() => onChange(offset + limit)}
          disabled={offset + limit >= total}
          className="inline-flex min-h-11 items-center gap-1 rounded-xl border border-sand-200 bg-white px-3 text-sm font-medium text-gray-700 transition hover:bg-sand-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Sau <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
