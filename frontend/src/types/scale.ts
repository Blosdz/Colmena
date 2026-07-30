export interface ScaleOption {
  id: string;
  value: number;
  label: string;
  sort_order: number;
}

export interface Scale {
  id: string;
  project_id: string | null;
  name: string;
  scale_kind: string;   // frecuencia | intensidad | acuerdo | dificultad | satisfaccion | personalizada
  render_style: string; // radio | slider_line | stars | faces | nps
  points: number;
  options: ScaleOption[];
  created_at: string;
  updated_at: string;
}

export interface ScaleListResponse {
  items: Scale[];
  total: number;
}
