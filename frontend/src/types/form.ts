export interface Form {
  id: string;
  project_id: string;
  title: string;
  description?: string | null;
  instructions?: string | null;
  status: string;
  public_slug?: string | null;
  allow_anonymous: boolean;
  collect_started_at?: string | null;
  collect_closed_at?: string | null;
  thank_you_message?: string | null;
  metadata_json?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FormListResponse {
  items: Form[];
  total: number;
}

export interface FormSection {
  id: string;
  form_id: string;
  title: string;
  description?: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface FormSectionPayload {
  title: string;
  description?: string | null;
  sort_order?: number;
}

export interface FormInstrument {
  id: string;
  form_id: string;
  project_variable_id?: string | null;
  name: string;
  acronym?: string | null;
  author?: string | null;
  year?: number | null;
  description?: string | null;
  response_scale_name?: string | null;
  scoring_method?: string | null;
  reverse_scoring_enabled: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface FormInstrumentPayload {
  name: string;
  project_variable_id?: string | null;
  acronym?: string | null;
  author?: string | null;
  year?: number | null;
  description?: string | null;
  response_scale_name?: string | null;
  scoring_method?: string | null;
  reverse_scoring_enabled?: boolean;
  sort_order?: number;
}

export interface FormDimension {
  id: string;
  instrument_id: string;
  name: string;
  code?: string | null;
  description?: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface FormDimensionPayload {
  name: string;
  code?: string | null;
  description?: string | null;
  sort_order?: number;
}

export interface FormQuestion {
  id: string;
  form_id: string;
  section_id?: string | null;
  instrument_id?: string | null;
  dimension_id?: string | null;
  project_variable_id?: string | null;
  code?: string | null;
  label: string;
  help_text?: string | null;
  question_type: string;
  question_role: string;
  measurement_level: string;
  data_type: string;
  is_required: boolean;
  is_scored: boolean;
  is_reverse_scored: boolean;
  min_value?: number | null;
  max_value?: number | null;
  sort_order: number;
  validation_json?: unknown;
  config_json?: unknown;
  created_at: string;
  updated_at: string;
}

export interface FormQuestionPayload {
  label: string;
  section_id?: string | null;
  instrument_id?: string | null;
  dimension_id?: string | null;
  project_variable_id?: string | null;
  code?: string | null;
  help_text?: string | null;
  question_type: string;
  question_role?: string;
  measurement_level?: string;
  data_type?: string;
  is_required?: boolean;
  is_scored?: boolean;
  is_reverse_scored?: boolean;
  min_value?: number | null;
  max_value?: number | null;
  sort_order?: number;
  validation_json?: unknown;
  config_json?: unknown;
}

export interface FormQuestionOption {
  id: string;
  question_id: string;
  label: string;
  value: string;
  score?: number | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface FormQuestionOptionPayload {
  label: string;
  value: string;
  score?: number | null;
  sort_order?: number;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
}

export interface PublicFormLink {
  form_id: string;
  public_slug: string;
  public_url: string;
  status: string;
}

export interface ResponseAnswer {
  id: string;
  response_id: string;
  question_id: string;
  option_id?: string | null;
  value_text?: string | null;
  value_number?: number | null;
  value_date?: string | null;
  value_json?: unknown;
  score_value?: number | null;
  created_at: string;
  updated_at: string;
}

export interface FormResponse {
  id: string;
  project_id: string;
  form_id: string;
  respondent_code?: string | null;
  status: string;
  submitted_at?: string | null;
  source: string;
  metadata_json?: unknown;
  created_at: string;
  updated_at: string;
  answers: ResponseAnswer[];
}

export interface FormResponseList {
  items: FormResponse[];
  total: number;
}
