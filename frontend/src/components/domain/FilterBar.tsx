import type { ReactNode } from "react";

interface FilterBarProps {
  children: ReactNode;
  className?: string;
}

export function FilterBar({ children, className = "" }: FilterBarProps) {
  return (
    <div
      className={`mb-5 flex flex-col gap-3 rounded-2xl border border-sand-200 bg-white p-3.5 shadow-sm sm:flex-row sm:flex-wrap sm:items-end ${className}`}
    >
      {children}
    </div>
  );
}
