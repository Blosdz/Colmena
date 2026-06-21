import { apiClient } from "./client";
import type {
  ControlScale,
  ControlScaleCreatePayload,
  ControlScaleItem,
  ControlScaleItemCreatePayload,
  ResponseScore,
  ScoreBand,
  ScoreBandCreatePayload,
  ScoredDataset,
  ScoringConfig,
  ScoringConfigCreatePayload,
  ScoringConfigList,
  ScoringOptions,
  ScoringPreview,
  ScoringResults,
  ScoringRunPayload,
  ScoringRunResult,
} from "../types/scoring";

export function listScoringConfigs(formId: string) {
  return apiClient.get<ScoringConfigList>(`/api/v1/forms/${formId}/scoring/configs`);
}

export function createScoringConfig(formId: string, payload: ScoringConfigCreatePayload) {
  return apiClient.post<ScoringConfig>(`/api/v1/forms/${formId}/scoring/configs`, payload);
}

export function listScoreBands(configId: string) {
  return apiClient.get<ScoreBand[]>(`/api/v1/scoring/configs/${configId}/bands`);
}

export function createScoreBand(configId: string, payload: ScoreBandCreatePayload) {
  return apiClient.post<ScoreBand>(`/api/v1/scoring/configs/${configId}/bands`, payload);
}

export function listControlScales(formId: string) {
  return apiClient.get<ControlScale[]>(`/api/v1/forms/${formId}/control-scales`);
}

export function createControlScale(formId: string, payload: ControlScaleCreatePayload) {
  return apiClient.post<ControlScale>(`/api/v1/forms/${formId}/control-scales`, payload);
}

export function listControlScaleItems(controlScaleId: string) {
  return apiClient.get<ControlScaleItem[]>(`/api/v1/control-scales/${controlScaleId}/items`);
}

export function createControlScaleItem(controlScaleId: string, payload: ControlScaleItemCreatePayload) {
  return apiClient.post<ControlScaleItem>(`/api/v1/control-scales/${controlScaleId}/items`, payload);
}

export function previewScoring(formId: string) {
  return apiClient.post<ScoringPreview>(`/api/v1/forms/${formId}/scoring/preview`);
}

export function runScoring(formId: string, payload: ScoringRunPayload) {
  return apiClient.post<ScoringRunResult>(`/api/v1/forms/${formId}/scoring/run`, payload);
}

export function getScoringResults(formId: string) {
  return apiClient.get<ScoringResults>(`/api/v1/forms/${formId}/scoring/results`);
}

export function getScoringDataset(formId: string) {
  return apiClient.get<ScoredDataset>(`/api/v1/forms/${formId}/scoring/dataset`);
}

export function getScoringOptions(formId: string) {
  return apiClient.get<ScoringOptions>(`/api/v1/forms/${formId}/scoring/options`);
}

export function getResponseScores(responseId: string) {
  return apiClient.get<ResponseScore[]>(`/api/v1/form-responses/${responseId}/scores`);
}
