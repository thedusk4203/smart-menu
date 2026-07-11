import { useId, useRef } from "react";
import type { ChangeEvent, InputHTMLAttributes } from "react";
import { formatMoneyInput, parseMoneyInput } from "../../lib/format";

interface MoneyFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "value" | "onChange"> {
  value: string;
  onValueChange: (value: string) => void;
  label?: string;
  error?: string;
  hint?: string;
  suffix?: string;
  maxFractionDigits?: number;
}

function caretAfterDigits(value: string, digitCount: number): number {
  if (digitCount <= 0) return 0;
  let seen = 0;
  for (let index = 0; index < value.length; index += 1) {
    if (/\d/.test(value[index])) seen += 1;
    if (seen === digitCount) return index + 1;
  }
  return value.length;
}

export function MoneyField({
  label,
  error,
  hint,
  suffix = "đ",
  className = "",
  id,
  value,
  onValueChange,
  maxFractionDigits = 0,
  ...props
}: MoneyFieldProps) {
  const autoId = useId();
  const fieldId = id ?? autoId;
  const inputRef = useRef<HTMLInputElement>(null);
  const displayValue = formatMoneyInput(value, maxFractionDigits);

  const onChange = (event: ChangeEvent<HTMLInputElement>) => {
    const rawValue = event.currentTarget.value;
    const cursor = event.currentTarget.selectionStart ?? rawValue.length;
    const rawBeforeCursor = rawValue.slice(0, cursor);
    const precedingDigits = (rawBeforeCursor.match(/\d/g) ?? []).length;
    const decimalPosition = rawBeforeCursor.lastIndexOf(",");
    const decimalDigits = decimalPosition >= 0 ? (rawBeforeCursor.slice(decimalPosition + 1).match(/\d/g) ?? []).length : 0;
    const nextValue = parseMoneyInput(rawValue, maxFractionDigits);
    onValueChange(nextValue);
    requestAnimationFrame(() => {
      const input = inputRef.current;
      if (input && document.activeElement === input) {
        const nextDisplay = formatMoneyInput(nextValue, maxFractionDigits);
        const nextDecimalPosition = nextDisplay.indexOf(",");
        const nextCursor = decimalPosition >= 0 && nextDecimalPosition >= 0
          ? nextDecimalPosition + 1 + decimalDigits
          : caretAfterDigits(nextDisplay, precedingDigits);
        input.setSelectionRange(nextCursor, nextCursor);
      }
    });
  };

  return (
    <div className={className}>
      {label && <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-gray-700">{label}</label>}
      <div className="relative">
        <input
          ref={inputRef}
          id={fieldId}
          type="text"
          inputMode="decimal"
          value={displayValue}
          onChange={onChange}
          className={`w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 transition focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:bg-sand-100 disabled:text-gray-500 ${
            suffix ? "pr-12" : ""
          } ${error ? "border-red-400 focus:ring-red-300" : "border-sand-200"}`}
          {...props}
        />
        {suffix && <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-sm text-gray-400">{suffix}</span>}
      </div>
      {error ? <p className="mt-1 text-xs text-red-600">{error}</p> : hint ? <p className="mt-1 text-xs text-gray-500">{hint}</p> : null}
    </div>
  );
}
