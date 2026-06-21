import { useState, useCallback, useEffect } from "react";
import type { ParsedQuestion } from "./bulkQuestionParser";
import type { BaremoLevel } from "./baremoCalculator";
export type { BaremoLevel };
import { calculateEqualRangeBaremos } from "./baremoCalculator";

// ── Types ──────────────────────────────────────────────

export type ScaleDraft = {
  name: string;
  options: { id: string; value: number; label: string }[];
};

export type DimensionDraft = {
  id: string;
  name: string;
  description: string;
  itemCodes: string[];       // which item codes belong to this dimension
  baremos: BaremoLevel[];    // dimension-level baremos
};

export type VariableDraft = {
  id: string;
  name: string;
  dimensions: DimensionDraft[];
  items: ParsedQuestion[];
  scale: ScaleDraft;
  baremos: BaremoLevel[];           // variable-level baremos
};

export type DataRow = Record<string, string | number>;

export type ProjectDraft = {
  title: string;
  author: string;
  description: string;
  variables: VariableDraft[];
  dataRows: DataRow[];               // uploaded Excel data
  dataColumns: string[];             // column headers from Excel
};

// ── Defaults ───────────────────────────────────────────

const DEFAULT_SCALE: ScaleDraft = {
  name: "Likert 5 puntos",
  options: [
    { id: "1", value: 1, label: "Totalmente en desacuerdo" },
    { id: "2", value: 2, label: "En desacuerdo" },
    { id: "3", value: 3, label: "Ni de acuerdo ni en desacuerdo" },
    { id: "4", value: 4, label: "De acuerdo" },
    { id: "5", value: 5, label: "Totalmente de acuerdo" },
  ],
};

export function createVariable(name: string): VariableDraft {
  return {
    id: crypto.randomUUID(),
    name,
    dimensions: [],
    items: [],
    scale: { ...DEFAULT_SCALE, options: DEFAULT_SCALE.options.map(o => ({ ...o })) },
    baremos: [],
  };
}

export function createDimension(name: string): DimensionDraft {
  return { id: crypto.randomUUID(), name, description: "", itemCodes: [], baremos: [] };
}

// ── Auto-baremo calculation ────────────────────────────

function autoCalculateBaremos(numItems: number, scaleMin: number, scaleMax: number, levels: number = 3): BaremoLevel[] {
  if (numItems <= 0) return [];
  const totalMin = numItems * scaleMin;
  const totalMax = numItems * scaleMax;
  return calculateEqualRangeBaremos(totalMin, totalMax, levels);
}

// ── Global Store State ─────────────────────────────────

function createDefaultDraft(): ProjectDraft {
  return {
    title: "",
    author: "",
    description: "",
    variables: [createVariable("Variable principal")],
    dataRows: [],
    dataColumns: [],
  };
}

let globalDraft: ProjectDraft = createDefaultDraft();
let globalActiveVariableId = globalDraft.variables[0].id;
let globalActiveTab: VariableTab = "dimensions";
let globalShowProjectInfo = false;

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach(l => l());
}

function reset() {
  globalDraft = createDefaultDraft();
  globalActiveVariableId = globalDraft.variables[0].id;
  globalActiveTab = "dimensions";
  globalShowProjectInfo = false;
  notify();
}

function hydrate(draftData: ProjectDraft) {
  globalDraft = draftData;
  if (draftData.variables.length > 0) {
    globalActiveVariableId = draftData.variables[0].id;
  }
  notify();
}

// ── Hook ───────────────────────────────────────────────

export type VariableTab = "dimensions" | "items" | "scale" | "baremos" | "data";

export function useProjectDraft() {
  const [, setTick] = useState(0);
  const forceUpdate = useCallback(() => setTick(t => t + 1), []);

  useEffect(() => {
    listeners.add(forceUpdate);
    return () => {
      listeners.delete(forceUpdate);
    };
  }, [forceUpdate]);

  const activeVariable = globalDraft.variables.find(v => v.id === globalActiveVariableId) ?? globalDraft.variables[0];

  const updateProject = useCallback((updates: Partial<Pick<ProjectDraft, "title" | "author" | "description">>) => {
    globalDraft = { ...globalDraft, ...updates };
    notify();
  }, []);

  const addVariable = useCallback(() => {
    const v = createVariable(`Variable ${globalDraft.variables.length + 1}`);
    globalDraft = { ...globalDraft, variables: [...globalDraft.variables, v] };
    globalActiveVariableId = v.id;
    globalActiveTab = "dimensions";
    notify();
  }, []);

  const removeVariable = useCallback((id: string) => {
    const next = globalDraft.variables.filter(v => v.id !== id);
    if (next.length === 0) {
      const fallback = createVariable("Variable principal");
      globalDraft = { ...globalDraft, variables: [fallback] };
    } else {
      globalDraft = { ...globalDraft, variables: next };
    }
    const remaining = globalDraft.variables.filter(v => v.id !== id);
    if (remaining.length > 0) {
      globalActiveVariableId = remaining[0].id;
    } else {
      globalActiveVariableId = globalDraft.variables[0].id;
    }
    notify();
  }, []);

  const renameVariable = useCallback((id: string, name: string) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v => v.id === id ? { ...v, name } : v),
    };
    notify();
  }, []);

  const addDimension = useCallback((varId: string, name: string) => {
    const dim = createDimension(name);
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v =>
        v.id === varId ? { ...v, dimensions: [...v.dimensions, dim] } : v
      ),
    };
    notify();
  }, []);

  const removeDimension = useCallback((varId: string, dimId: string) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v =>
        v.id === varId ? { ...v, dimensions: v.dimensions.filter(d => d.id !== dimId) } : v
      ),
    };
    notify();
  }, []);

  const updateDimension = useCallback((varId: string, dimId: string, updates: Partial<DimensionDraft>) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v =>
        v.id === varId
          ? { ...v, dimensions: v.dimensions.map(d => d.id === dimId ? { ...d, ...updates } : d) }
          : v
      ),
    };
    notify();
  }, []);

  const addItems = useCallback((varId: string, newItems: ParsedQuestion[]) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v =>
        v.id === varId ? { ...v, items: [...v.items, ...newItems] } : v
      ),
    };
    notify();
  }, []);

  const updateItem = useCallback((varId: string, itemId: string, updates: Partial<ParsedQuestion>) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v =>
        v.id === varId
          ? { ...v, items: v.items.map(i => i.id === itemId ? { ...i, ...updates } : i) }
          : v
      ),
    };
    notify();
  }, []);

  const updateScale = useCallback((varId: string, scale: ScaleDraft) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v => v.id === varId ? { ...v, scale } : v),
    };
    notify();
  }, []);

  const updateBaremos = useCallback((varId: string, baremos: BaremoLevel[]) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v => v.id === varId ? { ...v, baremos } : v),
    };
    notify();
  }, []);

  const updateDimensionBaremos = useCallback((varId: string, dimId: string, baremos: BaremoLevel[]) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v =>
        v.id === varId
          ? { ...v, dimensions: v.dimensions.map(d => d.id === dimId ? { ...d, baremos } : d) }
          : v
      ),
    };
    notify();
  }, []);

  const autoGenerateAllBaremos = useCallback((varId: string, levels: number = 3) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v => {
        if (v.id !== varId) return v;
        const scaleMin = Math.min(...v.scale.options.map(o => o.value));
        const scaleMax = Math.max(...v.scale.options.map(o => o.value));
        const varBaremos = autoCalculateBaremos(v.items.length, scaleMin, scaleMax, levels);
        const updatedDims = v.dimensions.map(dim => {
          const dimItemCount = v.items.filter(i => i.dimensionName === dim.name).length || dim.itemCodes.length;
          const dimBaremos = autoCalculateBaremos(dimItemCount > 0 ? dimItemCount : 1, scaleMin, scaleMax, levels);
          return { ...dim, baremos: dimBaremos };
        });
        return { ...v, baremos: varBaremos, dimensions: updatedDims };
      }),
    };
    notify();
  }, []);

  const setData = useCallback((columns: string[], rows: DataRow[]) => {
    globalDraft = { ...globalDraft, dataColumns: columns, dataRows: rows };
    notify();
  }, []);

  return {
    draft: globalDraft,
    activeVariable,
    activeVariableId: globalActiveVariableId,
    activeTab: globalActiveTab,
    showProjectInfo: globalShowProjectInfo,
    setActiveVariableId: (id: string) => {
      globalActiveVariableId = id;
      notify();
    },
    setActiveTab: (tab: VariableTab) => {
      globalActiveTab = tab;
      notify();
    },
    setShowProjectInfo: (show: boolean) => {
      globalShowProjectInfo = show;
      notify();
    },
    updateProject,
    addVariable,
    removeVariable,
    renameVariable,
    addDimension,
    removeDimension,
    updateDimension,
    addItems,
    updateItem,
    updateScale,
    updateBaremos,
    updateDimensionBaremos,
    autoGenerateAllBaremos,
    setData,
    reset,
    hydrate,
    totalDimensions: globalDraft.variables.reduce((sum, v) => sum + v.dimensions.length, 0),
    totalItems: globalDraft.variables.reduce((sum, v) => sum + v.items.length, 0),
  };
}
