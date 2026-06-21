import { uploadChartImage } from "../../../api/chartImages";
import type { ChartSpec } from "../../../types/chart";
import type { EditableChartState } from "../../../types/chartEditor";

function normalizeSvgDataUrl(dataUrl: string) {
  if (!dataUrl.startsWith("data:image/svg+xml")) {
    return dataUrl;
  }
  if (dataUrl.includes(";base64,")) {
    return dataUrl;
  }
  const [, rawPayload = ""] = dataUrl.split(",", 2);
  const decoded = decodeURIComponent(rawPayload);
  return `data:image/svg+xml;base64,${btoa(decoded)}`;
}

export async function saveChartImageForWord({
  formId,
  chart,
  state,
  dataUrl,
  format,
}: {
  formId: string;
  chart: ChartSpec;
  state: EditableChartState;
  dataUrl: string;
  format: "png" | "svg";
}) {
  const safeDataUrl = format === "svg" ? normalizeSvgDataUrl(dataUrl) : dataUrl;
  return uploadChartImage(formId, {
    chart_id: chart.chart_id,
    chart_type: state.chartType,
    title: state.title,
    format,
    data_url: safeDataUrl,
    file_name: `${chart.chart_id}.${format}`,
    source_type: "chart_editor",
    analysis_run_id: null,
    metadata_json: {
      theme: state.theme,
      editable_state: {
        chartType: state.chartType,
        title: state.title,
        subtitle: state.subtitle,
        xAxisTitle: state.xAxisTitle,
        yAxisTitle: state.yAxisTitle,
        orientation: state.orientation,
        showPercentages: state.showPercentages,
        showFrequencies: state.showFrequencies,
        showValues: state.showValues,
        showLegend: state.showLegend,
        showGrid: state.showGrid,
        labelRotation: state.labelRotation,
        fontScale: state.fontScale,
      },
      chart_spec_summary: {
        chart_id: chart.chart_id,
        chart_type: chart.chart_type,
        source_type: chart.source_type,
      },
      created_from_frontend: true,
    },
  });
}
