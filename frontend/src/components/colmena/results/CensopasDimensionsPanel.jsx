import { useQuery } from '@tanstack/react-query';
import { ShieldAlert } from 'lucide-react';

import { getCensopasResults } from '../../../api/studies.js';
import { formatPercent } from '../../../utils/format.js';
import { displayLabel } from '../../../utils/labels.js';
import { EmptyState } from '../../ui/EmptyState.jsx';
import { LoadingState } from '../../ui/LoadingState.jsx';
import DimensionsStackedChart, { BANDS } from './DimensionsStackedChart.jsx';
import PriorityBarChart from './PriorityBarChart.jsx';

const NFIELD_BY_KEY = { Favorable: 'favorable_n', Intermedio: 'intermediate_n', Desfavorable: 'unfavorable_n' };

function Privacy() {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-muted">
      <ShieldAlert size={13} /> Suprimido por privacidad
    </span>
  );
}

/**
 * Vista D1-D6 (o S1-S20 en MEDIA): barra apilada 100% + tabla exacta +
 * priorización, todas alimentadas por el mismo contrato trichotomy
 * (`GET /studies/{id}/censopas/results`, `construct_type` filtrado). Ninguna
 * de las tres secciones recalcula favorable/intermedio/desfavorable — leen
 * los campos que el backend ya resolvió.
 *
 * `dimensionByCode` (subdimension_code -> dimension_code, del árbol de
 * constructos) + `filterDimensionCode` permiten el drilldown: al llegar
 * desde el Resumen con una dimensión seleccionada, sólo se listan sus
 * subdimensiones en vez de las 20.
 */
export default function CensopasDimensionsPanel({
  studyId,
  constructType,
  title,
  emptyTitle = 'Aún no hay resultados calculados',
  emptyDescription = 'Ve a la pestaña Baremos y ejecuta "Calcular resultados".',
  dimensionByCode,
  filterDimensionCode,
  onSelectConstruct,
}) {
  const { data, isLoading } = useQuery({
    queryKey: ['censopasResults', studyId],
    queryFn: () => getCensopasResults(studyId),
    enabled: Boolean(studyId),
  });

  if (isLoading) return <LoadingState label="Cargando resultados…" />;

  const allResults = data?.results || [];
  let rows = allResults
    .filter((result) => result.construct_type === constructType)
    .sort((a, b) => a.construct_code.localeCompare(b.construct_code, 'es'));
  if (filterDimensionCode && dimensionByCode) {
    rows = rows.filter((row) => dimensionByCode[row.construct_code] === filterDimensionCode);
  }

  if (!rows.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  const reference = rows[0];
  const priorityRows = rows
    .filter((row) => !row.suppressed && row.priority_rank != null)
    .sort((a, b) => a.priority_rank - b.priority_rank);

  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="rounded-2xl border border-border bg-surfaceSoft p-4 text-sm text-muted">
        Baremo:{' '}
        <strong className="text-dark">{displayLabel(reference.barem_status, 'Sin baremo activo')}</strong>
        {' · '}
        Equivalencia oficial CENSOPAS: <strong className="text-dark">{reference.official_equivalence ? 'Sí' : 'No'}</strong>
        {!reference.official_equivalence ? (
          <span> — resultado de referencia, no equivale al reporte oficial CENSOPAS.</span>
        ) : null}
      </div>

      <DimensionsStackedChart rows={rows} title={`${title} — distribución (%)`} onSelectConstruct={onSelectConstruct} />

      <div className="overflow-x-auto rounded-2xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-surfaceSoft">
            <tr>
              <th className="px-4 py-3">{title}</th>
              {BANDS.map((band) => (
                <th key={band.key} className="px-4 py-3">{band.key}</th>
              ))}
              <th className="px-4 py-3">n válido</th>
              <th className="px-4 py-3">Nivel</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.construct_id} className="border-t border-border">
                <td className="px-4 py-3">
                  <p className="font-medium text-dark">{row.construct_code}</p>
                  <p className="text-xs text-muted">{row.construct_name}</p>
                </td>
                {row.suppressed ? (
                  <td colSpan={5} className="px-4 py-3"><Privacy /></td>
                ) : (
                  <>
                    {BANDS.map((band) => (
                      <td key={band.key} className="px-4 py-3">
                        {row[NFIELD_BY_KEY[band.key]]} ({formatPercent(row[band.pctField], { decimals: 1 })})
                      </td>
                    ))}
                    <td className="px-4 py-3">{row.n_valid}</td>
                    <td className="px-4 py-3">{displayLabel(row.collective_classification)}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {priorityRows.length ? (
        <div className="rounded-2xl border border-border bg-white p-5">
          <p className="mb-1 text-sm font-semibold text-dark">Priorización — % desfavorable</p>
          <p className="mb-4 text-xs text-muted">
            Orden y porcentaje calculados por el backend (priority_rank / unfavorable_pct) — nunca recalculados aquí.
          </p>
          <PriorityBarChart rows={priorityRows} />
        </div>
      ) : null}
    </div>
  );
}
