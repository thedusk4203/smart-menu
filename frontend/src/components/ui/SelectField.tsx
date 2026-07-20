import type { SelectHTMLAttributes } from "react";
import { useId } from "react";
import { ChevronDown } from "lucide-react";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  hint?: string;
  options: SelectOption[];
  placeholder?: string;
}

export function SelectField({
  label,
  error,
  hint,
  options,
  placeholder,
  className = "",
  id,
  ...props
}: SelectFieldProps) {
  const autoId = useId();
  const fieldId = id ?? autoId;
  const descriptionId = `${fieldId}-description`;
  return (
    <div className={className}>
      {label && (
        <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={fieldId}
          className={`w-full appearance-none rounded-xl border bg-white px-3.5 py-2.5 pr-10 text-sm text-gray-900 transition focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:bg-sand-100 ${
            error ? "border-red-400 focus:ring-red-300" : "border-sand-200"
          }`}
          {...props}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={error || hint ? descriptionId : undefined}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
      </div>
      {error ? (
        <p id={descriptionId} className="mt-1 text-xs text-red-600">{error}</p>
      ) : hint ? (
        <p id={descriptionId} className="mt-1 text-xs text-gray-500">{hint}</p>
      ) : null}
    </div>
  );
}
