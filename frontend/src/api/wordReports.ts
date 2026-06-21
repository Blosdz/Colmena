import { apiClient } from "./client";
import type { WordReport, WordReportGeneratePayload, WordReportOptions } from "../types/wordReport";

export function generateWordReport(formId: string, payload: WordReportGeneratePayload) {
  return apiClient.post<WordReport>(`/api/v1/forms/${formId}/word-reports/generate`, payload);
}

export function getWordReportOptions(formId: string) {
  return apiClient.get<WordReportOptions>(`/api/v1/forms/${formId}/word-reports/options`);
}

export function listWordReports(formId: string) {
  return apiClient.get<WordReport[]>(`/api/v1/forms/${formId}/word-reports`);
}
