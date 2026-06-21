import type { ChartSpec } from "../../../types/chart";
import type {
  ChartDataTableModel,
  ChartEditorResultSpec,
  ChartThemeName,
  EditableChartState,
} from "../../../types/chartEditor";

type ThemeSpec = {
  palette: string[];
  background: string;
  textColor: string;
  gridColor: string;
  fontFamily: string;
  legendPosition: "h" | "v";
  margin: { l: number; r: number; t: number; b: number };
};

export const chartThemes: Record<ChartThemeName, ThemeSpec> = {
  academic_light: {
    palette: ["#5B6C8F", "#9AA6B2", "#D99A21", "#7BA7B2", "#B7791F"],
    background: "#FFFFFF",
    textColor: "#1F1F1F",
    gridColor: "#E6E8EC",
    fontFamily: "Times New Roman, Georgia, serif",
    legendPosition: "h",
    margin: { l: 56, r: 24, t: 74, b: 56 },
  },
  colmena_premium: {
    palette: ["#D99A21", "#F2B84B", "#7E5B12", "#3F3F46", "#A66A0A"],
    background: "#FFFDF8",
    textColor: "#1F1F1F",
    gridColor: "#EFE6D2",
    fontFamily: "Inter, Segoe UI, sans-serif",
    legendPosition: "h",
    margin: { l: 56, r: 24, t: 74, b: 56 },
  },
  presentation_clean: {
    palette: ["#1F1F1F", "#D99A21", "#2563EB", "#2E7D32", "#B91C1C"],
    background: "#FFFFFF",
    textColor: "#111111",
    gridColor: "#D8DCE3",
    fontFamily: "Inter, Segoe UI, sans-serif",
    legendPosition: "v",
    margin: { l: 56, r: 24, t: 80, b: 60 },
  },
  monochrome_apa: {
    palette: ["#2F2F2F", "#606060", "#8A8A8A", "#B5B5B5", "#D9D9D9"],
    background: "#FFFFFF",
    textColor: "#222222",
    gridColor: "#E0E0E0",
    fontFamily: "Times New Roman, Georgia, serif",
    legendPosition: "h",
    margin: { l: 56, r: 24, t: 74, b: 56 },
  },
};

function cloneValue<T>(value: T): T {
  if (typeof structuredClone === "function") {
    return structuredClone(value);
  }

  return JSON.parse(JSON.stringify(value)) as T;
}

function coerceStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item ?? ""));
}

function coerceNumberArray(value: unknown): number[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => (typeof item === "number" ? item : Number(item)))
    .filter((item) => Number.isFinite(item));
}

function coerceMatrix(value: unknown): number[][] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.map((row) =>
    Array.isArray(row)
      ? row.map((item) => (item === null ? Number.NaN : typeof item === "number" ? item : Number(item)))
      : [],
  );
}

function getTheme(chart: ChartSpec, themeName: ChartThemeName) {
  return chartThemes[themeName] ?? (chart.theme as ThemeSpec) ?? chartThemes.colmena_premium;
}

function getAxisTitles(chart: ChartSpec) {
  const layout = chart.plotly_layout ?? {};
  const xAxisTitle =
    typeof (layout.xaxis as { title?: { text?: string } } | undefined)?.title?.text === "string"
      ? ((layout.xaxis as { title?: { text?: string } }).title?.text ?? "")
      : "";
  const yAxisTitle =
    typeof (layout.yaxis as { title?: { text?: string } } | undefined)?.title?.text === "string"
      ? ((layout.yaxis as { title?: { text?: string } }).title?.text ?? "")
      : "";

  return { xAxisTitle, yAxisTitle };
}

export function getSafeAvailableChartTypes(chart: ChartSpec) {
  const payload = (chart.data ?? {}) as Record<string, unknown>;

  if (Array.isArray(payload.z)) {
    return ["heatmap"];
  }

  if (Array.isArray(payload.series) && Array.isArray(payload.categories)) {
    return ["grouped_bar", "stacked_bar", "bar"];
  }

  if (Array.isArray(payload.labels) && Array.isArray(payload.values)) {
    return ["bar", "horizontal_bar", "pie", "donut"];
  }

  if (Array.isArray(payload.values)) {
    return ["histogram", "boxplot", "bar"];
  }

  if (Array.isArray(payload.x) && Array.isArray(payload.y)) {
    if (chart.chart_type === "boxplot") {
      return ["boxplot", "grouped_bar", "bar"];
    }
    return ["scatter"];
  }

  return [chart.chart_type, ...chart.recommended_alternatives].filter(Boolean);
}

export function createInitialEditableChartState(chart: ChartSpec): EditableChartState {
  const themeName = (typeof chart.theme?.template_name === "string"
    ? chart.theme.template_name
    : "colmena_premium") as ChartThemeName;
  const { xAxisTitle, yAxisTitle } = getAxisTitles(chart);
  const available = getSafeAvailableChartTypes(chart);
  const orientation =
    chart.chart_type === "horizontal_bar" ||
    (chart.plotly_data[0] && (chart.plotly_data[0] as { orientation?: string }).orientation === "h")
      ? "horizontal"
      : "vertical";

  return {
    chartType: available.includes(chart.chart_type) ? chart.chart_type : available[0] ?? chart.chart_type,
    title: chart.title,
    subtitle: chart.subtitle ?? "",
    xAxisTitle,
    yAxisTitle,
    theme: themeName,
    orientation,
    showPercentages: false,
    showFrequencies: true,
    showValues: false,
    showLegend: Boolean(chart.plotly_layout?.showlegend ?? true),
    showGrid: true,
    showDataTable: false,
    showAdvancedJson: false,
    selectedPalette: themeName,
    labelRotation: 0,
    fontScale: 1,
    rawSpec: {
      chart_id: chart.chart_id,
      chart_type: chart.chart_type,
      source_type: chart.source_type,
    },
  };
}

function getFrequencyPayload(chart: ChartSpec) {
  const payload = (chart.data ?? {}) as Record<string, unknown>;
  const labels = coerceStringArray(payload.labels);
  const values = coerceNumberArray(payload.values);
  const text = Array.isArray(payload.text) ? payload.text.map((item) => String(item ?? "")) : [];

  if (labels.length && values.length) {
    return { labels, values, text };
  }

  const categories = coerceStringArray(payload.categories);
  const series = Array.isArray(payload.series) ? (payload.series as Array<Record<string, unknown>>) : [];
  if (categories.length && series.length) {
    const aggregated = categories.map((_, index) =>
      series.reduce((total, serie) => total + Number((serie.values as number[] | undefined)?.[index] ?? 0), 0),
    );
    return { labels: categories, values: aggregated, text: aggregated.map((value) => String(value)) };
  }

  return { labels: [], values: [], text: [] };
}

function getGroupedPayload(chart: ChartSpec) {
  const payload = (chart.data ?? {}) as Record<string, unknown>;
  const categories = coerceStringArray(payload.categories);
  const series = Array.isArray(payload.series) ? cloneValue(payload.series) : [];

  if (categories.length && Array.isArray(series) && series.length) {
    return { categories, series: series as Array<Record<string, unknown>> };
  }

  const freq = getFrequencyPayload(chart);
  return {
    categories: freq.labels,
    series: [
      {
        name: chart.title,
        values: freq.values,
        text: freq.text,
      },
    ],
  };
}

function getValuePayload(chart: ChartSpec) {
  const payload = (chart.data ?? {}) as Record<string, unknown>;
  const values = coerceNumberArray(payload.values);

  if (values.length) {
    return values;
  }

  const yValues = Array.isArray(payload.y) ? payload.y : [];
  const xValues = Array.isArray(payload.x) ? payload.x : [];
  return coerceNumberArray(yValues.length ? yValues : xValues);
}

function getXYPayload(chart: ChartSpec) {
  const payload = (chart.data ?? {}) as Record<string, unknown>;
  return {
    x: Array.isArray(payload.x) ? cloneValue(payload.x) : [],
    y: Array.isArray(payload.y) ? cloneValue(payload.y) : [],
  };
}

function getHeatmapPayload(chart: ChartSpec) {
  const payload = (chart.data ?? {}) as Record<string, unknown>;
  return {
    x: coerceStringArray(payload.x),
    y: coerceStringArray(payload.y),
    z: coerceMatrix(payload.z),
  };
}

function buildValueLabels(
  labels: string[],
  values: number[],
  state: EditableChartState,
  decimals = 1,
) {
  const total = values.reduce((sum, value) => sum + value, 0);

  return values.map((value, index) => {
    const parts: string[] = [];
    if (state.showFrequencies) {
      parts.push(String(value));
    }
    if (state.showPercentages && total > 0) {
      parts.push(`${((value / total) * 100).toFixed(decimals)}%`);
    }
    if (!state.showValues && parts.length === 0) {
      return labels[index] ?? "";
    }
    return parts.join(" · ");
  });
}

function buildBarData(chart: ChartSpec, state: EditableChartState) {
  const payload = getFrequencyPayload(chart);
  const horizontal = state.orientation === "horizontal" || state.chartType === "horizontal_bar";
  const text = state.showValues || state.showFrequencies || state.showPercentages ? buildValueLabels(payload.labels, payload.values, state) : undefined;

  return [
    {
      type: "bar",
      orientation: horizontal ? "h" : "v",
      x: horizontal ? payload.values : payload.labels,
      y: horizontal ? payload.labels : payload.values,
      marker: { color: chartThemes[state.theme].palette[0] },
      text,
      textposition: "auto",
      hovertemplate: horizontal
        ? "%{y}: %{x}<extra></extra>"
        : "%{x}: %{y}<extra></extra>",
    },
  ];
}

function buildGroupedData(chart: ChartSpec, state: EditableChartState) {
  const payload = getGroupedPayload(chart);
  return payload.series.map((serie, index) => ({
    type: "bar",
    name: String(serie.name ?? `Serie ${index + 1}`),
    x: payload.categories,
    y: Array.isArray(serie.values) ? serie.values : [],
    text:
      state.showValues || state.showFrequencies || state.showPercentages
        ? (Array.isArray(serie.values) ? serie.values : []).map((value) => String(value))
        : undefined,
    textposition: "auto",
    marker: { color: chartThemes[state.theme].palette[index % chartThemes[state.theme].palette.length] },
  }));
}

function buildPieData(chart: ChartSpec, state: EditableChartState) {
  const payload = getFrequencyPayload(chart);
  return [
    {
      type: "pie",
      labels: payload.labels,
      values: payload.values,
      hole: state.chartType === "donut" ? 0.48 : 0,
      textinfo: state.showPercentages ? "label+percent" : state.showValues || state.showFrequencies ? "label+value" : "label",
      marker: { colors: chartThemes[state.theme].palette },
    },
  ];
}

function buildHistogramData(chart: ChartSpec, state: EditableChartState) {
  const values = getValuePayload(chart);
  return [
    {
      type: "histogram",
      x: values,
      marker: { color: chartThemes[state.theme].palette[0] },
      opacity: 0.88,
      text: state.showValues ? values.map((value) => String(value)) : undefined,
    },
  ];
}

function buildBoxplotData(chart: ChartSpec, state: EditableChartState) {
  const payload = getXYPayload(chart);
  const values = payload.y.length ? payload.y : getValuePayload(chart);
  const groups = payload.x.length ? payload.x : undefined;

  return [
    {
      type: "box",
      y: values,
      x: groups,
      boxpoints: state.showValues ? "outliers" : false,
      marker: { color: chartThemes[state.theme].palette[0] },
      line: { color: chartThemes[state.theme].palette[0] },
    },
  ];
}

function buildScatterData(chart: ChartSpec, state: EditableChartState) {
  const payload = getXYPayload(chart);
  return [
    {
      type: "scatter",
      mode: state.showValues ? "markers+text" : "markers",
      x: payload.x,
      y: payload.y,
      text: state.showValues ? payload.x.map((_, index) => String(index + 1)) : undefined,
      marker: {
        color: chartThemes[state.theme].palette[0],
        size: 11,
        opacity: 0.82,
      },
    },
  ];
}

function buildHeatmapData(chart: ChartSpec) {
  const payload = getHeatmapPayload(chart);
  return [
    {
      type: "heatmap",
      x: payload.x,
      y: payload.y,
      z: payload.z,
      colorscale: "YlOrBr",
    },
  ];
}

function buildMeanBarData(chart: ChartSpec, state: EditableChartState) {
  const payload = getXYPayload(chart);
  const groups = Array.isArray(payload.x) ? payload.x.map((item) => String(item)) : [];
  const values = Array.isArray(payload.y) ? payload.y.map((item) => Number(item)) : [];
  const grouped = new Map<string, number[]>();

  groups.forEach((group, index) => {
    const current = grouped.get(group) ?? [];
    current.push(values[index] ?? 0);
    grouped.set(group, current);
  });

  const labels = Array.from(grouped.keys());
  const means = labels.map((label) => {
    const items = grouped.get(label) ?? [];
    return items.length ? items.reduce((sum, item) => sum + item, 0) / items.length : 0;
  });

  return [
    {
      type: "bar",
      x: labels,
      y: means,
      marker: { color: chartThemes[state.theme].palette[0] },
      text: state.showValues ? means.map((value) => value.toFixed(2)) : undefined,
      textposition: "auto",
    },
  ];
}

function buildDataForType(chart: ChartSpec, state: EditableChartState) {
  switch (state.chartType) {
    case "bar":
    case "horizontal_bar":
      if (chart.chart_type === "boxplot" && Array.isArray((chart.data as Record<string, unknown>).x)) {
        return buildMeanBarData(chart, state);
      }
      return buildBarData(chart, state);
    case "grouped_bar":
    case "stacked_bar":
      if (chart.chart_type === "boxplot" && Array.isArray((chart.data as Record<string, unknown>).x)) {
        return buildMeanBarData(chart, state);
      }
      return buildGroupedData(chart, state);
    case "pie":
    case "donut":
      return buildPieData(chart, state);
    case "histogram":
      return buildHistogramData(chart, state);
    case "boxplot":
      return buildBoxplotData(chart, state);
    case "scatter":
      return buildScatterData(chart, state);
    case "heatmap":
      return buildHeatmapData(chart);
    default:
      return cloneValue(chart.plotly_data);
  }
}

function buildLayoutForState(chart: ChartSpec, state: EditableChartState) {
  const theme = getTheme(chart, state.theme);
  const layout = cloneValue(chart.plotly_layout ?? {});
  const horizontal = state.orientation === "horizontal" || state.chartType === "horizontal_bar";
  const barmode = state.chartType === "stacked_bar" ? "stack" : state.chartType === "grouped_bar" ? "group" : undefined;

  layout.title = {
    text: state.subtitle
      ? `${state.title}<br><span style="font-size:${Math.round(12 * state.fontScale)}px;color:${theme.textColor};opacity:0.7">${state.subtitle}</span>`
      : state.title,
    x: 0,
    xanchor: "left",
    font: { size: Math.round(22 * state.fontScale), color: theme.textColor, family: theme.fontFamily },
  };
  layout.paper_bgcolor = theme.background;
  layout.plot_bgcolor = theme.background;
  layout.font = { color: theme.textColor, family: theme.fontFamily, size: Math.round(13 * state.fontScale) };
  layout.margin = theme.margin;
  layout.showlegend = state.showLegend;
  layout.legend = { orientation: theme.legendPosition, x: 0, y: theme.legendPosition === "h" ? -0.22 : 1 };
  layout.xaxis = {
    ...(layout.xaxis as Record<string, unknown>),
    title: { text: horizontal ? state.yAxisTitle : state.xAxisTitle },
    showgrid: state.showGrid,
    gridcolor: theme.gridColor,
    tickangle: state.labelRotation,
    automargin: true,
  };
  layout.yaxis = {
    ...(layout.yaxis as Record<string, unknown>),
    title: { text: horizontal ? state.xAxisTitle : state.yAxisTitle },
    showgrid: state.showGrid,
    gridcolor: theme.gridColor,
    automargin: true,
  };
  if (barmode) {
    layout.barmode = barmode;
  }
  layout.annotations = state.subtitle
    ? [
        {
          text: state.subtitle,
          x: 0,
          xref: "paper",
          y: 1.12,
          yref: "paper",
          showarrow: false,
          align: "left",
          font: { size: Math.round(12 * state.fontScale), color: theme.textColor },
        },
      ]
    : [];

  return layout;
}

function buildConfig(chart: ChartSpec) {
  return {
    ...cloneValue(chart.plotly_config),
    responsive: true,
    displaylogo: false,
  };
}

export function applyEditableStateToPlotlySpec(chart: ChartSpec, state: EditableChartState): ChartEditorResultSpec {
  return {
    data: buildDataForType(chart, state),
    layout: buildLayoutForState(chart, state),
    config: buildConfig(chart),
  };
}

export function deriveChartDataTable(chart: ChartSpec): ChartDataTableModel | null {
  const payload = (chart.data ?? {}) as Record<string, unknown>;

  if (Array.isArray(payload.labels) && Array.isArray(payload.values)) {
    const labels = coerceStringArray(payload.labels);
    const values = Array.isArray(payload.values) ? payload.values : [];
    return {
      columns: ["Categoria", "Valor"],
      rows: labels.map((label, index) => ({
        Categoria: label,
        Valor: (values[index] as string | number | null | undefined) ?? null,
      })),
      sourceLabel: "Distribucion simple",
    };
  }

  if (Array.isArray(payload.categories) && Array.isArray(payload.series)) {
    const categories = coerceStringArray(payload.categories);
    const series = payload.series as Array<Record<string, unknown>>;
    return {
      columns: ["Categoria", ...series.map((serie) => String(serie.name ?? "Serie"))],
      rows: categories.map((category, index) => {
        const row: Record<string, string | number | null> = { Categoria: category };
        series.forEach((serie) => {
          row[String(serie.name ?? "Serie")] = Array.isArray(serie.values)
            ? ((serie.values[index] as string | number | null | undefined) ?? null)
            : null;
        });
        return row;
      }),
      sourceLabel: "Categorias por serie",
    };
  }

  if (Array.isArray(payload.x) && Array.isArray(payload.y) && !Array.isArray(payload.z)) {
    const x = payload.x as unknown[];
    const y = payload.y as unknown[];
    return {
      columns: ["X", "Y"],
      rows: x.slice(0, 200).map((value, index) => ({
        X: (value as string | number | null | undefined) ?? null,
        Y: (y[index] as string | number | null | undefined) ?? null,
      })),
      sourceLabel: "Pares del grafico",
    };
  }

  if (Array.isArray(payload.values)) {
    const values = payload.values as unknown[];
    return {
      columns: ["Valor"],
      rows: values.slice(0, 200).map((value) => ({ Valor: (value as string | number | null | undefined) ?? null })),
      sourceLabel: "Distribucion numerica",
    };
  }

  if (Array.isArray(payload.z)) {
    const x = coerceStringArray(payload.x);
    const y = coerceStringArray(payload.y);
    const z = coerceMatrix(payload.z);
    return {
      columns: ["Fila", ...x],
      rows: y.map((label, rowIndex) => {
        const row: Record<string, string | number | null> = { Fila: label };
        x.forEach((columnLabel, columnIndex) => {
          const value = z[rowIndex]?.[columnIndex];
          row[columnLabel] = Number.isFinite(value) ? value : null;
        });
        return row;
      }),
      sourceLabel: "Matriz",
    };
  }

  return null;
}

export function buildEditorWarnings(chart: ChartSpec, state: EditableChartState) {
  const warnings = [...chart.warnings];
  const safeTypes = getSafeAvailableChartTypes(chart);

  if (!safeTypes.includes(state.chartType)) {
    warnings.push("Este tipo de grafico puede no representar adecuadamente este resultado.");
  }

  if (chart.chart_type !== state.chartType && chart.chart_type !== "bar" && chart.chart_type !== "horizontal_bar") {
    warnings.push("Has cambiado la visualizacion recomendada. Revisa que la forma elegida siga siendo adecuada para el resultado.");
  }

  warnings.push("Este grafico ayuda a visualizar el resultado, pero la interpretacion estadistica debe basarse en la prueba correspondiente.");
  return Array.from(new Set(warnings));
}
