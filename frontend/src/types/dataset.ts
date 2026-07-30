export interface DatasetColumn {
  name: string;
  label: string;
  question_id?: string | null;
  kind: string;
}

export interface DatasetPreview {
  form_id: string;
  mode: string;
  total_rows: number;
  total_columns: number;
  columns: DatasetColumn[];
  rows: Record<string, unknown>[];
}

export interface CompletenessItem {
  question_id: string;
  column_name: string;
  label: string;
  total_responses: number;
  answered_count: number;
  missing_count: number;
  missing_percent: number;
  required: boolean;
  warning_level: string;
}

export interface CompletenessSummary {
  form_id: string;
  total_responses: number;
  items: CompletenessItem[];
}

export interface DatasetExportArtifact {
  id: string;
  project_id: string;
  form_id?: string | null;
  artifact_type: string;
  file_name: string;
  file_path: string;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  metadata_json?: unknown;
  created_at: string;
}

export interface DatasetExportList {
  items: DatasetExportArtifact[];
  total: number;
}

export interface DataDictionaryOption {
  id: string;
  label: string;
  value?: string | null;
  score?: number | null;
  sort_order: number;
}

export interface DataDictionaryItem {
  question_id: string;
  column_name: string;
  code?: string | null;
  label: string;
  question_type: string;
  question_role: string;
  measurement_level: string;
  data_type: string;
  is_required: boolean;
  is_scored: boolean;
  is_reverse_scored: boolean;
  section_title?: string | null;
  instrument_name?: string | null;
  dimension_name?: string | null;
  project_variable_name?: string | null;
  options: DataDictionaryOption[];
}

export interface DataDictionary {
  form_id: string;
  items: DataDictionaryItem[];
}

// Edición de celda en la grilla de captura manual (upsert).
export interface AnswerUpsertPayload {
  raw_value?: string | null;
  clear?: boolean;
  option_id?: string | null;
  value_text?: string | null;
  value_number?: number | null;
  value_date?: string | null;
}

export interface AnswerUpsertResult {
  id: string;
  response_id: string;
  question_id: string;
  option_id?: string | null;
  value_text?: string | null;
  value_number?: number | null;
  value_date?: string | null;
  value_json?: unknown;
  score_value?: number | null;
  updated_at: string;
}
