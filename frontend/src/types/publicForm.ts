export interface PublicFormSectionRead {
  id: string;
  title: string;
  description?: string | null;
  sort_order: number;
}

export interface PublicFormDimensionRead {
  id: string;
  name: string;
  code?: string | null;
  sort_order: number;
}

export interface PublicFormInstrumentRead {
  id: string;
  name: string;
  acronym?: string | null;
  dimensions: PublicFormDimensionRead[];
}

export interface PublicFormOptionRead {
  id: string;
  label: string;
  value: string;
  sort_order: number;
}

export interface PublicFormQuestionRead {
  id: string;
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
  options: PublicFormOptionRead[];
}

export interface PublicFormRead {
  id: string;
  project_id: string;
  title: string;
  description?: string | null;
  instructions?: string | null;
  status: string;
  sections: PublicFormSectionRead[];
  instruments: PublicFormInstrumentRead[];
  questions: PublicFormQuestionRead[];
  thank_you_message?: string | null;
  metadata_json?: string | null;
}

export interface PublicAnswerCreate {
  question_id: string;
  option_id?: string | null;
  value_text?: string | null;
  value_number?: number | null;
  value_date?: string | null;
  value_json?: any;
}

export interface PublicFormResponseCreate {
  respondent_code?: string | null;
  answers: PublicAnswerCreate[];
  metadata_json?: any;
}

export interface PublicFormResponseRead {
  status: string;
  response_id: string;
  form_id: string;
  submitted_at: string;
}
