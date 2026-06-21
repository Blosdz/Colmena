import { AlertCircle } from "lucide-react";
import { lazy, Suspense } from "react";
import { useState } from "react";

import type { ChartSpec } from "../../../types/chart";
import { Card } from "../../ui/Card";
import { LoadingState } from "../../ui/LoadingState";
import { ChartAdvancedPanel } from "./ChartAdvancedPanel";
import { ChartControls } from "./ChartControls";
import { ChartDataTable } from "./ChartDataTable";
import { buildEditorWarnings, deriveChartDataTable } from "./chartEditorUtils";
import { ChartExportControls } from "./ChartExportControls";
import { useChartEditor } from "./useChartEditor";
import { ChartWarningPanel } from "./ChartWarningPanel";

const LazyPlotCanvas = lazy(() => import("./PlotlyChartCanvas"));

export function ChartEditor({
  chart,
  onReset,
  onImageSaved,
  storageKey,
}: {
  chart: ChartSpec;
  onReset?: () => void;
  onImageSaved?: () => void;
  storageKey?: string;
}) {
  const [graphDiv, setGraphDiv] = useState<unknown>(null);
  const { state, derivedSpec, updateField, applyPreset, resetToRecommended } = useChartEditor(chart, storageKey);
  const warnings = buildEditorWarnings(chart, state);
  const dataTable = deriveChartDataTable(chart);

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_390px]">
      <div className="space-y-5">
        <Card className="space-y-5 p-5">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber">Vista del grafico</p>
            <h3 className="text-xl font-semibold text-dark">{state.title}</h3>
            {state.subtitle ? <p className="text-sm text-muted">{state.subtitle}</p> : null}
          </div>
          <div className="min-h-[440px] overflow-hidden rounded-[24px] border border-border bg-white p-2">
            <Suspense fallback={<LoadingState label="Cargando motor visual de Plotly..." />}>
              {chart.ready_for_frontend ? (
                <LazyPlotCanvas
                  config={derivedSpec.config}
                  data={derivedSpec.data}
                  layout={derivedSpec.layout}
                  onReady={setGraphDiv}
                />
              ) : (
                <div className="flex min-h-[420px] items-center justify-center">
                  <div className="max-w-md space-y-3 text-center">
                    <AlertCircle className="mx-auto h-8 w-8 text-warning" />
                    <p className="text-base font-semibold text-dark">No se pudo renderizar este grafico</p>
                    <p className="text-sm leading-6 text-muted">
                      La especificacion tecnica sigue disponible y puede revisarse en el panel avanzado.
                    </p>
                  </div>
                </div>
              )}
            </Suspense>
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            <Card className="space-y-2 bg-surfaceSoft p-4">
              <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Explicacion simple</h4>
              <p className="text-sm leading-7 text-dark">{chart.plain_language_explanation}</p>
            </Card>
            <Card className="space-y-2 bg-surfaceSoft p-4">
              <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Nota academica</h4>
              <p className="text-sm leading-7 text-dark">{chart.academic_note}</p>
            </Card>
          </div>
        </Card>

        <ChartWarningPanel warnings={warnings} />

        <ChartExportControls
          chart={chart}
          formId={chart.form_id}
          graphDiv={graphDiv}
          onImageSaved={onImageSaved}
          state={state}
        />

        {state.showDataTable ? <ChartDataTable model={dataTable} /> : null}

        {state.showAdvancedJson ? (
          <ChartAdvancedPanel
            chartJson={{
              chart_id: chart.chart_id,
              chart_type: state.chartType,
              derivedSpec,
              source_type: chart.source_type,
            }}
            state={state}
          />
        ) : null}
      </div>

      <div className="space-y-5">
        <ChartControls
          applyPreset={applyPreset}
          chart={chart}
          onReset={() => {
            resetToRecommended();
            onReset?.();
          }}
          state={state}
          updateField={updateField}
        />
      </div>
    </div>
  );
}
