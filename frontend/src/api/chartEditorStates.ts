import { apiClient } from "./client";

export interface ChartEditorStateRead {
  id: string;
  storage_key: string;
  form_id: string;
  chart_id: string;
  project_id: string;
  graphs_json: Record<string, unknown> | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ChartEditorStateListRead {
  form_id: string;
  total: number;
  items: ChartEditorStateRead[];
}

export interface ChartEditorStateSave {
  storage_key: string;
  graphs_json: Record<string, unknown> | null;
  metadata_json?: Record<string, unknown> | null;
}

export function upsertChartEditorState(formId: string, chartId: string, payload: ChartEditorStateSave) {
  return apiClient.put<ChartEditorStateRead>(
    `/api/v1/forms/${formId}/chart-editor-states/${chartId}`,
    payload,
  );
}

export function listChartEditorStates(formId: string) {
  return apiClient.get<ChartEditorStateListRead>(`/api/v1/forms/${formId}/chart-editor-states`);
}

export function getChartEditorState(formId: string, chartId: string) {
  return apiClient.get<ChartEditorStateRead>(
    `/api/v1/forms/${formId}/chart-editor-states/${chartId}`,
  );
}

export function deleteChartEditorState(formId: string, chartId: string) {
  return apiClient.delete<{ status: string; chart_id: string }>(
    `/api/v1/forms/${formId}/chart-editor-states/${chartId}`,
  );
}
