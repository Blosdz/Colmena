import { apiRequest } from './client.js';

export function createSurvey(projectId, payload) {
  return apiRequest(`/projects/${projectId}/surveys`, { method: 'POST', body: payload });
}

export function createSurveyFromInstrument(projectId, payload) {
  return apiRequest(`/projects/${projectId}/surveys/from-instrument`, {
    method: 'POST',
    body: payload,
  });
}

export function listSurveys(projectId, { page = 1, pageSize = 50 } = {}) {
  return apiRequest(`/projects/${projectId}/surveys?page=${page}&page_size=${pageSize}`);
}

export function getSurvey(surveyId) {
  return apiRequest(`/surveys/${surveyId}`);
}

export function updateSurvey(surveyId, payload) {
  return apiRequest(`/surveys/${surveyId}`, { method: 'PATCH', body: payload });
}

export function deleteSurvey(surveyId) {
  return apiRequest(`/surveys/${surveyId}`, { method: 'DELETE' });
}
