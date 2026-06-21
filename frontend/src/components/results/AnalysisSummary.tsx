import type { OrchestratedAnalysis } from "../../types/analysis";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";

export function AnalysisSummary({ analysis }: { analysis?: OrchestratedAnalysis | null }) {
  if (!analysis) {
    return (
      <EmptyState
        title="Aun no hay analisis ejecutados"
        description="Usa el panel de ejecucion para lanzar un resumen descriptivo, una correlacion guiada o un scan general del formulario."
      />
    );
  }

  return (
    <div className="space-y-4">
      <Card className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone={analysis.status === "completed" ? "success" : "warning"}>{analysis.status}</Badge>
          <Badge tone="info">{analysis.analysis_goal}</Badge>
        </div>
        <div className="space-y-3">
          <h3 className="text-xl font-semibold text-dark">{analysis.title}</h3>
          <p className="text-sm leading-7 text-dark">{analysis.executive_summary}</p>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card className="space-y-3">
          <h4 className="text-base font-semibold text-dark">Resultado principal</h4>
          <p className="text-sm leading-7 text-dark">{analysis.main_result}</p>
          <p className="text-sm text-muted">{analysis.statistical_result}</p>
        </Card>
        <Card className="space-y-3">
          <h4 className="text-base font-semibold text-dark">Interpretacion academica</h4>
          <p className="text-sm leading-7 text-dark">{analysis.academic_interpretation}</p>
        </Card>
      </div>

      <Card className="space-y-3 bg-surfaceSoft">
        <h4 className="text-base font-semibold text-dark">Explicacion en lenguaje claro</h4>
        <p className="text-sm leading-7 text-dark">{analysis.plain_language_explanation}</p>
      </Card>

      {analysis.warnings.length > 0 ? (
        <Card className="space-y-2">
          <h4 className="text-base font-semibold text-dark">Warnings</h4>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            {analysis.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      {analysis.recommended_next_steps.length > 0 ? (
        <Card className="space-y-2">
          <h4 className="text-base font-semibold text-dark">Siguientes pasos sugeridos</h4>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            {analysis.recommended_next_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        {analysis.result_blocks.map((block, index) => (
          <Card className="space-y-2" key={`${block.block_type}-${index}`}>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber">{block.block_type}</p>
            <h4 className="text-base font-semibold text-dark">{block.title}</h4>
            <p className="text-sm leading-6 text-muted">{block.summary}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
