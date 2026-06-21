export interface NumericSummary {
  valid_n: number;
  missing_n: number;
  mean?: number | null;
  median?: number | null;
  mode?: number | null;
  standard_deviation?: number | null;
  variance?: number | null;
  minimum?: number | null;
  maximum?: number | null;
  range?: number | null;
  skewness?: number | null;
  kurtosis?: number | null;
  percentile_25?: number | null;
  percentile_50?: number | null;
  percentile_75?: number | null;
}

export interface FrequencyRow {
  label?: string | null;
  value?: string | null;
  frequency: number;
  percent?: number | null;
  valid_percent?: number | null;
  cumulative_percent?: number | null;
}

export interface QuestionDescriptive {
  question_id: string;
  code?: string | null;
  label: string;
  question_type: string;
  question_role: string;
  measurement_level: string;
  data_type: string;
  is_scored: boolean;
  valid_n: number;
  missing_n: number;
  frequencies: FrequencyRow[];
  numeric?: NumericSummary | null;
  warnings: string[];
}

export interface DescriptiveOverview {
  form_id: string;
  project_id: string;
  total_responses: number;
  included_responses: number;
  discarded_responses: number;
  total_questions: number;
  scored_questions: number;
  categorical_questions: number;
  numeric_questions: number;
  missing_overview: Record<string, unknown>;
  warnings: string[];
}

export interface DescriptiveReport {
  form_id: string;
  project_id: string;
  mode: string;
  decimals: number;
  overview: DescriptiveOverview;
  questions: QuestionDescriptive[];
  dimensions: Array<Record<string, unknown>>;
  instruments: Array<Record<string, unknown>>;
  project_variables: Array<Record<string, unknown>>;
}

export interface AnalysisTarget {
  target_type: string;
  target_id: string;
  role?: string | null;
  label: string;
}

export interface AnalysisWorkflow {
  analysis_goal: string;
  title: string;
  description: string;
  required_roles: string[];
}

export interface AnalysisOptions {
  form_id: string;
  goals: string[];
  available_targets: Record<string, AnalysisTarget[]>;
  recommended_workflows: AnalysisWorkflow[];
}

export interface AnalysisSummaryRead {
  form_id: string;
  project_id: string;
  total_responses: number;
  included_responses: number;
  data_quality: Record<string, unknown>;
  available_analyses: string[];
  recent_analysis_runs: Array<{
    id: string;
    analysis_type: string;
    status: string;
    created_at: string;
    result_preview?: Record<string, unknown> | null;
  }>;
  warnings: string[];
}

export interface OrchestratedAnalysis {
  form_id: string;
  project_id: string;
  analysis_goal: string;
  status: string;
  analysis_run_id?: string | null;
  title: string;
  executive_summary: string;
  what_was_analyzed: string;
  main_result: string;
  statistical_result: string;
  academic_interpretation: string;
  plain_language_explanation: string;
  assumptions: Array<{
    name: string;
    status: string;
    description: string;
    evidence?: string | null;
  }>;
  warnings: string[];
  recommended_next_steps: string[];
  result_blocks: Array<{
    block_type: string;
    title: string;
    summary: string;
    payload?: unknown;
  }>;
  apa_table_blocks: Array<Record<string, unknown>>;
  chart_blocks: Array<Record<string, unknown>>;
  export_blocks: Array<Record<string, unknown>>;
  raw_results_summary: Record<string, unknown>;
}

export interface RunAnalysisPayload {
  analysis_goal: string;
  targets: Array<{
    target_type: string;
    target_id: string;
    role?: string;
    label?: string;
  }>;
  method?: string;
  alpha?: number;
  decimals?: number;
  include_discarded?: boolean;
  score_aggregation?: "mean" | "sum";
  store_result?: boolean;
  options?: Record<string, unknown>;
}
