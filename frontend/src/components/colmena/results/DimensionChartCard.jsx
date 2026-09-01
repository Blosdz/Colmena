import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ShieldAlert } from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { compareConstructGroups } from '../../../api/analytics.js';
import { useOptionLabels } from '../../../hooks/useOptionLabels.js';
import { formatNumber, formatPercent } from '../../../utils/format.js';
import { CATEGORICAL_COLORS, semanticBandColor } from '../../../utils/chartColors.js';
import { Card } from '../../ui/Card.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';

function dominantBandColor(bands = []) {
  if (!bands.length) return CATEGORICAL_COLORS[0];
  const top = bands.reduce((best, band) => ((band.pct || 0) > (best.pct || 0) ? band : best), bands[0]);
  return top.color_hint || semanticBandColor(top.label);
}

function loadStoredConfig(storageKey) {
  try {
    const raw = window.localStorage.getItem(storageKey);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function Privacy() {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-muted">
      <ShieldAlert size={13} /> Suprimido por privacidad
    </span>
  );
}

export default function DimensionChartCard({ studyId, versionId, dimension, subdimensions = [], exogenousFields = [] }) {
  const storageKey = `telemetry-chart:${studyId}:${dimension.construct_id}`;
  const stored = loadStoredConfig(storageKey);
  const [chartType, setChartType] = useState(stored?.chartType || 'bar');
  const [metric, setMetric] = useState(stored?.metric || 'mean');
  const [groupVariableId, setGroupVariableId] = useState(stored?.groupVariableId || '');

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify({ chartType, metric, groupVariableId }));
    } catch {
      // localStorage puede fallar en modo privado; la tarjeta sigue funcionando sin persistir.
    }
  }, [storageKey, chartType, metric, groupVariableId]);

  const { resolveLabel } = useOptionLabels(versionId);
  const selectedField = exogenousFields.find(({ variable }) => String(variable.id) === String(groupVariableId));

  const groupsQuery = useQuery({
    queryKey: ['constructCompareGroups', studyId, dimension.construct_id, groupVariableId],
    queryFn: () =>
      compareConstructGroups(studyId, {
        construct_id: dimension.construct_id,
        group_variable_id: Number(groupVariableId),
      }),
    enabled: chartType === 'bar' && Boolean(groupVariableId),
  });

  if (dimension.suppressed) {
    return (
      <Card>
        <p className="text-sm font-semibold text-dark">{dimension.construct_name}</p>
        <div className="mt-6 flex justify-center"><Privacy /></div>
      </Card>
    );
  }

  const rows = [dimension, ...subdimensions];
  const barData = groupVariableId
    ? (groupsQuery.data?.groups || []).map((group, index) => ({
        name: selectedField ? resolveLabel(selectedField.question.option_set_id, group.code) : group.code,
        value: group.suppressed ? null : group[metric],
        suppressed: group.suppressed,
        fill: CATEGORICAL_COLORS[index % CATEGORICAL_COLORS.length],
      }))
    : rows.map((row) => ({
        name: row.construct_id === dimension.construct_id ? row.construct_name : `↳ ${row.construct_name}`,
        value: row.suppressed ? null : row[metric === 'mean' ? 'mean_score' : 'median_score'],
        suppressed: row.suppressed,
        fill: dominantBandColor(row.bands),
      }));

  const pieData = (dimension.bands || []).map((band) => ({
    name: band.label,
    value: band.pct || 0,
    fill: band.color_hint || semanticBandColor(band.label),
  }));

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-dark">{dimension.construct_name}</p>
          <p className="mt-1 text-xs text-muted">n = {dimension.n_valid} · {dimension.construct_code}</p>
        </div>
        <div className="flex rounded-lg bg-surfaceSoft p-0.5">
          <button type="button" className={`colmena-pill-tab ${chartType === 'bar' ? 'active' : ''}`} onClick={() => setChartType('bar')}>Barras</button>
          <button type="button" className={`colmena-pill-tab ${chartType === 'donut' ? 'active' : ''}`} onClick={() => setChartType('donut')}>Círculos</button>
        </div>
      </div>

      {chartType === 'bar' ? (
        <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
          <div className="flex rounded-lg bg-surfaceSoft p-0.5">
            <button type="button" className={`colmena-pill-tab ${metric === 'mean' ? 'active' : ''}`} onClick={() => setMetric('mean')}>Media</button>
            <button type="button" className={`colmena-pill-tab ${metric === 'median' ? 'active' : ''}`} onClick={() => setMetric('median')}>Mediana</button>
          </div>
          <label className="flex flex-col gap-1">
            <span className="colmena-label">Filtrar por variable</span>
            <select
              className="colmena-input h-9 px-3 text-xs"
              value={groupVariableId}
              onChange={(event) => setGroupVariableId(event.target.value)}
            >
              <option value="">Sin filtro</option>
              {exogenousFields.map(({ variable }) => (
                <option key={variable.id} value={variable.id}>{variable.name}</option>
              ))}
            </select>
          </label>
        </div>
      ) : (
        <p className="mt-3 text-xs text-muted">
          Las bandas se calculan sobre el total del estudio; el filtro por variable no aplica en esta vista.
        </p>
      )}

      <div className="mt-4 h-64">
        {chartType === 'bar' ? (
          groupVariableId && groupsQuery.isLoading ? (
            <div className="flex h-full items-center justify-center text-xs text-muted">Calculando…</div>
          ) : barData.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.25)" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(value) => formatNumber(value, { decimals: 1 })} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {barData.map((entry) => <Cell key={entry.name} fill={entry.suppressed ? '#D1D5DB' : entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="Sin datos" description="No hay grupos para mostrar con este filtro." />
          )
        ) : pieData.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius="55%" outerRadius="85%" paddingAngle={2}>
                {pieData.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
              </Pie>
              <Tooltip formatter={(value) => formatPercent(value, { decimals: 1 })} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState title="Sin bandas configuradas" description="Este baremo no tiene bandas definidas para esta dimensión." />
        )}
      </div>
    </Card>
  );
}
