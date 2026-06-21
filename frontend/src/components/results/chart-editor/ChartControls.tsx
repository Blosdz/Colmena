import type { ChartSpec } from "../../../types/chart";
import type { ChartThemeName, EditableChartState } from "../../../types/chartEditor";
import { Button } from "../../ui/Button";
import { Card } from "../../ui/Card";
import { ChartDisplayControls } from "./ChartDisplayControls";
import { ChartStyleControls } from "./ChartStyleControls";
import { ChartTextControls } from "./ChartTextControls";
import { ChartTypeSelector } from "./ChartTypeSelector";

export function ChartControls({
  chart,
  state,
  updateField,
  applyPreset,
  onReset,
}: {
  chart: ChartSpec;
  state: EditableChartState;
  updateField: <K extends keyof EditableChartState>(field: K, value: EditableChartState[K]) => void;
  applyPreset: (preset: ChartThemeName) => void;
  onReset: () => void;
}) {
  return (
    <Card className="space-y-5 p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-dark">Editor visual</h3>
          <p className="text-sm text-muted">Ajusta la presentacion sin alterar el resultado estadistico original.</p>
        </div>
        <Button onClick={onReset} size="sm" variant="secondary">
          Restaurar recomendacion
        </Button>
      </div>

      <ChartTypeSelector chart={chart} onChange={(value) => updateField("chartType", value)} value={state.chartType} />

      <ChartTextControls
        onChange={(field, value) => updateField(field, value)}
        subtitle={state.subtitle}
        title={state.title}
        xAxisTitle={state.xAxisTitle}
        yAxisTitle={state.yAxisTitle}
      />

      <ChartStyleControls
        allowOrientation={chart.editable_options.can_change_orientation}
        fontScale={state.fontScale}
        labelRotation={state.labelRotation}
        onFontScaleChange={(value) => updateField("fontScale", value)}
        onLabelRotationChange={(value) => updateField("labelRotation", value)}
        onOrientationChange={(value) => updateField("orientation", value)}
        onShowGridChange={(value) => updateField("showGrid", value)}
        onThemeChange={applyPreset}
        orientation={state.orientation}
        showGrid={state.showGrid}
        theme={state.theme}
      />

      <ChartDisplayControls
        onToggle={(field, value) => updateField(field, value)}
        showAdvancedJson={state.showAdvancedJson}
        showDataTable={state.showDataTable}
        showFrequencies={state.showFrequencies}
        showLegend={state.showLegend}
        showPercentages={state.showPercentages}
        showValues={state.showValues}
      />
    </Card>
  );
}
