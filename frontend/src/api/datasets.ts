import { apiClient } from "./client";
import type {
  AnswerUpsertPayload,
  AnswerUpsertResult,
  CompletenessSummary,
  DataDictionary,
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

// Dataset con valores legibles para la vista de "base de datos" de Telemetría.
export function getResponsesDataset(formId: string) {
  return apiClient.get<DatasetPreview>(
    `/api/v1/forms/${formId}/dataset?mode=label&include_metadata=true&include_discarded=false&limit=1000`,
  );
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

// ── Grilla de captura manual (vista de datos tipo SPSS) ─────────────────────

export function getManualDataset(formId: string) {
  return apiClient.get<DatasetPreview>(
    `/api/v1/forms/${formId}/dataset?mode=value&include_metadata=true&include_discarded=false&limit=1000`,
  );
}

export function getDataDictionary(formId: string) {
  return apiClient.get<DataDictionary>(`/api/v1/forms/${formId}/data-dictionary`);
}

export function upsertAnswer(responseId: string, questionId: string, payload: AnswerUpsertPayload) {
  return apiClient.put<AnswerUpsertResult>(
    `/api/v1/form-responses/${responseId}/answers/${questionId}`,
    payload,
  );
}

export function createManualResponse(formId: string, respondentCode: string) {
  return apiClient.post<{ id: string }>(`/api/v1/forms/${formId}/responses`, {
    respondent_code: respondentCode,
    status: "partial",
    source: "manual",
    answers: [],
  });
}

export function updateResponseStatus(responseId: string, status: "partial" | "complete" | "discarded") {
  return apiClient.patch<{ response_id: string; status: string }>(
    `/api/v1/form-responses/${responseId}/status`,
    { status },
  );
}
