import { apiClient } from "./client";
import type { ApaTable, ApaTableBatch } from "../types/apaTable";

export function generateApaTable(formId: string, payload: Record<string, unknown>) {
  return apiClient.post<ApaTable>(`/api/v1/forms/${formId}/apa-tables/generate`, payload);
}

export function generateApaBatch(formId: string, payload: Record<string, unknown>) {
  return apiClient.post<ApaTableBatch>(`/api/v1/forms/${formId}/apa-tables/batch`, payload);
}

export function getApaOptions(formId: string) {
  return apiClient.get<Record<string, unknown>>(`/api/v1/forms/${formId}/apa-tables/options`);
}
