import { useQuery } from "@tanstack/react-query";

import { getDescriptiveOverview, getDescriptives } from "../../api/descriptives";
import { getScoringResults } from "../../api/scoring";
import { formatNumber, formatPercent } from "../../utils/formatters";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { Card } from "../ui/Card";
import { MetricCard } from "./MetricCard";

export function DescriptivePanel({ formId }: { formId: string }) {
  const overviewQuery = useQuery({
    queryKey: ["descriptive-overview", formId],
    queryFn: () => getDescriptiveOverview(formId),
  });
  const descriptivesQuery = useQuery({
    queryKey: ["descriptives", formId],
    queryFn: () => getDescriptives(formId),
  });
  const scoringQuery = useQuery({
    queryKey: ["scoring-results", formId],
    queryFn: () => getScoringResults(formId),
  });

  if (overviewQuery.isLoading || descriptivesQuery.isLoading || scoringQuery.isLoading) {
    return <LoadingState label="Calculando descriptivos..." />;
  }

  if (overviewQuery.isError) {
    return <ErrorState message={(overviewQuery.error as Error).message} />;
  }

  if (descriptivesQuery.isError) {
    return <ErrorState message={(descriptivesQuery.error as Error).message} />;
  }
  if (scoringQuery.isError) {
    return <ErrorState message={(scoringQuery.error as Error).message} />;
  }

  const overview = overviewQuery.data;
  const report = descriptivesQuery.data;
  const scoring = scoringQuery.data;

  if (!overview || !report || overview.total_responses === 0) {
    return (
      <EmptyState
        title="No hay estadisticos descriptivos disponibles"
        description="Cuando el formulario tenga respuestas, aqui apareceran el resumen de la muestra y las variables principales."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Respuestas totales" value={overview.total_responses} />
        <MetricCard label="Incluidas" value={overview.included_responses} />
        <MetricCard label="Preguntas puntuadas" value={overview.scored_questions} />
        <MetricCard label="Preguntas numericas" value={overview.numeric_questions} />
      </div>

      {scoring && scoring.scored_responses > 0 ? (
        <Card className="space-y-3 bg-surfaceSoft">
          <h3 className="text-base font-semibold text-dark">Resumen de scoring</h3>
          <div className="grid gap-3 md:grid-cols-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Scoreadas</p>
              <p className="mt-2 text-lg font-semibold text-dark">{scoring.scored_responses}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Validas</p>
              <p className="mt-2 text-lg font-semibold text-dark">{scoring.valid_responses}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Advertencia</p>
              <p className="mt-2 text-lg font-semibold text-dark">{scoring.warning_responses}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Invalidas</p>
              <p className="mt-2 text-lg font-semibold text-dark">{scoring.invalid_responses}</p>
            </div>
          </div>
          {scoring.band_distribution.length > 0 ? (
            <div className="space-y-2">
              {scoring.band_distribution.slice(0, 4).map((band) => (
                <div className="flex items-center justify-between rounded-2xl bg-white px-4 py-3 text-sm" key={`${band.scoring_config_id}-${band.level}`}>
                  <span className="text-dark">
                    {band.scoring_config_name} - {band.level}
                  </span>
                  <span className="text-muted">
                    {band.n} · {formatPercent(band.percent)}
                  </span>
                </div>
              ))}
            </div>
          ) : null}
        </Card>
      ) : null}

      {overview.warnings.length > 0 ? (
        <Card className="space-y-2 bg-surfaceSoft">
          <h3 className="text-base font-semibold text-dark">Advertencias de calidad</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            {overview.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        {report.questions.slice(0, 6).map((question) => (
          <Card key={question.question_id} className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-dark">{question.label}</h3>
              <p className="text-sm text-muted">
                {question.question_type} · {question.measurement_level} · n valido {question.valid_n}
              </p>
            </div>

            {question.numeric ? (
              <dl className="grid gap-3 text-sm text-muted sm:grid-cols-2">
                <div>
                  <dt className="font-medium text-dark">M</dt>
                  <dd>{formatNumber(question.numeric.mean)}</dd>
                </div>
                <div>
                  <dt className="font-medium text-dark">DE</dt>
                  <dd>{formatNumber(question.numeric.standard_deviation)}</dd>
                </div>
                <div>
                  <dt className="font-medium text-dark">Mdn</dt>
                  <dd>{formatNumber(question.numeric.median)}</dd>
                </div>
                <div>
                  <dt className="font-medium text-dark">Rango</dt>
                  <dd>{formatNumber(question.numeric.range)}</dd>
                </div>
              </dl>
            ) : (
              <div className="space-y-2">
                {question.frequencies.slice(0, 4).map((row) => (
                  <div className="flex items-center justify-between rounded-2xl bg-[#fcfbf7] px-4 py-3 text-sm" key={row.value || row.label}>
                    <span className="text-dark">{row.label || row.value || "Sin etiqueta"}</span>
                    <span className="text-muted">
                      {row.frequency} · {formatPercent(row.valid_percent ?? row.percent)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
