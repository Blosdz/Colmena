import { Card } from './Card.jsx';

export default function MetricCard({ icon: Icon, label, value, hint }) {
  return (
    <Card className="flex min-h-20 items-center gap-3 px-4 py-3" padded={false}>
      {Icon ? (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber/10 text-amber">
          <Icon size={18} />
        </div>
      ) : null}
      <div className="min-w-0">
        <p className="colmena-label">{label}</p>
        <p className="truncate text-xl font-bold text-dark">{value}</p>
        {hint ? <p className="truncate text-[11px] text-muted">{hint}</p> : null}
      </div>
    </Card>
  );
}
