import { apiClient } from "./client";
import type { Scale, ScaleListResponse } from "../types/scale";

/** Presets del sistema (siempre) + escalas del proyecto si se pasa projectId. */
export function listScales(projectId?: string) {
  return apiClient.get<ScaleListResponse>(
    "/api/v1/scales",
    projectId ? { project_id: projectId } : undefined,
  );
}

export type ScaleCreatePayload = {
  name: string;
  scale_kind: string;
  render_style: string;
  points: number;
  options: { value: number; label: string; sort_order: number }[];
};

/** Crea una escala del catálogo del proyecto (persiste los puntos del Likert elegidos). */
export function createScale(projectId: string, payload: ScaleCreatePayload) {
  return apiClient.post<Scale>(`/api/v1/projects/${projectId}/scales`, payload);
}
