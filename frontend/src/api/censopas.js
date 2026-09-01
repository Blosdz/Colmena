import { apiRequest } from './client.js';

export function getCensopasCatalog() {
  return apiRequest('/censopas/catalog', { skipAuth: true });
}
