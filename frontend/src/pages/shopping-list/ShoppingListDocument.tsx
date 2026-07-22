import { useEffect, useRef } from "react";
import { Leaf } from "lucide-react";
import { formatNumber, formatVND } from "../../lib/format";
import type { ShoppingDisplayRow } from "./shoppingListView";

interface ShoppingRowsProps {
  rows: ShoppingDisplayRow[];
  onToggle?: (row: ShoppingDisplayRow) => void;
}

function RowCheckbox({ row, onToggle }: { row: ShoppingDisplayRow; onToggle?: ShoppingRowsProps["onToggle"] }) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = row.isPartiallyPurchased;
  }, [row.isPartiallyPurchased]);

  return (
    <input
      ref={ref}
      type="checkbox"
      checked={row.isPurchased}
      onChange={() => onToggle?.(row)}
      readOnly={!onToggle}
      aria-label={`${row.isPurchased ? "Bỏ đánh dấu" : "Đánh dấu đã có"} ${row.name}`}
      className="mt-1 h-4 w-4 shrink-0 rounded border-sand-300 text-brand-600 focus:ring-brand-400"
    />
  );
}

export function ShoppingRows({ rows, onToggle }: ShoppingRowsProps) {
  return (
    <ul className="divide-y divide-sand-100">
      {rows.map((row) => (
        <li key={row.key} className="shopping-print-row flex items-start gap-3 px-4 py-3 sm:px-5">
          <RowCheckbox row={row} onToggle={onToggle} />
          <div className="min-w-0 flex-1">
            <p className={`text-sm font-medium ${row.isPurchased ? "text-gray-500 line-through" : "text-gray-900"}`}>
              {row.name}
              {row.itemKind === "pantry" && (
                <span className="ml-2 rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-800">
                  kiểm tra trong bếp
                </span>
              )}
            </p>
            <p className="mt-1 text-xs text-gray-600">
              {row.itemKind === "purchase"
                ? `Cần ${formatNumber(row.requiredQuantity, 1)} ${row.unit} · mua ${formatNumber(row.purchaseQuantity, 1)} ${row.unit}`
                : `${formatNumber(row.purchaseQuantity, 1)} ${row.unit}`}
            </p>
          </div>
          <span className="text-sm font-medium tabular-nums text-gray-700">
            {row.itemKind === "pantry" ? "Có sẵn" : formatVND(row.estimatedCost)}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function ShoppingDocumentHeader({
  planName,
  scopeLabel,
  done,
  rowCount,
  totalCost,
  meta,
  printedAt,
}: {
  planName?: string | null;
  scopeLabel: string;
  done: number;
  rowCount: number;
  totalCost: number;
  meta?: string;
  printedAt?: string;
}) {
  return (
    <header className="mb-5">
      {printedAt && <p className="mb-3 text-xs text-gray-500">In lúc {printedAt}</p>}
      <div className="flex items-center gap-3 text-brand-700">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600 text-white">
          <Leaf className="h-6 w-6" />
        </span>
        <span className="text-xl font-bold text-gray-900">Smart Menu</span>
      </div>
      <h1 className="mt-4 text-2xl font-bold text-gray-900">Danh sách đi chợ{planName ? ` – ${planName}` : ""}</h1>
      <p className="mt-1 text-sm font-medium text-brand-700">{scopeLabel}</p>
      <p className="mt-1 text-sm text-gray-700">{done}/{rowCount} đã mua · {formatVND(totalCost)}</p>
      {meta && <p className="mt-1 text-xs text-gray-600">{meta}</p>}
    </header>
  );
}
