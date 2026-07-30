export type BaremoLevel = {
  id: string;
  name: string;
  min: number;
  max: number;
  description: string;
  color: string;
};

const DEFAULT_LEVEL_NAMES = ["Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"];
const THREE_LEVEL_NAMES = ["Bajo", "Medio", "Alto"];

export function calculateEqualRangeBaremos(
  minScore: number,
  maxScore: number,
  levelsCount: number,
  aggregationMethod: "sum" | "mean" = "sum"
): BaremoLevel[] {
  if (levelsCount <= 0 || minScore >= maxScore) return [];

  const defaultColors = ["#DC2626", "#F5B21A", "#11B7B2", "#059669", "#2563EB"];
  // Mismo criterio que compute_equal_range_baremo en el backend: 3 niveles usa
  // Bajo/Medio/Alto en vez de recortar la lista de 5 nombres.
  const names = levelsCount === 3 ? THREE_LEVEL_NAMES : DEFAULT_LEVEL_NAMES;
  const isIntegerRange = Number.isInteger(minScore) && Number.isInteger(maxScore);

  const levels: BaremoLevel[] = [];

  // Escalas de puntaje entero (suma de items): ancho = (max - min + 1) / niveles,
  // con cortes enteros contiguos sin huecos ni solapamientos (misma formula que
  // compute_equal_range_baremo en el backend para aggregation_method === "sum").
  if (aggregationMethod === "sum" && isIntegerRange) {
    const width = (maxScore - minScore + 1) / levelsCount;
    const boundaries: number[] = [];
    for (let i = 0; i < levelsCount; i++) boundaries.push(minScore + Math.round(width * i));
    boundaries.push(maxScore + 1);

    for (let i = 0; i < levelsCount; i++) {
      levels.push({
        id: crypto.randomUUID(),
        name: names[i] || `Nivel ${i + 1}`,
        min: boundaries[i],
        max: boundaries[i + 1] - 1,
        description: "",
        color: defaultColors[i % defaultColors.length]
      });
    }
    return levels;
  }

  const range = maxScore - minScore;
  const step = range / levelsCount;

  for (let i = 0; i < levelsCount; i++) {
    const currentMin = i === 0 ? minScore : Math.round((minScore + step * i) * 10) / 10;
    const currentMax = i === levelsCount - 1 ? maxScore : Math.round((minScore + step * (i + 1) - 0.1) * 10) / 10;

    levels.push({
      id: crypto.randomUUID(),
      name: names[i] || `Nivel ${i + 1}`,
      min: currentMin,
      max: currentMax,
      description: "",
      color: defaultColors[i % defaultColors.length]
    });
  }

  return levels;
}

export function validateBaremoGaps(levels: BaremoLevel[]): { valid: boolean; issues: string[] } {
  const sorted = [...levels].sort((a, b) => a.min - b.min);
  const issues: string[] = [];

  for (let i = 0; i < sorted.length - 1; i++) {
    const current = sorted[i];
    const next = sorted[i + 1];

    if (current.max >= next.min) {
      issues.push(`Solapamiento entre "${current.name}" (hasta ${current.max}) y "${next.name}" (desde ${next.min}).`);
    } else if (current.max < next.min - 0.1) {
      issues.push(
        `Hueco entre "${current.name}" (hasta ${current.max}) y "${next.name}" (desde ${next.min}): ese rango intermedio no queda cubierto por ninguna categoría.`,
      );
    }
  }

  return { valid: issues.length === 0, issues };
}
