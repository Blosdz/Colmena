import { useEffect } from "react";

const STORAGE_KEY = "colmena.activeProjectId";
const LEGACY_STORAGE_KEY = "colmena.activeStudyId";

export function extractStudyProjectId(pathname: string) {
  const match = pathname.match(/^\/(?:project|study)\/([^/]+)/);
  return match?.[1] ?? null;
}

export function getStoredActiveStudyId() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(STORAGE_KEY) || window.localStorage.getItem(LEGACY_STORAGE_KEY);
}

export function storeActiveStudyId(projectId: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, projectId);
  window.localStorage.setItem(LEGACY_STORAGE_KEY, projectId);
}

export function useActiveStudy(projectId?: string | null) {
  useEffect(() => {
    if (projectId) {
      storeActiveStudyId(projectId);
    }
  }, [projectId]);
}
