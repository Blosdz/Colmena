import { apiRequest } from './client.js';

export function listOrganizations() {
  return apiRequest('/organizations');
}

export function joinOrganization(code) {
  return apiRequest('/organizations/join', { method: 'POST', body: { code } });
}

export function createCollaboratorCode(organizationId, label = 'Colaboradores') {
  return apiRequest(`/organizations/${organizationId}/collaborator-codes`, {
    method: 'POST',
    body: { label },
  });
}
