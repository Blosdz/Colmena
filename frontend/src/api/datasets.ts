import { apiClient } from "./client";
import type {
  CompletenessSummary,
  DatasetExportArtifact,
  DatasetExportList,
  DatasetPreview,
} from "../types/dataset";

const defaultExportPayload = {
  mode: "mixed",
  include_metadata: true,
  include_discarded: false,
  expand_multiple_choice: false,
};

export function getDatasetPreview(formId: string) {
  return apiClient.get<DatasetPreview>(`/api/v1/forms/${formId}/dataset/preview`);
}

export function getCompleteness(formId: string) {
  return apiClient.get<CompletenessSummary>(`/api/v1/forms/${formId}/completeness`);
}

export function exportExcel(formId: string) {
  return apiClient.post<DatasetExportArtifact>(`/api/v1/forms/${formId}/exports/excel`, defaultExportPayload);
}

export function exportCsv(formId: string) {
  return apiClient.post<DatasetExportArtifact>(`/api/v1/forms/${formId}/exports/csv`, defaultExportPayload);
}

export function listFormExports(formId: string) {
  return apiClient.get<DatasetExportList>(`/api/v1/forms/${formId}/exports`);
}
