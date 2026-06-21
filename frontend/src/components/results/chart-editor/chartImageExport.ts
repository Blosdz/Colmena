import type { ChartSpec } from "../../../types/chart";
import type { EditableChartState } from "../../../types/chartEditor";

type PlotlyExportOptions = {
  width?: number;
  height?: number;
  scale?: number;
  format?: "png" | "svg";
};

type PlotlyModule = {
  toImage: (
    graphDiv: unknown,
    options: { format: "png" | "svg"; width: number; height: number; scale?: number },
  ) => Promise<string>;
};

async function getPlotlyModule(): Promise<PlotlyModule> {
  const module = await import("plotly.js/dist/plotly.min.js");
  return module.default ? (module.default as PlotlyModule) : (module as unknown as PlotlyModule);
}

export async function exportPlotlyToPng(graphDiv: unknown, options: PlotlyExportOptions = {}) {
  const Plotly = await getPlotlyModule();
  return Plotly.toImage(graphDiv, {
    format: "png",
    width: options.width ?? 1400,
    height: options.height ?? 900,
    scale: options.scale ?? 2,
  });
}

export async function exportPlotlyToSvg(graphDiv: unknown, options: PlotlyExportOptions = {}) {
  const Plotly = await getPlotlyModule();
  return Plotly.toImage(graphDiv, {
    format: "svg",
    width: options.width ?? 1400,
    height: options.height ?? 900,
    scale: options.scale ?? 1,
  });
}

export function dataUrlToBlob(dataUrl: string): Blob {
  const [header, body] = dataUrl.split(",", 2);
  const mimeMatch = header.match(/data:(.*?);base64/);
  const mimeType = mimeMatch?.[1] ?? "application/octet-stream";
  const binary = atob(body);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: mimeType });
}

export function downloadDataUrl(dataUrl: string, fileName: string) {
  const anchor = document.createElement("a");
  anchor.href = dataUrl;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

function sanitizeNamePart(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

export function buildChartImageFileName(
  chart: ChartSpec,
  state: EditableChartState,
  format: "png" | "svg",
) {
  const title = sanitizeNamePart(state.title || chart.title || chart.chart_id);
  return `${title || chart.chart_id}.${format}`;
}
