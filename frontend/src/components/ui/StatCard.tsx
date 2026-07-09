import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

type Tone = "brand" | "accent" | "sky" | "rose" | "indigo" | "amber";

interface StatCardProps {
  label: string;
  value: ReactNode;
  icon?: LucideIcon;
  sub?: ReactNode;
  tone?: Tone;
  compact?: boolean;
  className?: string;
}

const TONE: Record<Tone, string> = {
  brand: "bg-brand-100 text-brand-700",
  accent: "bg-accent-100 text-accent-700",
  sky: "bg-sky-100 text-sky-700",
  rose: "bg-rose-100 text-rose-700",
  indigo: "bg-indigo-100 text-indigo-700",
  amber: "bg-amber-100 text-amber-700",
};

export function StatCard({
  label, value, icon: Icon, sub, tone = "brand", compact = false, className = "",
}: StatCardProps) {
  return (
    <div className={`rounded-2xl border border-sand-200 bg-white shadow-sm ${compact ? "p-3" : "p-4"} ${className}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
          <p className={`mt-1 font-bold text-gray-900 ${compact ? "text-lg" : "truncate text-xl"}`}>{value}</p>
          {sub && <p className="mt-0.5 text-xs text-gray-500">{sub}</p>}
        </div>
        {Icon && !compact && (
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${TONE[tone]}`}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  );
}
