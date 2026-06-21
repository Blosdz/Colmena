import type { ScoringConfig } from "../../types/scoring";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";
import { ScoreBandEditor } from "./ScoreBandEditor";

function formatAggregation(value: string) {
  switch (value) {
    case "sum":
      return "Suma";
    case "mean":
      return "Promedio";
    case "weighted_mean":
      return "Promedio ponderado";
    default:
      return value;
  }
}

function formatMissingPolicy(value: string) {
  switch (value) {
    case "strict_complete":
      return "Completo obligatorio";
    case "allow_partial":
      return "Parcial permitido";
    case "prorate_if_threshold_met":
      return "Prorratear con umbral";
    default:
      return value;
  }
}

export function ScoringConfigPanel({
  configs,
  warnings,
}: {
  configs: ScoringConfig[];
  warnings?: string[];
}) {
  if (configs.length === 0) {
    return (
      <EmptyState
        title="Aun no hay configuraciones de scoring"
        description="Configura el instrumento desde el wizard o crea reglas de scoring antes de procesar respuestas."
      />
    );
  }

  return (
    <div className="space-y-4">
      {warnings && warnings.length > 0 ? (
        <Card className="space-y-2 bg-surfaceSoft">
          <h3 className="text-base font-semibold text-dark">Advertencias de configuracion</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      {configs.map((config) => (
        <Card className="space-y-4" key={config.id}>
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-lg font-semibold text-dark">{config.name}</h3>
            <Badge tone="info">{config.scoring_level}</Badge>
            <Badge tone="neutral">{formatAggregation(config.aggregation_method)}</Badge>
            <Badge tone="neutral">{formatMissingPolicy(config.missing_policy)}</Badge>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-border bg-[#fffdf8] px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Minimo de items</p>
              <p className="mt-2 text-sm font-semibold text-dark">{config.min_answered_items ?? "Sin minimo"}</p>
            </div>
            <div className="rounded-2xl border border-border bg-[#fffdf8] px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Completitud</p>
              <p className="mt-2 text-sm font-semibold text-dark">
                {config.min_completion_percent !== null && config.min_completion_percent !== undefined
                  ? `${config.min_completion_percent}%`
                  : "Sin umbral"}
              </p>
            </div>
            <div className="rounded-2xl border border-border bg-[#fffdf8] px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Items invertidos</p>
              <p className="mt-2 text-sm font-semibold text-dark">
                {config.reverse_scoring_enabled ? "Habilitados" : "Desactivados"}
              </p>
            </div>
            <div className="rounded-2xl border border-border bg-[#fffdf8] px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Codigo</p>
              <p className="mt-2 text-sm font-semibold text-dark">{config.code || "Sin codigo"}</p>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-semibold uppercase tracking-[0.12em] text-muted">Baremos configurados</h4>
            <ScoreBandEditor bands={config.bands} />
          </div>
        </Card>
      ))}
    </div>
  );
}
