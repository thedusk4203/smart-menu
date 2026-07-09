import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  offset: number;
  limit: number;
  count: number; // so item tra ve o trang hien tai
  onChange: (offset: number) => void;
}

export function Pagination({ offset, limit, count, onChange }: PaginationProps) {
  const page = Math.floor(offset / limit) + 1;
  const from = count === 0 ? 0 : offset + 1;
  const to = offset + count;
  const hasPrev = offset > 0;
  const hasNext = count >= limit;

  if (!hasPrev && !hasNext) return null;

  return (
    <div className="flex items-center justify-between gap-3 pt-1">
      <p className="text-sm text-gray-500">
        {count === 0 ? "Không có mục nào" : `Hiển thị ${from}–${to} · Trang ${page}`}
      </p>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onChange(Math.max(0, offset - limit))}
          disabled={!hasPrev}
          className="inline-flex items-center gap-1 rounded-xl border border-sand-200 bg-white px-3 py-1.5 text-sm text-gray-700 transition hover:bg-sand-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <ChevronLeft className="h-4 w-4" />
          Trước
        </button>
        <button
          onClick={() => onChange(offset + limit)}
          disabled={!hasNext}
          className="inline-flex items-center gap-1 rounded-xl border border-sand-200 bg-white px-3 py-1.5 text-sm text-gray-700 transition hover:bg-sand-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Sau
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
