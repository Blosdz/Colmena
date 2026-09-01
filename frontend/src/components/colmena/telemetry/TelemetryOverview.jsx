import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { AlertCircle, CheckCircle2, Clock, FileCheck2, Gauge, Mail, Users } from 'lucide-react';

import { Card } from '../../ui/Card.jsx';
import KpiCard from './KpiCard.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';
import { formatPercent } from '../../../utils/format.js';

const CHART_COLORS = {
  valid: '#11B7B2',
  excluded: '#DC2626',
  review: '#D97706',
  abandoned: '#94A3B8',
  notResponded: '#CBD5E1',
  started: '#F5B21A',
};

function formatDuration(seconds) {
  if (seconds === null || seconds === undefined) return '—';
  const rounded = Math.round(seconds);
  if (rounded < 60) return `${rounded}s`;
  return `${Math.floor(rounded / 60)}m ${rounded % 60}s`;
}

/** `fraction` va en [0, 1] (como lo devuelve el backend); formatPercent
 * espera [0, 100], de ahí la multiplicación. */
function formatFraction(fraction, decimals = 1) {
  if (fraction === null || fraction === undefined) return null;
  return formatPercent(fraction * 100, { decimals });
}

function ChartCard({ title, description, children, className = '' }) {
  return (
    <Card className={`flex flex-col ${className}`}>
      <p className="text-sm font-semibold text-dark">{title}</p>
      {description ? <p className="mt-1 text-xs text-muted">{description}</p> : null}
      <div className="mt-4 flex-1">{children}</div>
    </Card>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-white px-3 py-2 text-xs shadow-card">
      {label ? <p className="mb-1 font-semibold text-dark">{label}</p> : null}
      {payload.map((item) => (
        <p key={item.dataKey || item.name} className="text-muted">
          <span className="font-medium text-dark">{item.name}</span>: {item.value}
        </p>
      ))}
    </div>
  );
}

/**
 * Único punto de entrada visual de Telemetría (harness: "¿cómo avanza la
 * captura y qué calidad tiene?"). No consume /results/overview ni
 * compare-groups: eso es Resultados/Analítica, no Telemetría.
 */
export default function TelemetryOverview({ telemetry, descriptives, isLoading }) {
  if (isLoading) {
    return <div className="h-48 animate-pulse rounded-2xl border border-border bg-white/60" />;
  }
  if (!telemetry) {
    return (
      <Card>
        <EmptyState
          title="Todavía no hay telemetría"
          description="Elige una aplicación con sesiones para ver participación y calidad de captura."
        />
      </Card>
    );
  }

  // Convocados sólo existe cuando el estudio exige invitación individual y
  // hay invitaciones emitidas (ver TelemetryService._participation_funnel
  // en el backend). En estudios de enlace público no hay población objetivo
  // contable, así que no se fabrica una tasa con un denominador inventado.
  const hasInvitations = telemetry.invited_count !== null && telemetry.invited_count !== undefined;
  const validOverStarted = telemetry.started_count ? telemetry.valid_count / telemetry.started_count : null;
  const summary = descriptives?.summary;
  const answeredPct = summary ? Math.max(0, 100 - summary.missing_pct) : null;

  const series = telemetry.series || [];
  const completedSeries = series.map((point) => point.completed ?? 0);
  const lastCompleted = completedSeries.at(-1);
  const prevCompleted = completedSeries.at(-2);
  const completedDelta = lastCompleted !== undefined && prevCompleted !== undefined ? lastCompleted - prevCompleted : null;

  const kpis = hasInvitations
    ? [
        { icon: Mail, label: 'Convocados', value: telemetry.invited_count },
        { icon: Users, label: 'Recibidos', value: telemetry.started_count, sparkline: completedSeries },
        { icon: CheckCircle2, label: 'Válidos', value: telemetry.valid_count },
        {
          icon: FileCheck2,
          label: 'Tasa válida',
          value: formatFraction(telemetry.valid_rate) ?? '—',
          hint: `${telemetry.valid_count}/${telemetry.invited_count}`,
        },
        {
          icon: AlertCircle,
          label: 'No respondió',
          value: telemetry.not_responded_count,
          hint: formatFraction(telemetry.not_responded_count / telemetry.invited_count) || undefined,
        },
        {
          icon: Clock,
          label: 'Duración mediana',
          value: formatDuration(telemetry.median_duration_seconds),
          delta: completedDelta === null ? null : `${completedDelta >= 0 ? '▲' : '▼'} ${Math.abs(completedDelta)} hoy`,
          deltaTone: completedDelta === null ? 'neutral' : completedDelta >= 0 ? 'up' : 'down',
        },
      ]
    : [
        { icon: Users, label: 'Recibidos', value: telemetry.started_count, sparkline: completedSeries },
        { icon: CheckCircle2, label: 'Válidos', value: telemetry.valid_count },
        {
          icon: FileCheck2,
          label: 'Tasa válida (sobre recibidos)',
          value: validOverStarted === null ? '—' : formatFraction(validOverStarted),
          hint: `${telemetry.valid_count}/${telemetry.started_count}`,
        },
        {
          icon: Gauge,
          label: 'Ítems respondidos',
          value: answeredPct === null ? '—' : formatPercent(answeredPct, { decimals: 1 }),
        },
        {
          icon: Clock,
          label: 'Duración mediana',
          value: formatDuration(telemetry.median_duration_seconds),
          delta: completedDelta === null ? null : `${completedDelta >= 0 ? '▲' : '▼'} ${Math.abs(completedDelta)} hoy`,
          deltaTone: completedDelta === null ? 'neutral' : completedDelta >= 0 ? 'up' : 'down',
        },
      ];

  const statusBreakdown = [
    { key: 'valid', name: 'Válidos', value: telemetry.valid_count, color: CHART_COLORS.valid },
    { key: 'review', name: 'En revisión', value: telemetry.review_count, color: CHART_COLORS.review },
    { key: 'abandoned', name: 'Incompletos', value: telemetry.abandoned_count, color: CHART_COLORS.abandoned },
    { key: 'excluded', name: 'Excluidos', value: telemetry.excluded_count, color: CHART_COLORS.excluded },
    hasInvitations
      ? { key: 'notResponded', name: 'No respondió', value: telemetry.not_responded_count, color: CHART_COLORS.notResponded }
      : null,
  ].filter((slice) => slice && slice.value > 0);

  const funnelData = hasInvitations
    ? [
        { name: 'Convocados', value: telemetry.invited_count },
        { name: 'Respondieron', value: telemetry.started_count },
        { name: 'Válidos', value: telemetry.valid_count },
      ]
    : [
        { name: 'Iniciaron', value: telemetry.started_count },
        { name: 'Válidos', value: telemetry.valid_count },
      ];

  const qualityGauge = [{ name: 'Ítems respondidos', value: answeredPct ?? 0, fill: '#11B7B2' }];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {kpis.map((kpi) => <KpiCard key={kpi.label} {...kpi} />)}
      </div>

      {!hasInvitations ? (
        <p className="text-xs text-muted">
          Convocados no disponible: este estudio no exige invitación individual (enlace público), así
          que el sistema no tiene registrada una población objetivo para calcular la tasa recibida.
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard
          description={hasInvitations ? 'Convocados → respondieron → válidos.' : 'Iniciaron → válidos, sobre las sesiones recibidas.'}
          title="Embudo de participación"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer height="100%" width="100%">
              <BarChart data={funnelData} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
                <CartesianGrid horizontal={false} stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
                <XAxis allowDecimals={false} type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" tick={{ fontSize: 12, fill: '#111111' }} type="category" width={100} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(245,178,26,0.06)' }} />
                <Bar dataKey="value" fill="#F5B21A" name="Sesiones" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard description="Distribución del total de sesiones recibidas por resultado." title="Estado de las sesiones">
          {statusBreakdown.length ? (
            <div className="flex h-64 w-full items-center gap-4">
              <ResponsiveContainer height="100%" width="60%">
                <PieChart>
                  <Pie
                    cx="50%"
                    cy="50%"
                    data={statusBreakdown}
                    dataKey="value"
                    innerRadius="55%"
                    nameKey="name"
                    outerRadius="85%"
                    paddingAngle={2}
                  >
                    {statusBreakdown.map((slice) => <Cell key={slice.key} fill={slice.color} />)}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <ul className="flex-1 space-y-2 text-xs">
                {statusBreakdown.map((slice) => (
                  <li key={slice.key} className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2 text-dark">
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: slice.color }} />
                      {slice.name}
                    </span>
                    <span className="shrink-0 font-semibold text-dark">{slice.value}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <EmptyState description="Aparecerá con las primeras sesiones." title="Sin sesiones todavía" />
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(240px,1fr)]">
        <ChartCard description="Sesiones iniciadas y completadas por día." title="Evolución de respuestas">
          {series.length ? (
            <div className="h-64 w-full">
              <ResponsiveContainer height="100%" width="100%">
                <AreaChart data={series}>
                  <defs>
                    <linearGradient id="telemetryStarted" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#F5B21A" stopOpacity={0.32} />
                      <stop offset="100%" stopColor="#F5B21A" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="telemetryCompleted" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#11B7B2" stopOpacity={0.28} />
                      <stop offset="100%" stopColor="#11B7B2" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                  <Area dataKey="started" fill="url(#telemetryStarted)" name="Iniciadas" stroke="#F5B21A" strokeWidth={2} />
                  <Area dataKey="completed" fill="url(#telemetryCompleted)" name="Completadas" stroke="#11B7B2" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState description="La serie aparecerá con las primeras sesiones." title="Sin evolución todavía" />
          )}
        </ChartCard>

        <ChartCard description="Los análisis y la matriz usan únicamente casos válidos." title="Calidad de captura">
          <div className="flex h-40 items-center justify-center">
            <ResponsiveContainer height="100%" width="100%">
              <RadialBarChart
                barSize={14}
                cx="50%"
                cy="50%"
                data={qualityGauge}
                endAngle={-40}
                innerRadius="70%"
                outerRadius="100%"
                startAngle={220}
              >
                <RadialBar background={{ fill: '#F1F3F5' }} cornerRadius={8} dataKey="value" max={100} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
          <p className="-mt-6 text-center text-2xl font-bold text-dark">
            {answeredPct === null ? '—' : formatPercent(answeredPct, { decimals: 1 })}
          </p>
          <p className="text-center text-[11px] text-muted">ítems respondidos{summary ? ` · ${summary.missing_cells} faltante(s)` : ''}</p>
          <dl className="mt-4 space-y-2 border-t border-border/70 pt-3 text-xs">
            {[
              ['Incompletos', telemetry.abandoned_count, 'text-muted'],
              ['En revisión', telemetry.review_count, 'text-warning'],
              ['Excluidos', telemetry.excluded_count, 'text-danger'],
            ].map(([label, value, tone]) => (
              <div key={label} className="flex items-center justify-between">
                <dt className="text-muted">{label}</dt>
                <dd className={`font-bold ${tone}`}>{value}</dd>
              </div>
            ))}
          </dl>
        </ChartCard>
      </div>
    </div>
  );
}
