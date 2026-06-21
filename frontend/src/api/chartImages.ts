import { apiClient } from "./client";
import type { ChartImage, ChartImageList, ChartImageUploadResponse } from "../types/chartImage";

export function uploadChartImage(formId: string, payload: Record<string, unknown>) {
  return apiClient.post<ChartImageUploadResponse>(`/api/v1/forms/${formId}/chart-images`, payload);
}

export function listChartImages(formId: string) {
  return apiClient.get<ChartImageList>(`/api/v1/forms/${formId}/chart-images`);
}

export function listWordReadyChartImages(formId: string) {
  return apiClient.get<ChartImageList>(`/api/v1/forms/${formId}/chart-images/word-ready`);
}

export function getChartImage(formId: string, artifactId: string) {
  return apiClient.get<ChartImage>(`/api/v1/forms/${formId}/chart-images/${artifactId}`);
}

export function deleteChartImage(formId: string, artifactId: string) {
  return apiClient.delete<{ status: string; artifact_id: string }>(
    `/api/v1/forms/${formId}/chart-images/${artifactId}`,
  );
}
