import type { ChartSpec } from "./chart";

export type ChartThemeName =
  | "academic_light"
  | "colmena_premium"
  | "presentation_clean"
  | "monochrome_apa";

export type ChartOrientation = "vertical" | "horizontal";

export interface EditableChartState {
  chartType: string;
  title: string;
  subtitle: string;
  xAxisTitle: string;
  yAxisTitle: string;
  theme: ChartThemeName;
  orientation: ChartOrientation;
  showPercentages: boolean;
  showFrequencies: boolean;
  showValues: boolean;
  showLegend: boolean;
  showGrid: boolean;
  showDataTable: boolean;
  showAdvancedJson: boolean;
  selectedPalette: string;
  labelRotation: number;
  fontScale: number;
  rawSpec: Pick<ChartSpec, "chart_id" | "chart_type" | "source_type">;
}

export type PersistedChartState = Omit<EditableChartState, "rawSpec">;

export interface ChartEditorPreset {
  key: ChartThemeName;
  label: string;
  description: string;
}

export interface ChartDataTableModel {
  columns: string[];
  rows: Array<Record<string, string | number | null>>;
  sourceLabel: string;
}

export interface ChartEditorResultSpec {
  data: Record<string, unknown>[];
  layout: Record<string, unknown>;
  config: Record<string, unknown>;
}
