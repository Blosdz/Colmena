import { Area, AreaChart, ResponsiveContainer } from 'recharts';

import { Card } from '../../ui/Card.jsx';

/**
 * Detección de magnitudes: número + delta contra periodo anterior + serie
 * de fondo, siempre los tres juntos. Un número solo no dice nada porque no
 * hay con qué compararlo.
 */
export default function KpiCard({ icon: Icon, label, value, hint, delta, deltaTone = 'neutral', sparkline }) {
  const toneClass = deltaTone === 'up' ? 'text-success' : deltaTone === 'down' ? 'text-danger' : 'text-muted';
  return (
    <Card className="relative overflow-hidden px-4 py-3" padded={false}>
      {sparkline?.length > 1 ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-10 opacity-70">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sparkline.map((v) => ({ v }))} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id={`kpi-${label}`} x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#F5B21A" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#F5B21A" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area dataKey="v" fill={`url(#kpi-${label})`} stroke="#F5B21A" strokeWidth={1.5} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : null}
      <div className="relative flex items-start gap-3">
        {Icon ? (
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber/10 text-amber">
            <Icon size={18} />
          </div>
        ) : null}
        <div className="min-w-0">
          <p className="colmena-label">{label}</p>
          <div className="flex items-baseline gap-2">
            <p className="truncate text-xl font-bold text-dark">{value}</p>
            {delta ? <span className={`text-xs font-semibold ${toneClass}`}>{delta}</span> : null}
          </div>
          {hint ? <p className="truncate text-[11px] text-muted">{hint}</p> : null}
        </div>
      </div>
    </Card>
  );
}
