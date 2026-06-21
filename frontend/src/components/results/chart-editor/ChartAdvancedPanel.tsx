import type { EditableChartState } from "../../../types/chartEditor";
import { Button } from "../../ui/Button";

export function ChartAdvancedPanel({
  chartJson,
  state,
}: {
  chartJson: Record<string, unknown>;
  state: EditableChartState;
}) {
  const handleCopy = async () => {
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      return;
    }
    await navigator.clipboard.writeText(JSON.stringify({ chart: chartJson, state }, null, 2));
  };

  return (
    <details className="rounded-2xl border border-border bg-[#fcfbf7] p-4">
      <summary className="cursor-pointer text-sm font-medium text-dark">Panel avanzado</summary>
      <div className="mt-4 space-y-4">
        <div className="flex justify-end">
          <Button onClick={() => void handleCopy()} size="sm" variant="secondary">
            Copiar JSON
          </Button>
        </div>
        <div className="space-y-2">
          <p className="text-sm font-semibold text-dark">ChartSpec tecnico</p>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-2xl bg-white p-4 text-xs text-muted">
            {JSON.stringify(chartJson, null, 2)}
          </pre>
        </div>
        <div className="space-y-2">
          <p className="text-sm font-semibold text-dark">Estado editable</p>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-2xl bg-white p-4 text-xs text-muted">
            {JSON.stringify(state, null, 2)}
          </pre>
        </div>
      </div>
    </details>
  );
}
