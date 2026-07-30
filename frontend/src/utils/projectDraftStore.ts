import { useState, useCallback, useEffect } from "react";
import type { ParsedQuestion } from "./bulkQuestionParser";
import type { BaremoLevel } from "./baremoCalculator";
export type { BaremoLevel };
import { calculateEqualRangeBaremos } from "./baremoCalculator";
import type { CatalogScale } from "../components/forms/BulkQuestionTable";

// ── Types ──────────────────────────────────────────────

export type ScaleDraft = {
  name: string;
  options: { id: string; value: number; label: string }[];
  /** id real en `scales` del backend si coincide con un preset del catálogo; null/undefined = personalizada/editada */
  catalogScaleId?: string | null;
};

export type DimensionDraft = {
  id: string;
  name: string;
  description: string;
  itemCodes: string[];       // which item codes belong to this dimension
  baremos: BaremoLevel[];    // dimension-level baremos
};

// ── Study-variable metadata (maps to backend project_variables) ──
export type VariableRole = "main" | "intervening";
// Clasificación metodológica opcional, aplicable a cualquier rol.
export type VariableClassification = "independent" | "dependent" | "segment" | null;
export type MeasurementLevel = "nominal" | "ordinal" | "interval" | "ratio";
export type VariableDataType = "numeric" | "categorical" | "text" | "boolean" | "date";
// Cómo se mide la variable: con un cuestionario (ítems que se suman) o un dato directo (un solo valor).
export type MeasurementMode = "instrument" | "direct";

export type VariableDraft = {
  id: string;
  name: string;
  code: string;                     // short code, e.g. AUTOEST
  description: string;
  variableRole: VariableRole;       // → variable_role
  variableClassification: VariableClassification; // → variable_classification
  measurementMode: MeasurementMode; // → measurement_mode (lo elige el usuario)
  measurementLevel: MeasurementLevel; // → measurement_level (DERIVADO, no lo elige el usuario)
  dataType: VariableDataType;       // → data_type (solo relevante en modo "direct")
  isRequiredForAnalysis: boolean;   // → is_required_for_analysis
  dimensions: DimensionDraft[];
  items: ParsedQuestion[];
  scale: ScaleDraft;
  baremos: BaremoLevel[];           // variable-level baremos
};

export type VariableMeta = Pick<
  VariableDraft,
  "name" | "code" | "description" | "variableRole" | "variableClassification" | "measurementMode" | "measurementLevel" | "dataType" | "isRequiredForAnalysis"
>;

/**
 * Deriva el nivel de medición: el usuario nunca lo elige, el sistema lo deduce.
 * Debe reflejar exactamente `derive_measurement_level` del backend.
 */
export function deriveMeasurementLevel(mode: MeasurementMode, dataType: VariableDataType): MeasurementLevel {
  if (mode === "instrument") return "ordinal";
  if (dataType === "numeric") return "ratio";
  if (dataType === "date") return "interval";
  return "nominal"; // categorical, boolean, text
}

export type DataRow = Record<string, string | number>;

export type ProjectDraft = {
  title: string;
  author: string;
  description: string;
  variables: VariableDraft[];
  participantFields: string[];       // preset ids de "Datos del participante" (nombre, sexo, edad…)
  dataRows: DataRow[];               // uploaded Excel data
  dataColumns: string[];             // column headers from Excel
};

// ── Defaults ───────────────────────────────────────────

/**
 * Crea una variable nueva. La escala inicial viene del catálogo del backend, nunca hardcodeada:
 * si se pasa `defaultScale` (resuelto por `resolveDefaultCatalogScale` con datos de `useScales`),
 * la variable arranca ya con esa escala; si no, arranca sin opciones y el wizard la backfillea en
 * cuanto el catálogo termine de cargar (ver el `useEffect` de backfill en ProjectCreateWizard.tsx).
 */
export function createVariable(name: string, defaultScale?: CatalogScale): VariableDraft {
  return {
    id: crypto.randomUUID(),
    name,
    code: "",
    description: "",
    variableRole: "main",
    variableClassification: "independent",
    measurementMode: "instrument",
    measurementLevel: "ordinal",
    dataType: "numeric",
    isRequiredForAnalysis: true,
    dimensions: [],
    items: [],
    scale: defaultScale
      ? {
          name: defaultScale.name,
          options: defaultScale.options.map((o, i) => ({ id: String(i + 1), value: o.value, label: o.label })),
          catalogScaleId: defaultScale.id,
        }
      : { name: "", options: [] },
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
    variables: [createVariable("Variable 1")],
    participantFields: [],
    dataRows: [],
    dataColumns: [],
  };
}

let globalDraft: ProjectDraft = createDefaultDraft();
let globalActiveVariableId = globalDraft.variables[0].id;
let globalActiveTab: VariableTab = "variable";
let globalShowProjectInfo = false;

const listeners = new Set<() => void>();

function notify() {
  listeners.forEach(l => l());
}

function reset() {
  globalDraft = createDefaultDraft();
  globalActiveVariableId = globalDraft.variables[0].id;
  globalActiveTab = "variable";
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

export type VariableTab = "variable" | "dimensions" | "items" | "scale" | "baremos" | "data" | "participants";

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

  const addVariable = useCallback((defaultScale?: CatalogScale) => {
    const v = createVariable(`Variable ${globalDraft.variables.length + 1}`, defaultScale);
    globalDraft = { ...globalDraft, variables: [...globalDraft.variables, v] };
    globalActiveVariableId = v.id;
    globalActiveTab = "variable";
    notify();
  }, []);

  const removeVariable = useCallback((id: string) => {
    const next = globalDraft.variables.filter(v => v.id !== id);
    if (next.length === 0) {
      const fallback = createVariable("Variable 1");
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

  const updateVariableMeta = useCallback((id: string, updates: Partial<VariableMeta>) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v => {
        if (v.id !== id) return v;
        const merged = { ...v, ...updates };
        // El nivel de medición siempre se deriva; nunca lo fija el usuario directamente.
        merged.measurementLevel = deriveMeasurementLevel(merged.measurementMode, merged.dataType);
        return merged;
      }),
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

  const removeItem = useCallback((varId: string, itemId: string) => {
    globalDraft = {
      ...globalDraft,
      variables: globalDraft.variables.map(v =>
        v.id === varId ? { ...v, items: v.items.filter(i => i.id !== itemId) } : v
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

  const toggleParticipantField = useCallback((presetId: string) => {
    const current = globalDraft.participantFields;
    globalDraft = {
      ...globalDraft,
      participantFields: current.includes(presetId)
        ? current.filter(id => id !== presetId)
        : [...current, presetId],
    };
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
    updateVariableMeta,
    addDimension,
    removeDimension,
    updateDimension,
    addItems,
    updateItem,
    removeItem,
    updateScale,
    updateBaremos,
    updateDimensionBaremos,
    autoGenerateAllBaremos,
    setData,
    toggleParticipantField,
    reset,
    hydrate,
    totalDimensions: globalDraft.variables.reduce((sum, v) => sum + v.dimensions.length, 0),
    totalItems: globalDraft.variables.reduce((sum, v) => sum + v.items.length, 0),
  };
}
