export const ACTIVE_PROJECT_KEY = 'colmena.activeProjectId';

export function getActiveProjectId() {
  return localStorage.getItem(ACTIVE_PROJECT_KEY);
}

export function setActiveProjectId(projectId) {
  localStorage.setItem(ACTIVE_PROJECT_KEY, projectId);
}

export function clearActiveProjectId() {
  localStorage.removeItem(ACTIVE_PROJECT_KEY);
}

export function resolveActiveProject(projects) {
  const activeId = getActiveProjectId();

  if (!projects || projects.length === 0) {
    clearActiveProjectId();
    return null;
  }

  const exists = projects.some((p) => String(p.id) === String(activeId));
  if (activeId && exists) {
    return activeId;
  }

  clearActiveProjectId();
  const mostRecentId = projects[0].id;
  setActiveProjectId(mostRecentId);
  return mostRecentId;
}
