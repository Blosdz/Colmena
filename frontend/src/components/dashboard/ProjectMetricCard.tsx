import type { LucideIcon } from "lucide-react";

export function ProjectMetricCard({
  icon: Icon,
  toneClass,
  title,
  value,
  delta,
  hint,
}: {
  icon: LucideIcon;
  toneClass: string;
  title: string;
  value: string | number;
  delta?: string;
  hint?: string;
}) {
  return (
    <div className="rounded-[22px] border border-border bg-white px-5 py-5 shadow-card">
      <div className="flex items-start gap-4">
        <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-[20px] ${toneClass}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="space-y-2">
          <p className="text-sm font-medium leading-6 text-dark">{title}</p>
          <p className="text-[44px] font-semibold leading-none tracking-tight text-dark">{value}</p>
          {delta ? <p className="text-sm font-medium text-success">{delta}</p> : null}
          {hint ? <p className="text-sm text-muted">{hint}</p> : null}
        </div>
      </div>
    </div>
  );
}
