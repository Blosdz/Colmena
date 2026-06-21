import type { ChartThemeName } from "../types/chartEditor";

const chartTypeLabels: Record<string, string> = {
  bar: "Barras",
  horizontal_bar: "Barras horizontales",
  grouped_bar: "Barras agrupadas",
  stacked_bar: "Barras apiladas",
  pie: "Circular",
  donut: "Donut",
  histogram: "Histograma",
  boxplot: "Caja y bigotes",
  scatter: "Dispersion",
  heatmap: "Mapa de calor",
  line: "Linea",
  mosaic_future: "Mosaico (futuro)",
};

const presetLabels: Record<ChartThemeName, string> = {
  academic_light: "Academico claro",
  colmena_premium: "Colmena premium",
  presentation_clean: "Presentacion limpia",
  monochrome_apa: "Monocromo APA",
};

export function getChartTypeLabel(chartType: string) {
  return chartTypeLabels[chartType] ?? chartType;
}

export function getPresetLabel(theme: ChartThemeName) {
  return presetLabels[theme];
}

export function formatChartValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(3).replace(/\.?0+$/, "");
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}
