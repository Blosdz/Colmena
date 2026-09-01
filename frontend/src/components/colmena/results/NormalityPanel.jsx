import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { runNormality } from '../../../api/analytics.js';
import { formatNumber, formatPValue } from '../../../utils/format.js';
import { CHART_COLORS, CHART_MARGIN } from '../../../utils/chartColors.js';
import { Button } from '../../ui/Button.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';

const STATUS_LABELS = {
  NORMAL: 'Compatible con una distribución normal',
  NO_NORMAL: 'La distribución se aparta de la normal',
  INCONCLUSIVE: 'Resultado inconcluso',
  SUPPRESSED: 'Resultado suprimido',
};

export default function NormalityPanel({ studyId }) {
  const [selected, setSelected] = useState(0);
  const mutation = useMutation({ mutationFn: () => runNormality(studyId, {}) });
  const result = mutation.data?.results?.[selected];

  return (
    <div className="colmena-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-dark">Normalidad de puntajes agregados</p>
          <p className="mt-1 text-xs text-muted">Shapiro–Wilk hasta n=5000; D’Agostino–Pearson para muestras mayores.</p>
        </div>
        <Button variant="primary" size="sm" onClick={() => mutation.mutate()} loading={mutation.isPending}>
          Evaluar normalidad
        </Button>
      </div>

      {mutation.isError ? <p className="text-sm text-danger">{mutation.error?.message}</p> : null}
      {!mutation.data ? (
        <EmptyState
          title="Análisis complementario"
          description="Spearman no exige normalidad. Esta vista documenta la forma de la distribución."
        />
      ) : (
        <>
          <div className="rounded-xl bg-amber/10 px-3 py-2 text-xs text-yellowDark">{mutation.data.note}</div>
          <div className="flex flex-wrap gap-2">
            {mutation.data.results.map((item, index) => (
              <button
                key={item.construct_id}
                type="button"
                onClick={() => setSelected(index)}
                className={`colmena-badge cursor-pointer ${selected === index ? 'bg-amber text-white' : 'bg-amber/10 text-yellowDark'}`}
              >
                {item.construct_name}
              </button>
            ))}
          </div>

          {result ? (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(270px,0.7fr)_minmax(0,2fr)]">
              <div className="rounded-2xl border border-border p-4">
                <p className="text-sm font-semibold text-dark">{result.construct_name}</p>
                <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <Stat label="n" value={result.n} />
                  <Stat label="Prueba" value={result.test || 'Inconclusa'} />
                  <Stat label="Estadístico" value={formatNumber(result.statistic)} />
                  <Stat label="p" value={formatPValue(result.p_value)} />
                  <Stat label="Media" value={formatNumber(result.mean)} />
                  <Stat label="Mediana" value={formatNumber(result.median)} />
                  <Stat label="DE" value={formatNumber(result.standard_deviation)} />
                  <Stat label="Asimetría" value={formatNumber(result.skewness)} />
                  <Stat label="Curtosis" value={formatNumber(result.kurtosis)} />
                  <Stat label="Estado" value={STATUS_LABELS[result.status] || result.status || '—'} />
                </dl>
                {(result.warnings || []).map((warning) => (
                  <p key={warning} className="mt-2 text-xs text-danger">{warning}</p>
                ))}
              </div>

              <div className="h-72 rounded-2xl border border-border p-3">
                <p className="mb-1 text-xs font-semibold text-dark">Distribución de puntajes</p>
                <ResponsiveContainer width="100%" height="92%">
                  <BarChart data={result.histogram} margin={CHART_MARGIN}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
                    <XAxis
                      dataKey="min_value"
                      tickFormatter={(value) => formatNumber(value, { decimals: 0 })}
                      label={{ value: 'Puntaje', position: 'insideBottom', offset: -14, fontSize: 11 }}
                    />
                    <YAxis
                      allowDecimals={false}
                      label={{ value: 'Frecuencia', angle: -90, position: 'insideLeft', fontSize: 11 }}
                    />
                    <Tooltip labelFormatter={(value) => `Desde ${formatNumber(value)}`} />
                    <Bar dataKey="n" name="Frecuencia" fill={CHART_COLORS.primary} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-0.5 font-semibold text-dark">{value}</dd>
    </div>
  );
}
