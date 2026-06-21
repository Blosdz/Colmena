import type { PropsWithChildren } from "react";

import { cn } from "../../utils/cn";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info";

const toneStyles: Record<BadgeTone, string> = {
  neutral: "bg-[#f2efe7] text-muted",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  danger: "bg-danger/10 text-danger",
  info: "bg-info/10 text-info",
};

export function Badge({
  children,
  tone = "neutral",
  className,
}: PropsWithChildren<{ tone?: BadgeTone; className?: string }>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em]",
        toneStyles[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
