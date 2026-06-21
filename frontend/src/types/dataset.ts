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
