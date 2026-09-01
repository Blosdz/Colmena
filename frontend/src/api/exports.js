import { API_BASE_URL, apiRequest } from './client.js';

export function createExport(studyId, payload) {
  return apiRequest(`/studies/${studyId}/exports`, { method: 'POST', body: payload });
}

export function getExport(exportId) {
  return apiRequest(`/exports/${exportId}`);
}

export function getExportDownloadUrl(exportId) {
  return `${API_BASE_URL}/exports/${exportId}/download`;
}

export function listExports(studyId) {
  return apiRequest(`/studies/${studyId}/exports`);
}
