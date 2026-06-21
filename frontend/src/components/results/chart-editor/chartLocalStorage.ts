import type { PersistedChartState } from "../../../types/chartEditor";

const storagePrefix = "colmena.chartEditor";

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function buildChartStorageKey(formId: string, chartId: string) {
  return `${storagePrefix}.${formId}.${chartId}`;
}

export function loadChartEditorState(storageKey: string) {
  if (!canUseStorage()) {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as Partial<PersistedChartState>;
  } catch {
    return null;
  }
}

export function saveChartEditorState(storageKey: string, state: PersistedChartState) {
  if (!canUseStorage()) {
    return;
  }

  try {
    window.localStorage.setItem(storageKey, JSON.stringify(state));
  } catch {
    // ignore storage quota and serialization errors in MVP
  }
}

export function clearChartEditorState(storageKey: string) {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.removeItem(storageKey);
}
