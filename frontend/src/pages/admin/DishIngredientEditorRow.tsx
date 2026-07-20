import { Trash2 } from "lucide-react";
import type { FormIngredient } from "./dishForm";


export function IngredientEditorRow({
  item,
  onChange,
  onRemove,
}: {
  item: FormIngredient;
  onChange: (patch: Partial<FormIngredient>) => void;
  onRemove: () => void;
}) {
  const flexible = Number(item.max_extra_quantity) > 0;
  return (
    <li className="grid gap-3 p-3 sm:grid-cols-[minmax(10rem,1fr)_6rem_5rem_7rem_7rem_2.5rem] sm:items-end">
      <div>
        <p className="font-medium text-gray-900">{item.name}</p>
        <p className="mt-1 text-xs text-gray-500">
          Chỉ nhập lượng tăng nếu món có thể hấp thụ phần nguyên liệu còn rất ít.
        </p>
      </div>
      <label className="text-xs font-medium text-gray-600">
        Định lượng
        <input
          aria-label={`Định lượng ${item.name}`}
          type="number"
          min="0.01"
          step="0.01"
          value={item.quantity}
          onChange={(event) => onChange({ quantity: event.target.value })}
          className="mt-1 h-10 w-full rounded-lg border border-sand-200 px-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
      </label>
      <label className="text-xs font-medium text-gray-600">
        Đơn vị
        <input
          aria-label={`Đơn vị ${item.name}`}
          value={item.unit}
          onChange={(event) => onChange({ unit: event.target.value })}
          className="mt-1 h-10 w-full rounded-lg border border-sand-200 px-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
      </label>
      <label className="text-xs font-medium text-gray-600">
        Tăng tối đa
        <input
          aria-label={`Lượng tăng tối đa ${item.name}`}
          type="number"
          min="0"
          step="0.01"
          value={item.max_extra_quantity}
          onChange={(event) => onChange({
            max_extra_quantity: event.target.value,
            extra_step_quantity: Number(event.target.value) > 0 ? item.extra_step_quantity : "",
          })}
          className="mt-1 h-10 w-full rounded-lg border border-sand-200 px-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
      </label>
      <label className="text-xs font-medium text-gray-600">
        Bước tăng
        <input
          aria-label={`Bước tăng ${item.name}`}
          type="number"
          min="0.01"
          max={item.max_extra_quantity || undefined}
          step="0.01"
          value={item.extra_step_quantity}
          disabled={!flexible}
          required={flexible}
          onChange={(event) => onChange({ extra_step_quantity: event.target.value })}
          className="mt-1 h-10 w-full rounded-lg border border-sand-200 px-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:bg-sand-50 disabled:text-gray-400"
        />
      </label>
      <button
        type="button"
        onClick={onRemove}
        className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-red-700 transition hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
        aria-label={`Bỏ ${item.name}`}
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </li>
  );
}

