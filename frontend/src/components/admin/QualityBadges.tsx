import { AlertCircle, CheckCircle2, TriangleAlert } from "lucide-react";

export function DataStateBadge({ state, label }: { state: "ok" | "warning" | "error"; label: string }) {
  const classes = {
    ok: "bg-brand-50 text-brand-800",
    warning: "bg-amber-50 text-amber-800",
    error: "bg-red-50 text-red-800",
  }[state];
  const Icon = state === "ok" ? CheckCircle2 : state === "warning" ? TriangleAlert : AlertCircle;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${classes}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" /> {label}
    </span>
  );
}
