import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { LayoutDashboard } from 'lucide-react';

import { getCensopasReadiness } from '../../../api/instruments.js';
import { getResultsOverview, getStudy } from '../../../api/studies.js';
import { listExogenousFields } from '../../../api/variables.js';
import { EmptyState } from '../../ui/EmptyState.jsx';
import { LoadingState } from '../../ui/LoadingState.jsx';
import MetricCard from '../../ui/MetricCard.jsx';
import CensopasDimensionsPanel from './CensopasDimensionsPanel.jsx';
import DimensionChartCard from './DimensionChartCard.jsx';

/**
 * Router de la pestaña "Dimensiones": los estudios CENSOPAS-COPSOQ tienen su
 * propio contrato trichotomy (favorable/intermedio/desfavorable) y su propia
 * visual obligatoria (barra apilada 100%, nunca pie/donut) — el dashboard
 * genérico de constructos (tarjetas por dimensión, círculos incluidos) sigue
 * existiendo para instrumentos Likert que no son CENSOPAS.
 */
export default function DimensionDashboardTab({ projectId, studyId }) {
  const { data: study, isLoading: isLoadingStudy } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => getStudy(studyId),
    enabled: Boolean(studyId),
  });
  const { data: readiness, isLoading: isLoadingReadiness } = useQuery({
    queryKey: ['censopas-readiness', study?.instrument_version_id],
    queryFn: () => getCensopasReadiness(study.instrument_version_id),
    enabled: Boolean(study?.instrument_version_id),
    retry: false,
  });

  if (!studyId) {
    return (
      <div className="p-4">
        <EmptyState title="Elige una aplicación o estudio." description="Los puntajes por dimensión se calculan por cada aplicación del instrumento." />
      </div>
    );
  }
  if (isLoadingStudy || (study?.instrument_version_id && isLoadingReadiness)) {
    return <LoadingState label="Cargando resultados…" />;
  }

  if (readiness?.is_censopas_instrument) {
    return <CensopasDimensionsPanel studyId={studyId} constructType="DIMENSION" title="Dimensiones" />;
  }

  return <GenericDimensionDashboard projectId={projectId} studyId={studyId} />;
}

function GenericDimensionDashboard({ projectId, studyId }) {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['resultsOverview', studyId],
    queryFn: () => getResultsOverview(studyId),
    enabled: Boolean(studyId),
  });
  const { data: exogenousFields = [] } = useQuery({
    queryKey: ['exogenousFields', projectId],
    queryFn: () => listExogenousFields(projectId),
    enabled: Boolean(projectId),
  });

  const results = overview?.results || [];
  const roots = results.filter((result) => result.parent_id === null);
  const dimensions = results.filter((result) => result.construct_type === 'DIMENSION');
  const childrenByParent = new Map();
  results.forEach((result) => {
    const siblings = childrenByParent.get(result.parent_id) || [];
    siblings.push(result);
    childrenByParent.set(result.parent_id, siblings);
  });

  return (
    <div className="flex flex-col gap-4 p-4">
      {isLoading ? (
        <LoadingState label="Cargando resultados…" />
      ) : results.length === 0 ? (
        <EmptyState
          title="Aún no hay resultados calculados"
          description="Ve a Resultados → Baremos y ejecuta el cálculo antes de armar el dashboard."
        >
          <Link to={`/colmena/project/${projectId}/results`} className="colmena-badge inline-flex bg-amber/10 text-yellowDark">
            Ir a Resultados
          </Link>
        </EmptyState>
      ) : dimensions.length === 0 ? (
        <EmptyState title="Sin dimensiones" description="Este instrumento no tiene constructos de tipo dimensión configurados." />
      ) : (
        <>
          {roots.length ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {roots.map((root) => (
                <MetricCard
                  key={root.construct_id}
                  icon={LayoutDashboard}
                  label={root.construct_name}
                  value={root.suppressed ? 'Suprimido' : `${Math.round(root.mean_score ?? 0)} / 100`}
                />
              ))}
            </div>
          ) : null}

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {dimensions.map((dimension) => (
              <DimensionChartCard
                key={dimension.construct_id}
                studyId={studyId}
                versionId={overview?.instrument_version_id}
                dimension={dimension}
                subdimensions={childrenByParent.get(dimension.construct_id) || []}
                exogenousFields={exogenousFields}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
