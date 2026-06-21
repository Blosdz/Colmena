import { apiClient } from "./client";
import type {
  Project,
  ProjectCreatePayload,
  ProjectListResponse,
  ProjectVariable,
  ProjectVariableCreatePayload,
  ProjectVariableListResponse,
} from "../types/project";

export function listProjects() {
  return apiClient.get<ProjectListResponse>("/api/v1/projects");
}

export function createProject(payload: ProjectCreatePayload) {
  return apiClient.post<Project>("/api/v1/projects", payload);
}

export function getProject(projectId: string) {
  return apiClient.get<Project>(`/api/v1/projects/${projectId}`);
}

export function listProjectVariables(projectId: string) {
  return apiClient.get<ProjectVariableListResponse>(`/api/v1/projects/${projectId}/variables`);
}

export function createProjectVariable(projectId: string, payload: ProjectVariableCreatePayload) {
  return apiClient.post<ProjectVariable>(`/api/v1/projects/${projectId}/variables`, payload);
}
