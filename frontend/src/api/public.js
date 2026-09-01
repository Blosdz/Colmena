import { API_ROOT_URL, apiRequest } from './client.js';

export function getPublicStudy(publicId) {
  return apiRequest(`/public/studies/${publicId}`, { skipAuth: true });
}

/**
 * Resuelve un formulario público por slug (shim de compatibilidad con
 * AppThesis, fuera del prefijo /api/v1). Devuelve el bundle de la encuesta,
 * que incluye `study_public_id` para continuar por el flujo normal.
 */
export async function getPublicFormBySlug(slug) {
  const response = await fetch(
    `${API_ROOT_URL}/api/public/forms/${encodeURIComponent(slug)}`,
    { headers: { Accept: 'application/json' } },
  );
  if (!response.ok) {
    throw new Error(`No se pudo cargar el formulario (${response.status})`);
  }
  return response.json();
}

export function createPublicResponseSession(publicId) {
  return apiRequest(`/public/studies/${publicId}/response-sessions`, {
    method: 'POST',
    skipAuth: true,
  });
}
