import { apiRequest } from './client.js';

export function registerUser({ email, username, password, firstName, lastName }) {
  return apiRequest('/auth/register', {
    method: 'POST',
    skipAuth: true,
    body: {
      email,
      username,
      password,
      first_name: firstName || null,
      last_name: lastName || null,
    },
  });
}

export function loginUser({ email, password }) {
  return apiRequest('/auth/login', {
    method: 'POST',
    skipAuth: true,
    body: { email, password },
  });
}

export function fetchCurrentUser() {
  return apiRequest('/auth/me');
}

/**
 * Vincula la cuenta a partir de un JWT de AppThesis (cross-login del monorepo
 * fullProyect). Tras esto el mismo JWT sirve como Bearer en el resto de la API.
 */
export function linkAppthesis(token) {
  return apiRequest('/auth/appthesis', {
    method: 'POST',
    skipAuth: true,
    headers: { Authorization: `Bearer ${token}` },
  });
}
