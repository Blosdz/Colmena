import { Card } from "../ui/Card";

export function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{label}</p>
      <p className="text-3xl font-semibold tracking-tight text-dark">{value}</p>
      {hint ? <p className="text-sm text-muted">{hint}</p> : null}
    </Card>
  );
}
