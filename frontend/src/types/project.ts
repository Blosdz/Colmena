export interface Project {
  id: string;
  title: string;
  subtitle?: string | null;
  research_type?: string | null;
  design_type?: string | null;
  approach?: string | null;
  institution?: string | null;
  faculty?: string | null;
  career?: string | null;
  advisor_name?: string | null;
  population_description?: string | null;
  sample_size_planned?: number | null;
  sample_size_current?: number | null;
  status: string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

export interface ProjectCreatePayload {
  title: string;
  research_type?: string;
  design_type?: string;
  approach?: string;
  institution?: string;
  faculty?: string;
  career?: string;
  advisor_name?: string;
  notes?: string;
  sample_size_planned?: number | null;
}

export interface ProjectVariable {
  id: string;
  project_id: string;
  name: string;
  code?: string | null;
  description?: string | null;
  variable_role: string;
  measurement_level: string;
  data_type: string;
  is_required_for_analysis: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectVariableCreatePayload {
  name: string;
  code?: string | null;
  description?: string | null;
  variable_role: string;
  measurement_level: string;
  data_type: string;
  is_required_for_analysis?: boolean;
  notes?: string | null;
}

export interface ProjectVariableListResponse {
  items: ProjectVariable[];
  total: number;
}
