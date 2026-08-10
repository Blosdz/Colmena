import { apiClient } from "./client";

export interface ChartImageUploadPayload {
  chart_id: string;
  chart_type: string;
  title: string;
  data_url: string;
}

export interface ChartImageRead {
  artifact_id: string;
  form_id: string;
  project_id: string;
  chart_id: string | null;
  chart_type: string | null;
  title: string | null;
  format: string;
  file_name: string | null;
  file_path: string;
  mime_type: string;
  file_size_bytes: number;
  created_at: string;
  metadata_json: Record<string, unknown> | null;
}

export interface ChartImageUploadResponse {
  status: string;
  image: ChartImageRead;
  message: string | null;
}

/** Sube una captura PNG (data URL) de una gráfica Chart.js en vivo, para que quede disponible como figura "word-ready". */
export function uploadChartImage(formId: string, payload: ChartImageUploadPayload) {
  return apiClient.post<ChartImageUploadResponse>(`/api/v1/forms/${formId}/chart-images`, {
    ...payload,
    format: "png",
    source_type: "manual",
  });
}
