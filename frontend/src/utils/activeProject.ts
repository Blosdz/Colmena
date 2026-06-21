export const ACTIVE_PROJECT_KEY = "colmena.activeProjectId";

export function getActiveProjectId(): string | null {
  return localStorage.getItem(ACTIVE_PROJECT_KEY);
}

export function setActiveProjectId(projectId: string): void {
  localStorage.setItem(ACTIVE_PROJECT_KEY, projectId);
}

export function clearActiveProjectId(): void {
  localStorage.removeItem(ACTIVE_PROJECT_KEY);
}

export function resolveActiveProject(projects: Array<{ id: string }>): string | null {
  const activeId = getActiveProjectId();

  if (!projects || projects.length === 0) {
    clearActiveProjectId();
    return null;
  }

  // Si existe y está en la lista de proyectos, lo mantenemos
  const exists = projects.some((p) => p.id === activeId);
  if (activeId && exists) {
    return activeId;
  }

  // Si no existe o no está en la lista, limpiamos y seleccionamos el primero (más reciente asumiendo orden descendente)
  clearActiveProjectId();
  const mostRecentId = projects[0].id;
  setActiveProjectId(mostRecentId);
  return mostRecentId;
}
