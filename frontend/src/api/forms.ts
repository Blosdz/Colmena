import { apiClient } from "./client";
import type {
  Form,
  FormDimension,
  FormDimensionPayload,
  FormInstrument,
  FormInstrumentPayload,
  FormListResponse,
  FormQuestion,
  FormQuestionOption,
  FormQuestionOptionPayload,
  FormQuestionPayload,
  FormResponseList,
  FormSection,
  FormSectionPayload,
  PublicFormLink,
} from "../types/form";

export function listProjectForms(projectId: string) {
  return apiClient.get<FormListResponse>(`/api/v1/projects/${projectId}/forms`);
}

export function createForm(projectId: string, payload: Record<string, unknown>) {
  return apiClient.post<Form>(`/api/v1/projects/${projectId}/forms`, payload);
}

export function getForm(formId: string) {
  return apiClient.get<Form>(`/api/v1/forms/${formId}`);
}

export function getPublicLink(formId: string) {
  return apiClient.get<PublicFormLink>(`/api/v1/forms/${formId}/public-link`);
}

export function publishForm(formId: string) {
  return apiClient.post<PublicFormLink>(`/api/v1/forms/${formId}/publish`);
}

export function closeForm(formId: string) {
  return apiClient.post<Form>(`/api/v1/forms/${formId}/close`);
}

export function reopenForm(formId: string) {
  return apiClient.post<Form>(`/api/v1/forms/${formId}/reopen`);
}

export function listResponses(formId: string) {
  return apiClient.get<FormResponseList>(`/api/v1/forms/${formId}/responses`);
}

export function createSection(formId: string, payload: FormSectionPayload) {
  return apiClient.post<FormSection>(`/api/v1/forms/${formId}/sections`, payload);
}

export function listSections(formId: string) {
  return apiClient.get<{ items: FormSection[]; total: number }>(`/api/v1/forms/${formId}/sections`);
}

export function createInstrument(formId: string, payload: FormInstrumentPayload) {
  return apiClient.post<FormInstrument>(`/api/v1/forms/${formId}/instruments`, payload);
}

export function listInstruments(formId: string) {
  return apiClient.get<{ items: FormInstrument[]; total: number }>(`/api/v1/forms/${formId}/instruments`);
}

export function createDimension(instrumentId: string, payload: FormDimensionPayload) {
  return apiClient.post<FormDimension>(`/api/v1/form-instruments/${instrumentId}/dimensions`, payload);
}

export function listDimensions(instrumentId: string) {
  return apiClient.get<{ items: FormDimension[]; total: number }>(
    `/api/v1/form-instruments/${instrumentId}/dimensions`,
  );
}

export function createQuestion(formId: string, payload: FormQuestionPayload) {
  return apiClient.post<FormQuestion>(`/api/v1/forms/${formId}/questions`, payload);
}

export function listQuestions(formId: string) {
  return apiClient.get<{ items: FormQuestion[]; total: number }>(`/api/v1/forms/${formId}/questions`);
}

export function createQuestionOption(questionId: string, payload: FormQuestionOptionPayload) {
  return apiClient.post<FormQuestionOption>(`/api/v1/form-questions/${questionId}/options`, payload);
}

export function listQuestionOptions(questionId: string) {
  return apiClient.get<{ items: FormQuestionOption[]; total: number }>(
    `/api/v1/form-questions/${questionId}/options`,
  );
}
