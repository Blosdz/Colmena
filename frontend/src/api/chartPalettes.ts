import { apiClient } from "./client";

export interface ChartPaletteRead {
  id: string;
  form_id: string;
  chart_key: string;
  project_id: string;
  colors: string[];
  created_at: string;
  updated_at: string;
}

export function getChartPalette(formId: string, chartKey: string) {
  return apiClient.get<ChartPaletteRead>(
    `/api/v1/forms/${formId}/chart-palettes/${chartKey}`,
  );
}

export function saveChartPalette(formId: string, chartKey: string, colors: string[]) {
  return apiClient.put<ChartPaletteRead>(
    `/api/v1/forms/${formId}/chart-palettes/${chartKey}`,
    { colors },
  );
}

export function deleteChartPalette(formId: string, chartKey: string) {
  return apiClient.delete<{ status: string; chart_key: string }>(
    `/api/v1/forms/${formId}/chart-palettes/${chartKey}`,
  );
}
