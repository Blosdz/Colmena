export interface ApaTableColumn {
  key: string;
  label: string;
  align: "left" | "center" | "right";
  format_type?: string | null;
}

export interface ApaTableCell {
  value: string;
  raw_value?: unknown;
  align: "left" | "center" | "right";
  format_type?: string | null;
}

export interface ApaTableRow {
  cells: ApaTableCell[];
  row_type: "body" | "subtotal" | "total" | "note";
}

export interface ApaTableNote {
  note_type: "general" | "statistical" | "caution" | "source";
  text: string;
}

export interface ApaTable {
  table_id: string;
  table_number?: number | null;
  table_type: string;
  title: string;
  subtitle?: string | null;
  columns: ApaTableColumn[];
  rows: ApaTableRow[];
  notes: ApaTableNote[];
  markdown: string;
  html: string;
  ready_for_word: boolean;
  ready_for_frontend: boolean;
  warnings: string[];
  source: Record<string, unknown>;
}

export interface ApaTableBatch {
  form_id: string;
  project_id: string;
  total_tables: number;
  tables: ApaTable[];
  warnings: string[];
}
