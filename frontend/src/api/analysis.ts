import { apiClient } from "./client";
import type {
  AnalysisOptions,
  AnalysisSummaryRead,
  OrchestratedAnalysis,
  RunAnalysisPayload,
} from "../types/analysis";

export function getAnalysisOptions(formId: string) {
  return apiClient.get<AnalysisOptions>(`/api/v1/forms/${formId}/analysis/options`);
}

export function getAnalysisSummary(formId: string) {
  return apiClient.get<AnalysisSummaryRead>(`/api/v1/forms/${formId}/analysis/summary`);
}

export function runAnalysis(formId: string, payload: RunAnalysisPayload) {
  return apiClient.post<OrchestratedAnalysis>(`/api/v1/forms/${formId}/analysis/run`, payload);
}

export function runFullScan(
  formId: string,
  payload: Omit<RunAnalysisPayload, "analysis_goal" | "targets" | "method">,
) {
  return apiClient.post<OrchestratedAnalysis>(`/api/v1/forms/${formId}/analysis/full-scan`, payload);
}
