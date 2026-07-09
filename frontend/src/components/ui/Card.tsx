import type { ReactNode } from "react";

interface CardProps {
  title?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

export function Card({ title, icon, action, className = "", bodyClassName = "", children }: CardProps) {
  const hasHeader = title || action;
  return (
    <div className={`rounded-2xl border border-sand-200 bg-white shadow-sm ${className}`}>
      {hasHeader && (
        <div className="flex items-center justify-between gap-3 border-b border-sand-200 px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            {icon && <span className="text-brand-600">{icon}</span>}
            {title && <h3 className="text-base font-semibold text-gray-800">{title}</h3>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      <div className={`p-5 ${bodyClassName}`}>{children}</div>
    </div>
  );
}
