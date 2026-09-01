// ESPEJO MANUAL de schemas Pydantic reales — ver README.md en este directorio para el porqué
// y el plan de reemplazo por generación real desde OpenAPI.
//
// Fuente exacta de cada tipo (leída directamente del código fuente, no inferida):
//   backend/app/schemas/analytics.py
//   backend/app/schemas/variables.py
//   backend/app/schemas/constructs.py
//   backend/app/schemas/censopas.py
//
// Cobertura: solo los schemas relevantes para resultados/analítica (BaremResultsPanel,
// SpearmanPanel, comparaciones de grupo, normalidad, variables, constructos). No es la
// superficie completa de la API — no inventar tipos aquí para endpoints no auditados.

// ---------------------------------------------------------------------------
// backend/app/schemas/variables.py
// ---------------------------------------------------------------------------

export type VariableType =
  | "QUESTION"
  | "DERIVED"
  | "DEMOGRAPHIC"
  | "EXOGENOUS"
  | "CONSTRUCT_SCORE"
  | "SYSTEM";

export type DataType =
  | "INTEGER"
  | "DECIMAL"
  | "TEXT"
  | "BOOLEAN"
  | "DATE"
  | "DATETIME"
  | "CATEGORY";

export type MeasurementLevel = "NOMINAL" | "ORDINAL" | "SCALE" | "BINARY" | "TEXT";

export type VariableRole =
  | "INDEPENDENT"
  | "DEPENDENT"
  | "CONTROL"
  | "EXOGENOUS"
  | "DESCRIPTIVE"
  | "OUTCOME"
  | "NONE";

/** backend/app/schemas/variables.py::VariableRead */
export interface VariableRead {
  id: number;
  public_id: string; // uuid
  project_id: number;
  study_id: number | null;
  instrument_version_id: number | null;
  question_id: number | null;
  construct_id: number | null;
  code: string;
  name: string;
  label: string | null;
  variable_type: string;
  data_type: string;
  measurement_level: string;
  role: string;
  // NOTA: is_editable/formula/metadata/created_at/updated_at no confirmados en la lectura
  // parcial de este schema — revisar backend/app/schemas/variables.py:54-77 antes de asumir.
}

// ---------------------------------------------------------------------------
// backend/app/schemas/constructs.py
// ---------------------------------------------------------------------------

export type ConstructType = "VARIABLE" | "DIMENSION" | "SUBDIMENSION" | "SCALE" | "FACTOR" | "INDEX";
export type ItemRole = "SCORED" | "CONTEXT" | "EXCLUDED";
export type ScoringDirection = "DIRECT" | "REVERSE";

/** backend/app/schemas/constructs.py::ConstructRead */
export interface ConstructRead {
  id: number;
  public_id: string;
  instrument_version_id: number;
  parent_id: number | null;
  code: string;
  name: string;
  construct_type: string;
  description: string | null;
  sort_order: number | null;
  metadata: Record<string, unknown>;
  created_at: string; // ISO datetime
  updated_at: string;
}

// ---------------------------------------------------------------------------
// backend/app/schemas/analytics.py
// ---------------------------------------------------------------------------

/** analytics.py::NormalityResultRead */
export interface NormalityResultRead {
  construct_id: number;
  construct_code: string;
  construct_name: string;
  n: number;
  test: string | null;
  statistic: number | null;
  p_value: number | null;
  status: string;
  mean: number | null;
  median: number | null;
  standard_deviation: number | null;
  minimum: number | null;
  maximum: number | null;
  histogram: HistogramBin[];
  warnings: string[];
}

export interface HistogramBin {
  min_value: number;
  max_value: number;
  n: number;
}

export interface NormalityResponse {
  analysis_run_id: number;
  study_id: number;
  note: string;
  results: NormalityResultRead[];
}

/** analytics.py::SpearmanVariableRead */
export interface SpearmanVariableRead {
  key: string;
  source_type: string;
  source_id: number;
  code: string;
  label: string;
  measurement_level: string;
}

/**
 * analytics.py::SpearmanPointBin — celda agregada de una grilla x/y (E-09).
 * NUNCA coordenadas individuales — ver GAP-009 en docs/frontend/ANALYTICS_GAPS.md.
 * El diseño privacy-safe con bins es intencional, no un hueco a llenar con pares crudos.
 */
export interface SpearmanPointBin {
  x_bin_center: number;
  y_bin_center: number;
  n: number;
}

/** analytics.py::SpearmanCellRead */
export interface SpearmanCellRead {
  x_key: string;
  y_key: string;
  rho: number | null;
  p_value: number | null;
  adjusted_p_value: number | null;
  n: number;
  magnitude: string | null;
  significant: boolean;
  /** Ausente/vacío salvo que la request tenga include_points=true (opt-in, rol elevado) */
  points_binned: SpearmanPointBin[];
  warnings: string[];
}

export interface SpearmanMatrixResponse {
  analysis_run_id: number;
  study_id: number;
  method: string;
  correction: string;
  normality_required: boolean;
  variables: SpearmanVariableRead[];
  cells: SpearmanCellRead[];
  excluded: string[];
}

/** analytics.py::GroupSummaryRead */
export interface GroupSummaryRead {
  code: string;
  n: number;
  suppressed: boolean;
  mean: number | null;
  median: number | null;
}

/** analytics.py::ConstructCompareGroupsResponse */
export interface ConstructCompareGroupsResponse {
  analysis_run_id: number;
  study_id: number;
  construct_id: number;
  group_variable_id: number;
  method: string | null;
  statistic: number | null;
  p_value: number | null;
  effect_size: number | null;
  effect_label: string | null;
  suppressed: boolean;
  groups: GroupSummaryRead[];
  warnings: string[];
  // NOTA: sin confidence_interval — confirmado ausente en el backend real (GAP-011).
  // No añadir este campo aquí hasta que el backend lo calcule.
}

/** analytics.py::AnalysisResultRead */
export interface AnalysisResultRead {
  id: number;
  result_code: string | null;
  result_type: string;
  question_id: number | null;
  construct_id: number | null;
  n_valid: number | null;
  numeric_value: number | null;
  statistic_value: number | null;
  p_value: number | null;
  adjusted_p_value: number | null;
  effect_size: number | null;
  effect_label: string | null;
  result_data: Record<string, unknown>;
}

/** analytics.py::AnalysisRunRead */
export interface AnalysisRunRead {
  id: number;
  public_id: string;
  study_id: number;
  analysis_type: string;
  engine: string;
  parameters: Record<string, unknown>;
  status: string; // PENDING | RUNNING | COMPLETED | FAILED (confirmar valores exactos en el enum real)
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
  results: AnalysisResultRead[];
}

// ---------------------------------------------------------------------------
// backend/app/schemas/censopas.py (reutilizado también por baremos académicos —
// BaremCutoffCreate/Read no son específicos de CENSOPAS, ver COLMENA_QA_DATASET_TESIS_DOS_VARIABLES.md §4)
// ---------------------------------------------------------------------------

export type Direction = "HIGHER_BETTER" | "LOWER_BETTER";

/** censopas.py::BaremRead */
export interface BaremRead {
  id: number;
  public_id: string;
  instrument_version_id: number;
  name: string;
  population_label: string | null;
  source_reference: string | null;
  status: string; // DRAFT | ... (revisar valores completos en app/models antes de fijar union)
  barem_version: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

/** censopas.py::BaremBandRead */
export interface BaremBandRead {
  id: number;
  barem_id: number;
  construct_id: number;
  code: string;
  label: string;
  min_value: number; // 0-100
  max_value: number; // 0-100
  severity_order: number;
  interpretation: string | null;
  color_hint: string | null;
  classification_code: string | null;
  metadata: Record<string, unknown>;
}

/** censopas.py::BaremDetailRead */
export interface BaremDetailRead extends BaremRead {
  bands: BaremBandRead[];
}

/** censopas.py::BaremCutoffRead */
export interface BaremCutoffRead {
  id: number;
  barem_id: number;
  construct_id: number;
  cut_1: number;
  cut_2: number;
  direction: string | null;
  favorable_label: string;
  intermediate_label: string;
  unfavorable_label: string;
}

/**
 * censopas.py::ConstructResultRead — resultado por constructo con supresión de
 * privacidad ya aplicada (n<5 → suppressed=true, campos numéricos en null).
 * NUNCA renderizar favorable_n/pct etc. sin comprobar `suppressed` primero.
 */
export interface ConstructResultRead {
  construct_id: number;
  construct_code: string;
  construct_name: string;
  n_valid: number;
  suppressed: boolean;
  favorable_n: number | null;
  intermediate_n: number | null;
  unfavorable_n: number | null;
  favorable_pct: number | null;
  intermediate_pct: number | null;
  unfavorable_pct: number | null;
  construct_score: number | null;
  classification_status: string; // PROVISIONAL | OFFICIAL | ... (confirmar enum completo)
}

export interface CensopasResultsResponse {
  study_id: number;
  scoring_status: string;
  official_equivalence_enabled: boolean;
  results: ConstructResultRead[];
}
