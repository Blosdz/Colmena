import { apiClient } from "./client";
import type { PublicFormRead, PublicFormResponseCreate, PublicFormResponseRead } from "../types/publicForm";

export function getPublicForm(publicSlug: string) {
  return apiClient.get<PublicFormRead>(`/api/public/forms/${publicSlug}`);
}

export function submitPublicResponse(publicSlug: string, payload: PublicFormResponseCreate) {
  return apiClient.post<PublicFormResponseRead>(`/api/public/forms/${publicSlug}/responses`, payload);
}
