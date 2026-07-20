import type { TextareaHTMLAttributes } from "react";
import { useId } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export function Textarea({ label, error, hint, className = "", id, rows = 4, ...props }: TextareaProps) {
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
      <textarea
        id={fieldId}
        rows={rows}
        className={`w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 transition focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:bg-sand-100 ${
          error ? "border-red-400 focus:ring-red-300" : "border-sand-200"
        }`}
        {...props}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={error || hint ? descriptionId : undefined}
      />
      {error ? (
        <p id={descriptionId} className="mt-1 text-xs text-red-600">{error}</p>
      ) : hint ? (
        <p id={descriptionId} className="mt-1 text-xs text-gray-500">{hint}</p>
      ) : null}
    </div>
  );
}
