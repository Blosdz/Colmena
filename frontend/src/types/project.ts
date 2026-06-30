export interface CatalogRef {
  id: string;
  name: string;
}

export interface ProjectDemographics {
  id: string;
  project_id: string;
  population_description?: string | null;
  sample_size_planned?: number | null;
  sample_size_current: number;
  sampling_method?: string | null;
  inclusion_criteria?: string | null;
  exclusion_criteria?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectDemographicsInput {
  population_description?: string | null;
  sample_size_planned?: number | null;
  sample_size_current?: number | null;
  sampling_method?: string | null;
  inclusion_criteria?: string | null;
  exclusion_criteria?: string | null;
}

export interface Project {
  id: string;
  user_id: string;
  title: string;
  subtitle?: string | null;
  type_research_id?: string | null;
  design_type_id?: string | null;
  approach_id?: string | null;
  type_research?: CatalogRef | null;
  design_type?: CatalogRef | null;
  approach?: CatalogRef | null;
  institution?: string | null;
  faculty?: string | null;
  career?: string | null;
  advisor_name?: string | null;
  status: string;
  notes?: string | null;
  demographics?: ProjectDemographics | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

export interface ProjectCreatePayload {
  title: string;
  subtitle?: string;
  type_research_id?: string | null;
  design_type_id?: string | null;
  approach_id?: string | null;
  institution?: string;
  faculty?: string;
  career?: string;
  advisor_name?: string;
  notes?: string;
  demographics?: ProjectDemographicsInput;
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
