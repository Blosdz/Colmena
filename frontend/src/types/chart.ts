export type ChartType =
  | "bar"
  | "horizontal_bar"
  | "grouped_bar"
  | "stacked_bar"
  | "pie"
  | "donut"
  | "histogram"
  | "boxplot"
  | "scatter"
  | "heatmap"
  | "line"
  | "mosaic_future";

export interface ChartEditableOptions {
  can_change_chart_type: boolean;
  available_chart_types: string[];
  can_edit_title: boolean;
  can_edit_subtitle: boolean;
  can_edit_axis_labels: boolean;
  can_show_percentages: boolean;
  can_show_frequencies: boolean;
  can_show_values: boolean;
  can_show_legend: boolean;
  can_change_palette: boolean;
  can_change_orientation: boolean;
  can_group_by: boolean;
  can_export_future: boolean;
  notes: string[];
}

export interface ChartTarget {
  target_type: string;
  target_id: string;
  role?: string | null;
  label?: string | null;
}

export interface ChartSpec {
  chart_id: string;
  form_id: string;
  project_id: string;
  chart_type: ChartType | string;
  title: string;
  subtitle?: string | null;
  description: string;
  source_type: string;
  source_reference?: string | null;
  targets: ChartTarget[];
  data: Record<string, unknown> | unknown[];
  encoding: Record<string, unknown>;
  plotly_data: Record<string, unknown>[];
  plotly_layout: Record<string, unknown>;
  plotly_config: Record<string, unknown>;
  theme: Record<string, unknown>;
  editable_options: ChartEditableOptions;
  recommended_alternatives: string[];
  academic_note: string;
  plain_language_explanation: string;
  warnings: string[];
  ready_for_frontend: boolean;
  ready_for_export: boolean;
  created_at: string;
}

export interface ChartBatch {
  form_id: string;
  project_id: string;
  total_charts: number;
  charts: ChartSpec[];
  warnings: string[];
}

export interface ChartOptions {
  form_id: string;
  available_chart_types: string[];
  available_themes: string[];
  recommended_charts: Array<{
    chart_type: string;
    analysis_goal: string;
    reason: string;
  }>;
  available_targets: Record<string, ChartTarget[]>;
  analysis_runs: Array<{
    id: string;
    analysis_type: string;
    created_at: string;
  }>;
}
