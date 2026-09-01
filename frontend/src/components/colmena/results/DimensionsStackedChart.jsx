import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { RISK_COLORS } from '../../../utils/chartColors.js';
import { formatPercent } from '../../../utils/format.js';

// Único gráfico admitido para D1-D6/S1-S20: barra horizontal apilada al
// 100% (favorable/intermedio/desfavorable). Nunca pie/donut ni un gráfico
// por dimensión — la guía CENSOPAS-COPSOQ lo prescribe explícitamente.
// Extraído de CensopasDimensionsPanel para reutilizarse también como
// gráfico principal del Resumen de Telemetría (con drilldown opcional).
export const BANDS = [
  { key: 'Favorable', pctField: 'favorable_pct', color: RISK_COLORS.favorable },
  { key: 'Intermedio', pctField: 'intermediate_pct', color: RISK_COLORS.intermediate },
  { key: 'Desfavorable', pctField: 'unfavorable_pct', color: RISK_COLORS.unfavorable },
];

export default function DimensionsStackedChart({ rows, title, onSelectConstruct }) {
  const chartData = rows
    .filter((row) => !row.suppressed)
    .map((row) => ({
      name: `${row.construct_code} · ${row.construct_name}`,
      code: row.construct_code,
      n_valid: row.n_valid,
      ...Object.fromEntries(BANDS.map((band) => [band.key, row[band.pctField] || 0])),
    }));

  if (!chartData.length) return null;

  const handleClick = (entry) => {
    if (onSelectConstruct && entry?.code) onSelectConstruct(entry.code);
  };

  return (
    <div className="rounded-2xl border border-border bg-white p-5">
      {title ? <p className="mb-4 text-sm font-semibold text-dark">{title}</p> : null}
      <div style={{ height: Math.max(220, chartData.length * 56) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 100]}
              ticks={[0, 20, 40, 60, 80, 100]}
              tick={{ fontSize: 11 }}
              tickFormatter={(value) => formatPercent(value, { decimals: 0 })}
            />
            <YAxis dataKey="name" type="category" width={220} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(value) => formatPercent(value, { decimals: 1 })} />
            {BANDS.map((band) => (
              <Bar
                key={band.key}
                dataKey={band.key}
                stackId="levels"
                fill={band.color}
                cursor={onSelectConstruct ? 'pointer' : 'default'}
                onClick={handleClick}
              >
                <LabelList
                  dataKey={band.key}
                  position="center"
                  formatter={(value) => (value >= 8 ? formatPercent(value, { decimals: 0 }) : '')}
                  fill="#fff"
                  fontSize={11}
                  fontWeight={700}
                />
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
