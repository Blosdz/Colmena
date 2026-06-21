export interface ChartImage {
  artifact_id: string;
  form_id: string;
  project_id: string;
  chart_id?: string | null;
  chart_type?: string | null;
  title?: string | null;
  format: "png" | "svg" | string;
  file_name: string;
  file_path: string;
  mime_type: string;
  file_size_bytes: number;
  created_at: string;
  metadata_json?: Record<string, unknown> | null;
}

export interface ChartImageList {
  form_id: string;
  total: number;
  items: ChartImage[];
}

export interface ChartImageUploadResponse {
  status: string;
  image: ChartImage;
  message: string;
}
