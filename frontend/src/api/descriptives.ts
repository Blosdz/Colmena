import { apiClient } from "./client";
import type { DescriptiveOverview, DescriptiveReport, DimensionDescriptiveListResponse } from "../types/analysis";

export function getDescriptiveOverview(formId: string) {
  return apiClient.get<DescriptiveOverview>(`/api/v1/forms/${formId}/descriptives/overview`);
}

export function getDescriptives(formId: string) {
  return apiClient.get<DescriptiveReport>(`/api/v1/forms/${formId}/descriptives`);
}

export function getDimensionDescriptives(formId: string) {
  return apiClient.get<DimensionDescriptiveListResponse>(`/api/v1/forms/${formId}/descriptives/dimensions`);
}
