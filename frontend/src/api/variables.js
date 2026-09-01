import { apiRequest } from './client.js';

export function listVariables(projectId, { page = 1, pageSize = 50 } = {}) {
  return apiRequest(`/projects/${projectId}/variables?page=${page}&page_size=${pageSize}`);
}

export function createVariable(projectId, payload) {
  return apiRequest(`/projects/${projectId}/variables`, { method: 'POST', body: payload });
}

export function batchUpdateVariables(projectId, items) {
  return apiRequest(`/projects/${projectId}/variables/batch`, {
    method: 'PATCH',
    body: { items },
  });
}

export function getVariable(variableId) {
  return apiRequest(`/variables/${variableId}`);
}

export function updateVariable(variableId, payload) {
  return apiRequest(`/variables/${variableId}`, { method: 'PATCH', body: payload });
}

export function deleteVariable(variableId) {
  return apiRequest(`/variables/${variableId}`, { method: 'DELETE' });
}

export function listExogenousFields(projectId) {
  return apiRequest(`/projects/${projectId}/exogenous-fields`);
}

export function createExogenousField(projectId, payload) {
  return apiRequest(`/projects/${projectId}/exogenous-fields`, { method: 'POST', body: payload });
}
