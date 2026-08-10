// Plugin de Chart.js hecho a mano para las barras de frecuencia: etiqueta de
// valor siempre visible. Se dibuja directamente sobre el canvas, así que queda
// incluida tal cual en la captura que usa ExportChartButton (toBase64Image) —
// lo que se ve en pantalla es exactamente lo que se exporta.
import type { Plugin } from "chart.js";

/** Dibuja el valor (o texto dado) encima de cada barra vertical — Chart.js no lo hace nativamente. */
export function makeBarValueLabelPlugin(getLabel: (index: number) => string | null | undefined): Plugin<"bar"> {
  return {
    id: "barValueLabel",
    afterDatasetsDraw(chart) {
      const meta = chart.getDatasetMeta(0);
      if (!meta || meta.hidden) return;
      const { ctx } = chart;
      ctx.save();
      ctx.fillStyle = "#1C1F24";
      ctx.font = "600 11px Inter, system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "bottom";
      meta.data.forEach((bar, index) => {
        const label = getLabel(index);
        if (!label) return;
        const point = bar as unknown as { x: number; y: number };
        ctx.fillText(label, point.x, point.y - 4);
      });
      ctx.restore();
    },
  };
}
