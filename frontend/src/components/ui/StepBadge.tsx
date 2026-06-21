import { cn } from "../../utils/cn";

export function StepBadge({
  index,
  active,
  done,
  label,
}: {
  index: number;
  active?: boolean;
  done?: boolean;
  label: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={cn(
          "flex h-9 w-9 items-center justify-center rounded-full border text-sm font-semibold transition",
          done
            ? "border-turquoise bg-turquoise text-white"
            : active
              ? "border-amber bg-yellowSoft text-amber"
              : "border-border bg-white text-muted",
        )}
      >
        {index}
      </div>
      <span className={cn("text-sm font-medium", active || done ? "text-dark" : "text-muted")}>{label}</span>
    </div>
  );
}
