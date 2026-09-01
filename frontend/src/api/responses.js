import { apiRequest } from './client.js';

export function createResponseSession(studyId) {
  return apiRequest(`/studies/${studyId}/response-sessions`, { method: 'POST', skipAuth: true });
}

export function upsertResponse(sessionId, questionId, payload) {
  return apiRequest(`/response-sessions/${sessionId}/responses/${questionId}`, {
    method: 'PUT',
    body: payload,
    skipAuth: true,
  });
}

export function completeResponseSession(sessionId, payload = {}) {
  return apiRequest(`/response-sessions/${sessionId}/complete`, {
    method: 'POST',
    body: payload,
    skipAuth: true,
  });
}
