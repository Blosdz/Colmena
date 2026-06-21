import type { ControlScale } from "../../types/scoring";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";

function toneForFlag(flagLevel: string) {
  if (flagLevel === "invalid") {
    return "danger" as const;
  }
  return "warning" as const;
}

export function ControlScaleEditor({ controlScales }: { controlScales: ControlScale[] }) {
  if (controlScales.length === 0) {
    return (
      <EmptyState
        title="Sin escalas de control"
        description="Puedes agregar una escala de control desde el wizard para advertir o invalidar respuestas sospechosas."
      />
    );
  }

  return (
    <div className="space-y-3">
      {controlScales.map((scale) => (
        <div className="space-y-3 rounded-[24px] border border-border bg-white p-4" key={scale.id}>
          <div className="flex flex-wrap items-center gap-3">
            <h4 className="text-base font-semibold text-dark">{scale.name}</h4>
            <Badge tone={toneForFlag(scale.flag_level)}>{scale.flag_level}</Badge>
            <Badge tone="neutral">{scale.control_type}</Badge>
            <Badge tone="info">{scale.rule_type}</Badge>
          </div>
          <p className="text-sm text-muted">
            Umbral: {scale.threshold ?? "sin umbral"} {scale.comparison_operator ? `(${scale.comparison_operator})` : ""}
          </p>
          <p className="text-sm text-dark">{scale.message || "Sin mensaje metodologico adicional."}</p>
          <div className="text-sm text-muted">
            {scale.items.length} items asociados
            {scale.items.length > 0 ? (
              <span>: {scale.items.map((item) => item.question_id.slice(0, 8)).join(", ")}</span>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
