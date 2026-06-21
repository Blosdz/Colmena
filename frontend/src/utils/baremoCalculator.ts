export type BaremoLevel = {
  id: string;
  name: string;
  min: number;
  max: number;
  description: string;
  color: string;
};

export function calculateEqualRangeBaremos(minScore: number, maxScore: number, levelsCount: number): BaremoLevel[] {
  if (levelsCount <= 0 || minScore >= maxScore) return [];

  const range = maxScore - minScore;
  const step = range / levelsCount;
  
  const defaultColors = ["#DC2626", "#F5B21A", "#11B7B2", "#059669", "#2563EB"];
  const defaultNames = ["Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"];

  const levels: BaremoLevel[] = [];
  
  for (let i = 0; i < levelsCount; i++) {
    const currentMin = i === 0 ? minScore : Math.round((minScore + step * i) * 10) / 10;
    const currentMax = i === levelsCount - 1 ? maxScore : Math.round((minScore + step * (i + 1) - 0.1) * 10) / 10;
    
    levels.push({
      id: crypto.randomUUID(),
      name: defaultNames[i] || `Nivel ${i + 1}`,
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
      issues.push(`Solapamiento entre ${current.name} y ${next.name}`);
    } else if (current.max < next.min - 0.1) {
      issues.push(`Hueco detectado entre ${current.name} y ${next.name}`);
    }
  }

  return { valid: issues.length === 0, issues };
}
