import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { getResultsOverview, listStudies } from '../../../api/studies.js';
import { formatPercent } from '../../../utils/format.js';
import { unfavorablePct } from '../../../utils/scoringResults.js';
import { Card } from '../../ui/Card.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';
import { LoadingState } from '../../ui/LoadingState.jsx';

/** Firma de comparabilidad: dos mediciones sólo son equivalentes si comparten
 * versión de instrumento y baremo (harness §31 aplicado a series temporales:
 * nunca comparar mediciones con metodología distinta). */
function signatureOf(overview) {
  return `${overview.instrument_version_id ?? 'none'}::${overview.barem_id ?? 'none'}`;
}

export default function EvolutionPanel({ projectId }) {
  const { data: overviews, isLoading, isError } = useQuery({
    queryKey: ['projectEvolutionOverviews', projectId],
    queryFn: async () => {
      const studiesPage = await listStudies(projectId, { page: 1, pageSize: 100 });
      const studies = (studiesPage?.items || []).filter((study) => study.instrument_version_id);
      const results = await Promise.all(studies.map((study) => getResultsOverview(study.id)));
      return studies.map((study, index) => ({ study, overview: results[index] }));
    },
    enabled: Boolean(projectId),
  });

  const indicators = useMemo(() => {
    const found = [];
    (overviews || []).forEach(({ overview }) => {
      (overview.results || []).forEach((result) => {
        if (result.construct_type !== 'DIMENSION' && result.construct_type !== 'VARIABLE') return;
        if (!found.some((item) => item.code === result.construct_code)) {
          found.push({ code: result.construct_code, name: result.construct_name });
        }
      });
    });
    return found;
  }, [overviews]);

  const [constructCode, setConstructCode] = useState('');
  useEffect(() => {
    if (!constructCode && indicators.length) setConstructCode(indicators[0].code);
  }, [constructCode, indicators]);

  if (isLoading) return <LoadingState label="Cargando evolución del proyecto..." />;
  if (isError) return <div className="p-4 text-sm font-medium text-danger">No se pudo cargar la evolución del proyecto.</div>;

  if (!overviews?.length || !indicators.length) {
    return (
      <div className="p-4">
        <EmptyState
          title="Aún no hay mediciones para comparar"
          description="Necesitas al menos una aplicación con scoring calculado sobre una dimensión o variable."
        />
      </div>
    );
  }

  const points = (overviews || [])
    .map(({ study, overview }) => {
      const result = (overview.results || []).find((item) => item.construct_code === constructCode);
      if (!result || result.suppressed) return null;
      return {
        studyId: study.id,
        studyName: study.name,
        date: study.start_at || null,
        signature: signatureOf(overview),
        instrumentVersionId: overview.instrument_version_id,
        baremId: overview.barem_id,
        n_valid: result.n_valid,
        value: unfavorablePct(result),
      };
    })
    .filter(Boolean)
    .sort((a, b) => {
      if (a.date && b.date) return new Date(a.date) - new Date(b.date);
      if (a.date) return -1;
      if (b.date) return 1;
      return a.studyId - b.studyId;
    });

  // La firma más frecuente (empate → la más reciente, ya que `points` está
  // ordenado cronológicamente) define la serie comparable; el resto se
  // muestra aparte, nunca conectado en la línea.
  const counts = new Map();
  points.forEach((point) => counts.set(point.signature, (counts.get(point.signature) || 0) + 1));
  const bestCount = Math.max(0, ...counts.values());
  const tiedSignatures = new Set([...counts.entries()].filter(([, count]) => count === bestCount).map(([sig]) => sig));
  let referenceSignature = null;
  for (let index = points.length - 1; index >= 0; index -= 1) {
    if (tiedSignatures.has(points[index].signature)) {
      referenceSignature = points[index].signature;
      break;
    }
  }

  const comparablePoints = points.filter((point) => point.signature === referenceSignature);
  const excludedPoints = points.filter((point) => point.signature !== referenceSignature);
  const chartData = comparablePoints.map((point) => ({
    label: point.date ? new Date(point.date).toLocaleDateString('es-PE', { year: 'numeric', month: 'short' }) : point.studyName,
    studyName: point.studyName,
    value: point.value,
  }));

  return (
    <div className="flex flex-col gap-4 p-4">
      <Card>
        <label className="flex max-w-sm flex-col gap-2">
          <span className="colmena-label">Indicador</span>
          <select className="colmena-input h-10 px-4 text-sm" value={constructCode} onChange={(event) => setConstructCode(event.target.value)}>
            {indicators.map((indicator) => (
              <option key={indicator.code} value={indicator.code}>{indicator.name}</option>
            ))}
          </select>
        </label>
      </Card>

      <Card>
        <p className="text-sm font-semibold text-dark">Evolución de exposición desfavorable</p>
        <p className="mt-1 text-xs text-muted">
          Sólo se conecta con una línea a las aplicaciones con la misma versión de instrumento y el mismo baremo —
          comparar mediciones con metodología distinta no es válido.
        </p>
        {chartData.length >= 1 ? (
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} tickFormatter={(value) => formatPercent(value, { decimals: 0 })} />
                <Tooltip
                  formatter={(value) => [formatPercent(value, { decimals: 1 }), '% desfavorable']}
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.studyName || ''}
                />
                <Line type="monotone" dataKey="value" name="% desfavorable" stroke="#DC2626" strokeWidth={3} dot={{ r: 5 }} activeDot={{ r: 7 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="mt-4">
            <EmptyState title="Sin puntos comparables" description="Ninguna aplicación tiene un resultado publicable para este indicador." />
          </div>
        )}
      </Card>

      {excludedPoints.length ? (
        <Card className="border-warning/30 bg-amber/5">
          <div className="flex items-start gap-2">
            <AlertTriangle size={16} className="mt-0.5 shrink-0 text-warning" />
            <div className="text-xs leading-5 text-dark">
              <p className="font-semibold">No es posible comparar estas mediciones como una serie equivalente:</p>
              <ul className="mt-1.5 space-y-1">
                {excludedPoints.map((point) => {
                  const reference = comparablePoints[0];
                  const reasons = [];
                  if (reference && point.instrumentVersionId !== reference.instrumentVersionId) reasons.push('usa otra versión de instrumento');
                  if (reference && point.baremId !== reference.baremId) reasons.push('usa otro baremo');
                  return (
                    <li key={point.studyId}>
                      <span className="font-medium">{point.studyName}</span>
                      {reasons.length ? ` — ${reasons.join(' y ')}.` : ' — metodología distinta.'} Sus resultados pueden
                      consultarse por separado en Resultados → Baremos de esa aplicación.
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
