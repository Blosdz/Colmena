export interface ScoreBand {
  id: string;
  scoring_config_id: string;
  label: string;
  code?: string | null;
  min_value: number;
  max_value: number;
  interpretation?: string | null;
  recommendation?: string | null;
  severity_order: number;
  color_hint?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScoringConfig {
  id: string;
  project_id: string;
  form_id: string;
  instrument_id?: string | null;
  dimension_id?: string | null;
  project_variable_id?: string | null;
  name: string;
  code?: string | null;
  scoring_level: "instrument" | "dimension" | "project_variable" | "custom";
  aggregation_method: "sum" | "mean" | "weighted_mean";
  missing_policy: "strict_complete" | "allow_partial" | "prorate_if_threshold_met";
  min_answered_items?: number | null;
  min_completion_percent?: number | null;
  reverse_scoring_enabled: boolean;
  score_min?: number | null;
  score_max?: number | null;
  interpretation_enabled: boolean;
  config_json?: Record<string, unknown> | unknown[] | null;
  is_active: boolean;
  bands: ScoreBand[];
  created_at: string;
  updated_at: string;
}

export interface ScoringConfigList {
  form_id: string;
  total: number;
  items: ScoringConfig[];
  warnings: string[];
}

export interface ScoreBandCreatePayload {
  label: string;
  code?: string | null;
  min_value: number;
  max_value: number;
  interpretation?: string | null;
  recommendation?: string | null;
  severity_order?: number;
  color_hint?: string | null;
}

export interface ScoringConfigCreatePayload {
  instrument_id?: string | null;
  dimension_id?: string | null;
  project_variable_id?: string | null;
  name: string;
  code?: string | null;
  scoring_level: "instrument" | "dimension" | "project_variable" | "custom";
  aggregation_method: "sum" | "mean" | "weighted_mean";
  missing_policy: "strict_complete" | "allow_partial" | "prorate_if_threshold_met";
  min_answered_items?: number | null;
  min_completion_percent?: number | null;
  reverse_scoring_enabled?: boolean;
  score_min?: number | null;
  score_max?: number | null;
  interpretation_enabled?: boolean;
  config_json?: Record<string, unknown> | unknown[] | null;
  is_active?: boolean;
  bands?: ScoreBandCreatePayload[];
}

export interface ControlScaleItem {
  id: string;
  control_scale_id: string;
  question_id: string;
  expected_option_id?: string | null;
  expected_value_text?: string | null;
  expected_value_number?: number | null;
  fail_if_selected: boolean;
  weight: number;
  pair_group?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ControlScale {
  id: string;
  project_id: string;
  form_id: string;
  instrument_id?: string | null;
  name: string;
  code?: string | null;
  control_type: "lie" | "attention" | "infrequency" | "consistency" | "custom";
  rule_type: "sum_threshold" | "mean_threshold" | "any_failed" | "count_failed" | "paired_inconsistency" | "custom";
  threshold?: number | null;
  comparison_operator?: "gt" | "gte" | "lt" | "lte" | "eq" | null;
  flag_level: "warning" | "invalid";
  message?: string | null;
  config_json?: Record<string, unknown> | unknown[] | null;
  is_active: boolean;
  items: ControlScaleItem[];
  created_at: string;
  updated_at: string;
}

export interface ControlScaleCreatePayload {
  instrument_id?: string | null;
  name: string;
  code?: string | null;
  control_type: "lie" | "attention" | "infrequency" | "consistency" | "custom";
  rule_type: "sum_threshold" | "mean_threshold" | "any_failed" | "count_failed" | "paired_inconsistency" | "custom";
  threshold?: number | null;
  comparison_operator?: "gt" | "gte" | "lt" | "lte" | "eq" | null;
  flag_level: "warning" | "invalid";
  message?: string | null;
  config_json?: Record<string, unknown> | unknown[] | null;
  is_active?: boolean;
  items?: ControlScaleItemCreatePayload[];
}

export interface ControlScaleItemCreatePayload {
  question_id: string;
  expected_option_id?: string | null;
  expected_value_text?: string | null;
  expected_value_number?: number | null;
  fail_if_selected?: boolean;
  weight?: number;
  pair_group?: string | null;
}

export interface ResponseScore {
  id: string;
  project_id: string;
  form_id: string;
  response_id: string;
  scoring_config_id: string;
  instrument_id?: string | null;
  dimension_id?: string | null;
  project_variable_id?: string | null;
  raw_score?: number | null;
  mean_score?: number | null;
  weighted_score?: number | null;
  final_score?: number | null;
  answered_items: number;
  missing_items: number;
  total_items: number;
  completion_percent?: number | null;
  band_id?: string | null;
  band_label?: string | null;
  interpretation?: string | null;
  validity_status: "valid" | "warning" | "invalid";
  warnings_json?: unknown;
  created_at: string;
  updated_at: string;
}

export interface ResponseControlFlag {
  id: string;
  project_id: string;
  form_id: string;
  response_id: string;
  control_scale_id: string;
  score?: number | null;
  failed_items: number;
  total_items: number;
  flag_status: "pass" | "warning" | "invalid";
  message?: string | null;
  details_json?: unknown;
  created_at: string;
  updated_at: string;
}

export interface ScoringRunPayload {
  include_discarded?: boolean;
  recalculate?: boolean;
  store_result?: boolean;
}

export interface ScoringRunResult {
  analysis_run_id?: string | null;
  form_id: string;
  project_id: string;
  total_responses: number;
  scored_responses: number;
  valid_responses: number;
  warning_responses: number;
  invalid_responses: number;
  warnings: string[];
  score_results: ResponseScore[];
  control_flags: ResponseControlFlag[];
}

export interface ScoringBandDistribution {
  scoring_config_id: string;
  scoring_config_name: string;
  level: string;
  n: number;
  percent: number;
  interpretation?: string | null;
}

export interface ControlScaleSummary {
  control_scale_id: string;
  name: string;
  flag_status: "pass" | "warning" | "invalid";
  n: number;
  percent: number;
}

export interface ScoringResults {
  form_id: string;
  total_responses: number;
  scored_responses: number;
  valid_responses: number;
  warning_responses: number;
  invalid_responses: number;
  band_distribution: ScoringBandDistribution[];
  control_flags: ControlScaleSummary[];
  warnings: string[];
}

export interface ScoredDataset {
  form_id: string;
  total_rows: number;
  columns: string[];
  rows: Record<string, unknown>[];
  warnings: string[];
}

export interface ScoringOptions {
  form_id: string;
  instruments: Array<{ id: string; name: string }>;
  dimensions: Array<{ id: string; name: string; instrument_id: string }>;
  scored_questions: Array<{ id: string; label: string; code?: string | null }>;
  reverse_scored_questions: Array<{ id: string; label: string; code?: string | null }>;
  configs: ScoringConfig[];
  control_scales: ControlScale[];
}

export interface ScoringPreview {
  form_id: string;
  warnings: string[];
  score_results: ResponseScore[];
  control_flags: ResponseControlFlag[];
}
