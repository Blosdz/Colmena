import { apiRequest } from './client.js';

export function createActionPlan(studyId, payload) {
  return apiRequest(`/studies/${studyId}/action-plans`, { method: 'POST', body: payload });
}

export function listActionPlans(studyId) {
  return apiRequest(`/studies/${studyId}/action-plans`);
}

export function addActionPlanItem(actionPlanId, payload) {
  return apiRequest(`/action-plans/${actionPlanId}/items`, { method: 'POST', body: payload });
}

export function listActionPlanItems(actionPlanId) {
  return apiRequest(`/action-plans/${actionPlanId}/items`);
}

export function updateActionPlanItem(itemId, payload) {
  return apiRequest(`/action-plan-items/${itemId}`, { method: 'PATCH', body: payload });
}

export function createKpi(studyId, payload) {
  return apiRequest(`/studies/${studyId}/kpis`, { method: 'POST', body: payload });
}

export function listKpis(studyId) {
  return apiRequest(`/studies/${studyId}/kpis`);
}

export function addKpiMeasurement(kpiId, payload) {
  return apiRequest(`/kpis/${kpiId}/measurements`, { method: 'POST', body: payload });
}

export function listKpiMeasurements(kpiId) {
  return apiRequest(`/kpis/${kpiId}/measurements`);
}
