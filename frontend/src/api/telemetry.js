import { apiRequest } from './client.js';

export function getStudyTelemetry(studyId) {
  return apiRequest(`/studies/${studyId}/telemetry`);
}

export function getProjectTelemetry(projectId) {
  return apiRequest(`/projects/${projectId}/telemetry`);
}
