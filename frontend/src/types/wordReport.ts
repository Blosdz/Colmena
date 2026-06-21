export interface WordReportSection {
  section_key: string;
  title: string;
  included: boolean;
  summary: string;
  warnings: string[];
}

export interface WordReport {
  artifact_id: string;
  form_id: string;
  project_id: string;
  report_type: string;
  file_name: string;
  file_path: string;
  mime_type: string;
  file_size_bytes: number;
  sections: WordReportSection[];
  table_count: number;
  chart_image_count: number;
  chart_placeholder_count: number;
  chart_image_artifact_ids: string[];
  analysis_run_count: number;
  warnings: string[];
  created_at: string;
}

export interface WordReportGeneratePayload {
  report_type: string;
  source_type: string;
  analysis_run_ids: string[];
  orchestrated_analysis_run_id: string | null;
  title: string;
  subtitle: string;
  decimals: number;
  include_discarded: boolean;
  score_aggregation: string;
  include_charts_placeholders: boolean;
  include_chart_images: boolean;
  chart_image_mode: "placeholders_only" | "images_if_available" | "selected_images_only";
  chart_image_artifact_ids: string[];
  include_plain_language_explanations: boolean;
  include_technical_appendix: boolean;
  include_cover: boolean;
  include_methodology_summary: boolean;
  options: Record<string, unknown>;
}

export interface WordReportOptions {
  form_id: string;
  available_report_types: string[];
  available_analysis_runs: Array<{
    id: string;
    analysis_type: string;
    created_at: string;
  }>;
  available_orchestrated_runs: Array<{
    id: string;
    analysis_goal: string;
    created_at: string;
  }>;
  recommended_report: string;
  available_sections: string[];
}
