import { AlertTriangle, Info, RefreshCw, X } from "lucide-react";
import type { UserFeedback } from "../../lib/userFeedback";

interface FeedbackBannerProps {
  feedback: UserFeedback;
  tone?: "error" | "warning" | "info";
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

const TONES = {
  error: "border-red-200 bg-red-50 text-red-900",
  warning: "border-amber-200 bg-amber-50 text-amber-950",
  info: "border-sky-200 bg-sky-50 text-sky-950",
};

export function FeedbackBanner({ feedback, tone = "error", onRetry, onDismiss, className = "" }: FeedbackBannerProps) {
  const Icon = tone === "info" ? Info : AlertTriangle;
  return (
    <section
      className={`rounded-2xl border px-4 py-3 ${TONES[tone]} ${className}`}
      role={tone === "error" ? "alert" : "status"}
      aria-live={tone === "error" ? "assertive" : "polite"}
    >
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold">{feedback.title}</h3>
          <p className="mt-1 text-sm leading-6">{feedback.message}</p>
          {(feedback.code || feedback.technicalMessage) && (
            <p className="mt-2 break-words rounded-lg bg-black/5 px-2.5 py-2 font-mono text-xs leading-5">
              {feedback.code && <span>Mã: {feedback.code}</span>}
              {feedback.code && feedback.technicalMessage && <span aria-hidden="true"> · </span>}
              {feedback.technicalMessage && <span>Chi tiết: {feedback.technicalMessage}</span>}
            </p>
          )}
          {onRetry && feedback.retryable && (
            <button type="button" onClick={onRetry} className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-xl bg-white/80 px-3 text-sm font-semibold shadow-sm transition hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current">
              <RefreshCw className="h-4 w-4" aria-hidden="true" /> Thử lại
            </button>
          )}
        </div>
        {onDismiss && (
          <button type="button" onClick={onDismiss} className="rounded-lg p-1 transition hover:bg-black/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current" aria-label="Đóng thông báo">
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>
    </section>
  );
}
