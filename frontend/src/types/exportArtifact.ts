export interface ExportArtifactLike {
  id?: string;
  artifact_id?: string;
  artifact_type?: string;
  file_name: string;
  file_path: string;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  created_at: string;
}
