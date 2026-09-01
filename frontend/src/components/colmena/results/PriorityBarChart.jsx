import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { riskColorFor, semanticBandColor } from '../../../utils/chartColors.js';
import { dominantBand, unfavorablePct } from '../../../utils/scoringResults.js';
import { formatPercent } from '../../../utils/format.js';
import { EmptyState } from '../../ui/EmptyState.jsx';

/**
 * Barras horizontales rankeadas por % desfavorable, con línea de referencia
 * al 50% — evita crear un gráfico por dimensión/subdimensión (hasta 20).
 */
export default function PriorityBarChart({ rows, emptyTitle = 'Sin filas publicables', emptyDescription }) {
  if (!rows.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription || 'Calcula el scoring para ver el ranking.'} />;
  }

  const data = rows.map((row) => {
    const band = dominantBand(row);
    return {
      name: row.construct_name,
      code: row.construct_code,
      value: unfavorablePct(row),
      fill: band?.color_hint || (band?.code ? riskColorFor(band.code) : semanticBandColor(band?.label)),
    };
  });

  const height = Math.max(220, data.length * 34);

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.25)" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            ticks={[0, 20, 40, 60, 80, 100]}
            tick={{ fontSize: 11 }}
            tickFormatter={(value) => formatPercent(value, { decimals: 0 })}
          />
          <YAxis dataKey="name" type="category" width={160} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value) => [formatPercent(value, { decimals: 1 }), '% desfavorable']} />
          <ReferenceLine x={50} stroke="#1C1F24" strokeDasharray="4 4" label={{ value: 'Referencia 50%', position: 'top', fontSize: 11 }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]}>
            {data.map((entry) => <Cell key={entry.code || entry.name} fill={entry.fill} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
