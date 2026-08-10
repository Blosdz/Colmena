import { useMutation } from "@tanstack/react-query";
import { ImagePlus } from "lucide-react";

import { uploadChartImage } from "../../api/chartImages";

interface ExportChartButtonProps {
  formId: string;
  chartId: string;
  chartType: string;
  title: string;
  /**
   * Captura la gráfica en el momento del click (ej. `chartRef.current?.toBase64Image() ?? null`).
   * Puede ser asíncrona: el 3D de ECharts se lee del canvas WebGL antes de subirlo.
   */
  getImage: () => string | null | Promise<string | null>;
}

/** Botón que captura una gráfica ya renderizada y la sube como figura "word-ready" para la tesis. */
export function ExportChartButton({ formId, chartId, chartType, title, getImage }: ExportChartButtonProps) {
  const mutation = useMutation({
    mutationFn: async () => {
      const dataUrl = await getImage();
      if (!dataUrl) throw new Error("No se pudo capturar la gráfica");
      return uploadChartImage(formId, { chart_id: chartId, chart_type: chartType, title, data_url: dataUrl });
    },
  });

  return (
    <div className="flex shrink-0 flex-col items-end gap-1">
      <button
        type="button"
        disabled={mutation.isPending || !formId}
        onClick={() => mutation.mutate()}
        className="inline-flex items-center gap-1.5 rounded-full bg-surfaceSoft px-2.5 py-1 text-[11px] font-medium text-muted transition-colors hover:text-dark disabled:cursor-not-allowed disabled:opacity-60"
      >
        <ImagePlus className="h-3.5 w-3.5" />
        {mutation.isPending ? "Agregando..." : mutation.isSuccess ? "Agregado ✓" : "Agregar a reporte"}
      </button>
      {mutation.isError ? <p className="text-[10px] text-danger">No se pudo exportar la gráfica.</p> : null}
    </div>
  );
}
