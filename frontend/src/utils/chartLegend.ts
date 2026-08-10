import type { Chart as ChartJS, LegendItem } from "chart.js";

/**
 * Leyenda con una entrada por barra —su color, su categoría y su valor— en vez
 * de una sola para todo el conjunto de datos.
 *
 * Chart.js, como ECharts, mapea la leyenda al *dataset*: con un único dataset de
 * barras multicolor sale una sola entrada que no identifica nada. Esto la
 * reconstruye a partir de las etiquetas del eje, igual que hace el 3D creando
 * una serie por barra, para que las dos variantes del reporte coincidan.
 */
export function perBarLegendLabels(valueLabels: string[]) {
  return (chart: ChartJS): LegendItem[] => {
    const labels = (chart.data.labels ?? []) as string[];
    const background = chart.data.datasets[0]?.backgroundColor;
    const colors = Array.isArray(background) ? (background as string[]) : [];

    return labels.map((label, index) => ({
      text: valueLabels[index] ? `${label}: ${valueLabels[index]}` : label,
      fillStyle: colors[index],
      strokeStyle: colors[index],
      lineWidth: 0,
      // Ocultar una barra suelta no es posible (todas viven en el mismo
      // dataset), así que las entradas nunca se marcan como ocultas.
      hidden: false,
      index,
    }));
  };
}

/** Estilo común de la leyenda, igual al que usa el `option` 3D del backend. */
export const LEGEND_LABEL_STYLE = {
  boxWidth: 12,
  boxHeight: 8,
  font: { size: 11 },
  color: "#6B7280",
} as const;
