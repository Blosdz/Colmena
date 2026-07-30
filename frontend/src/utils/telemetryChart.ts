import type { FrequencyRow, QuestionDescriptive } from "../types/analysis";
import { COLMENA_PALETTE } from "../components/telemetry/chartSetup";

export type TelemetryChartType = "doughnut" | "bar" | "horizontalBar" | "numeric";

/** Devuelve `count` colores estables ciclando la paleta de Colmena. */
export function palette(count: number): string[] {
  return Array.from({ length: count }, (_, i) => COLMENA_PALETTE[i % COLMENA_PALETTE.length]);
}

/** Etiqueta legible para una fila de frecuencia. */
function rowLabel(row: FrequencyRow): string {
  const label = row.label ?? row.value;
  return label != null && String(label).trim() !== "" ? String(label) : "Sin dato";
}

export interface ChartDatum {
  labels: string[];
  values: number[];
  /** Texto por barra/segmento (p. ej. "12 (34%)") para tooltips/labels. */
  captions: string[];
}

/** Convierte las frecuencias de una pregunta en labels/values listos para Chart.js. */
export function frequenciesToChartData(
  frequencies: FrequencyRow[],
  options: { showPercent?: boolean } = {},
): ChartDatum {
  const { showPercent = true } = options;
  const labels: string[] = [];
  const values: number[] = [];
  const captions: string[] = [];

  for (const row of frequencies) {
    labels.push(rowLabel(row));
    values.push(row.frequency);
    const pct = row.percent ?? row.valid_percent;
    captions.push(
      showPercent && pct != null ? `${row.frequency} (${pct.toFixed(1)}%)` : String(row.frequency),
    );
  }

  return { labels, values, captions };
}

/** Nº total de respuestas contadas en las frecuencias (excluye faltantes). */
export function totalFrequency(frequencies: FrequencyRow[]): number {
  return frequencies.reduce((sum, row) => sum + row.frequency, 0);
}

/**
 * Elige el tipo de gráfico según el tipo de pregunta y el nº de categorías.
 * - boolean / single_choice / dropdown con pocas opciones → doughnut
 * - likert / ordinal → barras verticales (ordenadas)
 * - multiple_choice o muchas categorías → barras horizontales
 * - numérica sin frecuencias categóricas → tarjeta de resumen numérico
 */
export function pickChartType(question: QuestionDescriptive): TelemetryChartType {
  const type = (question.question_type || "").toLowerCase();
  const level = (question.measurement_level || "").toLowerCase();
  const categoryCount = question.frequencies.length;

  const isNumericOnly =
    (type === "number" || type === "numeric" || question.data_type === "numeric") &&
    categoryCount === 0;
  if (isNumericOnly && question.numeric) {
    return "numeric";
  }

  if (categoryCount === 0) {
    // Sin categorías y sin resumen numérico útil: usamos barras como fallback.
    return "bar";
  }

  if (type === "multiple_choice" || categoryCount > 8) {
    return "horizontalBar";
  }

  if (type === "likert" || level === "ordinal") {
    return "bar";
  }

  if (
    (type === "boolean" || type === "single_choice" || type === "dropdown") &&
    categoryCount <= 6
  ) {
    return "doughnut";
  }

  // Categórica genérica: doughnut si son pocas, barras si son varias.
  return categoryCount <= 6 ? "doughnut" : "bar";
}
