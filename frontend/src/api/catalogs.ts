import { apiClient } from "./client";
import type { CatalogRef } from "../types/project";

export interface CatalogItem extends CatalogRef {
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CatalogListResponse {
  items: CatalogItem[];
  total: number;
}

export function listResearchTypes() {
  return apiClient.get<CatalogListResponse>("/api/v1/catalogs/research-types");
}

export function listDesignTypes() {
  return apiClient.get<CatalogListResponse>("/api/v1/catalogs/design-types");
}

export function listApproaches() {
  return apiClient.get<CatalogListResponse>("/api/v1/catalogs/approaches");
}
