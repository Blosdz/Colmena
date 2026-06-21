import { apiClient } from "./client";
import type { ChartBatch, ChartOptions, ChartSpec } from "../types/chart";

export function generateChart(formId: string, payload: Record<string, unknown>) {
  return apiClient.post<ChartSpec>(`/api/v1/forms/${formId}/charts/generate`, payload);
}

export function getRecommendedCharts(formId: string, query?: Record<string, string | number | boolean>) {
  return apiClient.get<ChartBatch>(`/api/v1/forms/${formId}/charts/recommended`, query);
}

export function getChartOptions(formId: string) {
  return apiClient.get<ChartOptions>(`/api/v1/forms/${formId}/charts/options`);
}

export function generateChartsFromAnalysisRun(formId: string, analysisRunId: string) {
  return apiClient.post<ChartBatch>(`/api/v1/forms/${formId}/charts/from-analysis-run/${analysisRunId}`);
}

export function generateChartsFromOrchestratedRun(formId: string, analysisRunId: string) {
  return apiClient.post<ChartBatch>(
    `/api/v1/forms/${formId}/charts/from-orchestrated-run/${analysisRunId}`,
  );
}

export function exportChartSpecs(formId: string, payload: Record<string, unknown>) {
  return apiClient.post<Record<string, unknown>>(`/api/v1/forms/${formId}/charts/export/json`, payload);
}
