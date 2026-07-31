import { apiClient } from "./client";

export type BaremoGroupKind = "variable" | "dimension" | "custom";

export interface BaremoTableRow {
  category: string;
  frequency: number;
}

export interface BaremoTableState {
  id: string;
  form_id: string;
  project_id: string;
  user_id: string | null;
  table_key: string;
  group_kind: BaremoGroupKind;
  title: string;
  rows: BaremoTableRow[];
  created_at: string;
  updated_at: string;
}

export interface BaremoTableStateList {
  form_id: string;
  total: number;
  items: BaremoTableState[];
}

export interface BaremoTableSavePayload {
  title: string;
  group_kind: BaremoGroupKind;
  rows: BaremoTableRow[];
}

export function listBaremoTables(formId: string) {
  return apiClient.get<BaremoTableStateList>(`/api/v1/forms/${formId}/baremo-tables`);
}

export function upsertBaremoTable(formId: string, tableKey: string, payload: BaremoTableSavePayload) {
  return apiClient.put<BaremoTableState>(`/api/v1/forms/${formId}/baremo-tables/${tableKey}`, payload);
}

export function deleteBaremoTable(formId: string, tableKey: string) {
  return apiClient.delete<{ status: string; table_key: string }>(
    `/api/v1/forms/${formId}/baremo-tables/${tableKey}`,
  );
}
