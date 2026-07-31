import { apiClient } from "./client";

// ---------- Fiabilidad (Alfa de Cronbach) ----------

export interface ItemReliability {
  item_id: string;
  label: string | null;
  item_total_correlation: number | null;
  alpha_if_deleted: number | null;
}

export interface CronbachAlphaResult {
  alpha: number | null;
  standardized_alpha: number | null;
  n_items: number;
  n_valid_cases: number;
  n_excluded_cases: number;
  average_inter_item_correlation: number | null;
  sum_item_variances: number | null;
  total_variance: number | null;
  classification: string;
  interpretation: string;
  items: ItemReliability[];
  warnings: string[];
}

export interface ReliabilityTarget {
  target_type: string;
  target_id: string;
  target_name: string;
  item_count: number;
  result: CronbachAlphaResult;
}

export interface ReliabilityReport {
  form_id: string;
  project_id: string;
  include_discarded: boolean;
  total_targets: number;
  applicable_targets: number;
  results: ReliabilityTarget[];
  warnings: string[];
}

export function getReliabilityByInstrument(formId: string) {
  return apiClient.get<ReliabilityReport>(`/api/v1/forms/${formId}/reliability/instruments`);
}

export function getReliabilityByDimension(formId: string) {
  return apiClient.get<ReliabilityReport>(`/api/v1/forms/${formId}/reliability/dimensions`);
}

// ---------- Normalidad (Shapiro-Wilk / Kolmogorov-Smirnov) ----------

export type NormalityMethod = "auto" | "shapiro" | "lilliefors" | "dagostino";

export interface NormalityDescriptiveContext {
  mean: number | null;
  median: number | null;
  std_dev: number | null;
  skewness: number | null;
  kurtosis: number | null;
  has_outliers_iqr: boolean | null;
}

export interface NormalityTestResult {
  target_type: string;
  target_id: string;
  target_name: string;
  method: string;
  statistic: number | null;
  p_value: number | null;
  alpha: number;
  valid_n: number;
  missing_n: number;
  missing_percent: number;
  classification: string;
  interpretation: string;
  warnings: string[];
  descriptive_context: NormalityDescriptiveContext;
}

export interface NormalityReport {
  form_id: string;
  project_id: string;
  method: string;
  alpha: number;
  include_discarded: boolean;
  score_aggregation: string;
  total_targets: number;
  applicable_targets: number;
  normal_count: number;
  non_normal_count: number;
  inconclusive_count: number;
  not_applicable_count: number;
  results: NormalityTestResult[];
  warnings: string[];
}

export function getNormalityByDimension(formId: string, method: NormalityMethod = "auto") {
  return apiClient.get<NormalityReport>(`/api/v1/forms/${formId}/normality/dimensions?method=${method}`);
}

export function getNormalityByVariable(formId: string, method: NormalityMethod = "auto") {
  return apiClient.get<NormalityReport>(`/api/v1/forms/${formId}/normality/project-variables?method=${method}`);
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface NormalCurvePoint {
  x: number;
  y: number;
}

export interface NormalityHistogram {
  target_type: string;
  target_id: string;
  target_name: string;
  mean: number | null;
  std: number | null;
  valid_n: number;
  bins: HistogramBin[];
  curve: NormalCurvePoint[];
  warnings: string[];
}

export function getNormalityHistogram(formId: string, targetType: string, targetId: string) {
  return apiClient.get<NormalityHistogram>(
    `/api/v1/forms/${formId}/normality/histogram?target_type=${targetType}&target_id=${targetId}`,
  );
}
