import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getChartEditorState, upsertChartEditorState } from "../../../api/chartEditorStates";
import type { ChartSpec } from "../../../types/chart";
import type { ChartThemeName, EditableChartState, PersistedChartState } from "../../../types/chartEditor";
import { applyEditableStateToPlotlySpec, createInitialEditableChartState } from "./chartEditorUtils";
import {
  buildChartStorageKey,
  clearChartEditorState,
  loadChartEditorState,
  saveChartEditorState,
} from "./chartLocalStorage";

function toPersistedState(state: EditableChartState): PersistedChartState {
  const { rawSpec, ...persisted } = state;
  return persisted;
}

function useDebounce<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

export function useChartEditor(chart: ChartSpec, customStorageKey?: string) {
  const storageKey = useMemo(
    () => customStorageKey ?? buildChartStorageKey(chart.form_id, chart.chart_id),
    [chart.chart_id, chart.form_id, customStorageKey],
  );
  const baseState = useMemo(() => createInitialEditableChartState(chart), [chart]);
  const [state, setState] = useState<EditableChartState>(baseState);
  const hasLoaded = useRef(false);
  const debouncedState = useDebounce(state, 2000);

  // Load: try API first, fall back to localStorage
  useEffect(() => {
    let cancelled = false;
    const loadFromApi = async () => {
      try {
        const remote = await getChartEditorState(chart.form_id, chart.chart_id);
        if (cancelled) return;
        const remoteState = remote.graphs_json as Partial<PersistedChartState> | null;
        if (remoteState && Object.keys(remoteState).length > 0) {
          setState({ ...baseState, ...remoteState });
          // Keep localStorage in sync
          saveChartEditorState(storageKey, remoteState as PersistedChartState);
        } else {
          const stored = loadChartEditorState(storageKey);
          setState({ ...baseState, ...(stored ?? {}) });
        }
      } catch {
        if (cancelled) return;
        const stored = loadChartEditorState(storageKey);
        setState({ ...baseState, ...(stored ?? {}) });
      } finally {
        if (!cancelled) {
          hasLoaded.current = true;
        }
      }
    };
    void loadFromApi();
    return () => {
      cancelled = true;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chart.chart_id, chart.form_id, storageKey]);

  // Save to localStorage immediately on every state change
  useEffect(() => {
    if (!hasLoaded.current) return;
    saveChartEditorState(storageKey, toPersistedState(state));
  }, [state, storageKey]);

  // Save to API after debounce (fire-and-forget)
  useEffect(() => {
    if (!hasLoaded.current) return;
    const persisted = toPersistedState(debouncedState);
    void upsertChartEditorState(chart.form_id, chart.chart_id, {
      storage_key: storageKey,
      graphs_json: persisted as unknown as Record<string, unknown>,
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedState]);

  const derivedSpec = useMemo(() => applyEditableStateToPlotlySpec(chart, state), [chart, state]);

  const resetToRecommended = useCallback(() => {
    clearChartEditorState(storageKey);
    setState(baseState);
    void upsertChartEditorState(chart.form_id, chart.chart_id, {
      storage_key: storageKey,
      graphs_json: null,
    });
  }, [baseState, chart.chart_id, chart.form_id, storageKey]);

  return {
    state,
    storageKey,
    derivedSpec,
    updateField: <K extends keyof EditableChartState>(field: K, value: EditableChartState[K]) => {
      setState((current) => ({ ...current, [field]: value }));
    },
    applyPreset: (theme: ChartThemeName) => {
      setState((current) => ({
        ...current,
        theme,
        selectedPalette: theme,
      }));
    },
    resetToRecommended,
    clearLocalState: () => {
      clearChartEditorState(storageKey);
    },
  };
}
