import type { ChartSpec } from "../../../types/chart";
import { getChartTypeLabel } from "../../../utils/chartFormatters";
import { Select, SelectOption } from "../../ui/Select";
import { getSafeAvailableChartTypes } from "./chartEditorUtils";

export function ChartTypeSelector({
  chart,
  value,
  onChange,
}: {
  chart: ChartSpec;
  value: string;
  onChange: (value: string) => void;
}) {
  const availableTypes = getSafeAvailableChartTypes(chart);

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-dark">Tipo de grafico</label>
      <Select value={value} onChange={(event) => onChange(event.target.value)}>
        {availableTypes.map((chartType) => (
          <SelectOption key={chartType} value={chartType}>
            {getChartTypeLabel(chartType)}
          </SelectOption>
        ))}
      </Select>
    </div>
  );
}
