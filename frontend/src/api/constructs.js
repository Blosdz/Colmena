import { apiRequest } from './client.js';

export function createStructureVariable(versionId, payload) {
  return apiRequest(`/instrument-versions/${versionId}/structure-variables`, { method: 'POST', body: payload });
}

export function listConstructs(versionId) {
  return apiRequest(`/instrument-versions/${versionId}/constructs`);
}

export function createConstruct(versionId, payload) {
  return apiRequest(`/instrument-versions/${versionId}/constructs`, {
    method: 'POST',
    body: payload,
  });
}

export function batchUpdateConstructs(versionId, items) {
  return apiRequest(`/instrument-versions/${versionId}/constructs/batch`, {
    method: 'PATCH',
    body: { items },
  });
}

export function getConstruct(constructId) {
  return apiRequest(`/constructs/${constructId}`);
}

export function updateConstruct(constructId, payload) {
  return apiRequest(`/constructs/${constructId}`, { method: 'PATCH', body: payload });
}

export function deleteConstruct(constructId) {
  return apiRequest(`/constructs/${constructId}`, { method: 'DELETE' });
}

export function linkItemToConstruct(constructId, payload) {
  return apiRequest(`/constructs/${constructId}/items`, { method: 'POST', body: payload });
}

export function updateConstructItem(constructId, questionId, payload) {
  return apiRequest(`/constructs/${constructId}/items/${questionId}`, {
    method: 'PATCH',
    body: payload,
  });
}

export function unlinkConstructItem(constructId, questionId) {
  return apiRequest(`/constructs/${constructId}/items/${questionId}`, { method: 'DELETE' });
}
