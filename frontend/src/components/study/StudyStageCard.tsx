import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { cn } from "../../utils/cn";

export function StudyStageCard({
  title,
  summary,
  status,
  href,
  actionLabel,
}: {
  title: string;
  summary: string;
  status: "pending" | "in_progress" | "complete";
  href: string;
  actionLabel: string;
}) {
  const statusLabel =
    status === "complete" ? "Completo" : status === "in_progress" ? "En progreso" : "Pendiente";

  return (
    <div className="flex min-h-[188px] flex-col rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-dark">{title}</h3>
          <p className="text-sm leading-6 text-muted">{summary}</p>
        </div>
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium",
            status === "complete" && "bg-[#EAF9EF] text-success",
            status === "in_progress" && "bg-[#FFF6DE] text-[#9A6A00]",
            status === "pending" && "bg-[#F5F6F7] text-muted",
          )}
        >
          {statusLabel}
        </span>
      </div>

      <Link
        className="mt-auto inline-flex h-11 items-center justify-center gap-2 rounded-[18px] border border-border text-sm font-medium text-dark transition hover:bg-[#FBF7EE]"
        to={href}
      >
        {actionLabel}
        <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );
}
