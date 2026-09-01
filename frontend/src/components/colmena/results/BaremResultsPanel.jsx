import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Calculator, ShieldAlert } from 'lucide-react';

import { formatNumber, formatPercent } from '../../../utils/format.js';
import { semanticBandColor, semanticBandOrder } from '../../../utils/chartColors.js';
import { displayLabel } from '../../../utils/labels.js';
import { getResultsOverview, getStudy, listBarems, runScoring, updateStudy } from '../../../api/studies.js';
import { Button } from '../../ui/Button.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';
import { LoadingState } from '../../ui/LoadingState.jsx';

const FALLBACK_COLORS = ['#ef4444', '#f59e0b', '#22c55e', '#2563eb', '#7c3aed'];

export default function BaremResultsPanel({ studyId }) {
  const queryClient = useQueryClient();
  const { data: study } = useQuery({ queryKey: ['study', studyId], queryFn: () => getStudy(studyId) });
  const { data: barems = [] } = useQuery({ queryKey: ['barems', study?.instrument_version_id], queryFn: () => listBarems(study.instrument_version_id), enabled: Boolean(study?.instrument_version_id) });
  const { data: overview, isLoading } = useQuery({ queryKey: ['resultsOverview', studyId], queryFn: () => getResultsOverview(studyId) });

  const selectBarem = useMutation({
    mutationFn: (baremId) => updateStudy(studyId, { barem_id: baremId ? Number(baremId) : null }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['study', studyId] }); queryClient.invalidateQueries({ queryKey: ['resultsOverview', studyId] }); },
  });
  const scoring = useMutation({
    mutationFn: () => runScoring(studyId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['resultsOverview', studyId] }),
  });

  if (isLoading || !study) return <LoadingState label="Cargando resultados…" />;
  const labels = [];
  (overview?.results || []).forEach((result) => result.bands.forEach((band) => { if (!labels.some((item) => item.label === band.label)) labels.push(band); }));
  labels.sort((a, b) => semanticBandOrder(a.label) - semanticBandOrder(b.label));
  const allResults = overview?.results || [];
  // Color oficial del baremo (color_hint) por etiqueta de banda — nunca el heurístico por
  // texto salvo que el backend no haya devuelto un color_hint para esa banda.
  const colorByLabel = new Map();
  allResults.forEach((result) => result.bands.forEach((band) => {
    if (band.color_hint && !colorByLabel.has(band.label)) colorByLabel.set(band.label, band.color_hint);
  }));
  const childrenByParent = new Map();
  allResults.forEach((result) => {
    const children = childrenByParent.get(result.parent_id) || [];
    children.push(result);
    childrenByParent.set(result.parent_id, children);
  });
  const orderedResults = [];
  const visitedResults = new Set();
  const appendBranch = (result, depth = 0) => {
    if (visitedResults.has(result.construct_id)) return;
    visitedResults.add(result.construct_id);
    orderedResults.push({ ...result, depth });
    (childrenByParent.get(result.construct_id) || []).forEach((child) => appendBranch(child, depth + 1));
  };
  (childrenByParent.get(null) || []).forEach((root) => appendBranch(root));
  allResults.forEach((result) => appendBranch(result));
  const chartData = orderedResults.filter((result) => !result.suppressed).map((result) => ({
    name: `${result.depth ? '↳ ' : ''}${result.construct_name}`,
    ...Object.fromEntries(result.bands.map((band) => [band.label, band.pct || 0])),
  }));
  const variableCount = allResults.filter((result) => result.parent_id === null).length;

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex flex-wrap items-end justify-between gap-4 rounded-2xl border border-border bg-surfaceSoft p-5">
        <div className="flex min-w-72 flex-col gap-2">
          <span className="colmena-label">Baremo del estudio</span>
          <select className="colmena-input h-10 px-4 text-sm" value={study.barem_id || ''} onChange={(event) => selectBarem.mutate(event.target.value)}>
            <option value="">Sin baremo (sólo puntajes)</option>
            {barems.map((barem) => <option key={barem.id} value={barem.id}>{barem.name} · {displayLabel(barem.status)}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-3">
          {overview?.algorithm_version ? <span className="text-xs text-muted">Algoritmo {overview.algorithm_version} · corrida #{overview.analysis_run_id}</span> : null}
          <Button variant="primary" size="sm" onClick={() => scoring.mutate()} loading={scoring.isPending}><Calculator size={15} className="mr-1" /> Calcular resultados</Button>
        </div>
      </div>
      {scoring.isError ? <p className="rounded-xl bg-danger/10 p-4 text-sm text-danger">{scoring.error?.message || 'No se pudo calcular el scoring.'}</p> : null}
      {overview?.analysis_run_id && Number(overview.barem_id || 0) !== Number(study.barem_id || 0) ? <p className="rounded-xl bg-amber/10 p-4 text-sm text-yellowDark">El baremo seleccionado cambió después de la última corrida. Pulsa “Calcular resultados” para aplicar el nuevo baremo; la tabla actual conserva la corrida anterior.</p> : null}

      {!overview?.results?.length ? <EmptyState title="Aún no hay resultados calculados" description="Elige un baremo —o deja sólo puntajes— y ejecuta el cálculo. Los resultados quedan guardados por corrida." /> : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Metric label="Respuestas completas" value={overview.n_completed} />
            <Metric label="Variables" value={variableCount} />
            <Metric label="Baremo" value={overview.barem_name || 'Sin clasificación'} />
            <Metric label="Privacidad mínima" value={`n ≥ ${overview.min_publishable_n}`} />
          </div>

          {chartData.length && labels.length ? <div className="h-[420px] rounded-2xl border border-border bg-white p-5"><p className="mb-4 text-sm font-semibold text-dark">Distribución por niveles (%)</p><ResponsiveContainer width="100%" height="90%"><BarChart data={chartData} layout="vertical" margin={{ left: 30, right: 20 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]} tickFormatter={(value) => formatPercent(value)} /><YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 11 }} /><Tooltip /><Legend />{labels.map((band, index) => <Bar key={band.label} dataKey={band.label} stackId="levels" fill={colorByLabel.get(band.label) || semanticBandColor(band.label)}><LabelList dataKey={band.label} position="center" formatter={(value) => value >= 8 ? formatPercent(value) : ''} fill="#fff" fontSize={11} fontWeight={700} /></Bar>)}</BarChart></ResponsiveContainer></div> : null}

          <div className="overflow-x-auto rounded-2xl border border-border"><table className="w-full text-left text-sm"><thead className="bg-surfaceSoft"><tr><th className="px-4 py-3">Prioridad</th><th className="px-4 py-3">Variable / dimensión</th><th className="px-4 py-3">n</th><th className="px-4 py-3">Puntaje</th>{labels.map((band) => <th key={band.label} className="px-4 py-3">{band.label}</th>)}</tr></thead><tbody>{orderedResults.map((result) => <tr key={result.construct_id} className="border-t border-border"><td className="px-4 py-3 font-semibold">#{result.priority_rank || '—'}</td><td className="px-4 py-3"><div style={{ paddingLeft: `${result.depth * 18}px` }}><p className="font-medium text-dark">{result.depth ? '↳ ' : ''}{result.construct_name}</p><p className="text-xs text-muted">{result.depth ? 'Dimensión' : 'Variable'} · {result.construct_code}</p></div></td><td className="px-4 py-3">{result.n_valid}</td><td className="px-4 py-3">{result.suppressed ? <Privacy /> : formatNumber(result.mean_score)}</td>{labels.map((label) => { const band = result.bands.find((item) => item.label === label.label); return <td key={label.label} className="px-4 py-3">{result.suppressed ? <Privacy /> : band ? `${band.n} (${band.pct?.toFixed(1)}%)` : '—'}</td>; })}</tr>)}</tbody></table></div>
          <p className="text-xs leading-5 text-muted">Las barras muestran distribución, no causalidad. Los colores siempre se acompañan de etiquetas y porcentajes. En proyectos de Censo, las celdas con n menor al mínimo se suprimen desde el backend.</p>
        </>
      )}
    </div>
  );
}

function Metric({ label, value }) { return <div className="rounded-2xl border border-border bg-white p-4"><p className="text-xs text-muted">{label}</p><p className="mt-2 text-lg font-bold text-dark">{value}</p></div>; }
function Privacy() { return <span className="inline-flex items-center gap-1 text-xs text-muted"><ShieldAlert size={13} /> Suprimido</span>; }
