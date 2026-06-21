import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getScoringResults, listControlScales, listScoringConfigs, runScoring } from "../../api/scoring";
import { formatNumber, formatPercent } from "../../utils/formatters";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { MetricCard } from "../results/MetricCard";
import { ControlScaleEditor } from "./ControlScaleEditor";
import { ScoringConfigPanel } from "./ScoringConfigPanel";

export function ScoringResultsPanel({ formId }: { formId: string }) {
  const queryClient = useQueryClient();
  const configsQuery = useQuery({
    queryKey: ["scoring-configs", formId],
    queryFn: () => listScoringConfigs(formId),
  });
  const controlScalesQuery = useQuery({
    queryKey: ["control-scales", formId],
    queryFn: () => listControlScales(formId),
  });
  const resultsQuery = useQuery({
    queryKey: ["scoring-results", formId],
    queryFn: () => getScoringResults(formId),
  });

  const runMutation = useMutation({
    mutationFn: () =>
      runScoring(formId, {
        include_discarded: false,
        recalculate: true,
        store_result: true,
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["scoring-results", formId] }),
        queryClient.invalidateQueries({ queryKey: ["descriptive-overview", formId] }),
        queryClient.invalidateQueries({ queryKey: ["descriptives", formId] }),
      ]);
    },
  });

  if (configsQuery.isLoading || controlScalesQuery.isLoading || resultsQuery.isLoading) {
    return <LoadingState label="Cargando scoring avanzado..." />;
  }

  if (configsQuery.isError) {
    return <ErrorState message={(configsQuery.error as Error).message} />;
  }

  if (controlScalesQuery.isError) {
    return <ErrorState message={(controlScalesQuery.error as Error).message} />;
  }

  if (resultsQuery.isError) {
    return <ErrorState message={(resultsQuery.error as Error).message} />;
  }

  const configs = configsQuery.data?.items ?? [];
  const configWarnings = configsQuery.data?.warnings ?? [];
  const controlScales = controlScalesQuery.data ?? [];
  const results = resultsQuery.data;

  if (configs.length === 0 && controlScales.length === 0) {
    return (
      <EmptyState
        title="Aun no hay reglas de scoring"
        description="Configura baremos, items invertidos y escalas de control desde el wizard para habilitar esta capa."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-dark">Scoring avanzado</h3>
          <p className="text-sm leading-6 text-muted">
            Ejecuta el scoring del formulario, revisa la distribucion por baremo y detecta respuestas con advertencias de control.
          </p>
        </div>
        <Button loading={runMutation.isPending} onClick={() => runMutation.mutate()}>
          Ejecutar scoring
        </Button>
      </div>

      {runMutation.isError ? <ErrorState message={(runMutation.error as Error).message} /> : null}
      {runMutation.data?.warnings.length ? (
        <Card className="space-y-2 bg-surfaceSoft">
          <h4 className="text-base font-semibold text-dark">Advertencias del ultimo calculo</h4>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            {runMutation.data.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      {results ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <MetricCard label="Respuestas totales" value={results.total_responses} />
            <MetricCard label="Scoreadas" value={results.scored_responses} />
            <MetricCard label="Validas" value={results.valid_responses} />
            <MetricCard label="Con advertencia" value={results.warning_responses} />
            <MetricCard label="Invalidas" value={results.invalid_responses} />
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <Card className="space-y-4">
              <h4 className="text-base font-semibold text-dark">Distribucion por baremo</h4>
              {results.band_distribution.length > 0 ? (
                <div className="space-y-2">
                  {results.band_distribution.map((band) => (
                    <div className="grid gap-2 rounded-2xl border border-border bg-[#fffdf8] px-4 py-3 md:grid-cols-[minmax(180px,1fr)_100px_90px_minmax(180px,1fr)]" key={`${band.scoring_config_id}-${band.level}`}>
                      <div>
                        <p className="text-sm font-semibold text-dark">{band.level}</p>
                        <p className="text-xs uppercase tracking-[0.12em] text-muted">{band.scoring_config_name}</p>
                      </div>
                      <p className="text-sm text-dark">{band.n} casos</p>
                      <p className="text-sm text-dark">{formatPercent(band.percent)}</p>
                      <p className="text-sm text-muted">{band.interpretation || "Sin interpretacion breve."}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="Aun no hay niveles calculados"
                  description="Ejecuta el scoring para ver la distribucion de baremos del instrumento."
                />
              )}
            </Card>

            <Card className="space-y-4">
              <h4 className="text-base font-semibold text-dark">Flags de control</h4>
              {results.control_flags.length > 0 ? (
                <div className="space-y-2">
                  {results.control_flags.map((flag) => (
                    <div className="grid gap-2 rounded-2xl border border-border bg-[#fffdf8] px-4 py-3 md:grid-cols-[minmax(180px,1fr)_120px_90px]" key={`${flag.control_scale_id}-${flag.flag_status}`}>
                      <p className="text-sm font-semibold text-dark">{flag.name}</p>
                      <p className="text-sm text-dark">{flag.flag_status}</p>
                      <p className="text-sm text-muted">
                        {flag.n} · {formatPercent(flag.percent)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="Sin flags de control"
                  description="Cuando ejecutes scoring con escalas de control activas, aqui veras advertencias e invalidez."
                />
              )}
            </Card>
          </div>

          {results.warnings.length > 0 ? (
            <Card className="space-y-2">
              <h4 className="text-base font-semibold text-dark">Advertencias metodologicas</h4>
              <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
                {results.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </Card>
          ) : null}
        </>
      ) : null}

      <ScoringConfigPanel configs={configs} warnings={configWarnings} />

      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h4 className="text-base font-semibold text-dark">Escalas de control configuradas</h4>
          <p className="text-sm text-muted">{formatNumber(controlScales.length, 0)} configuradas</p>
        </div>
        <ControlScaleEditor controlScales={controlScales} />
      </Card>
    </div>
  );
}
