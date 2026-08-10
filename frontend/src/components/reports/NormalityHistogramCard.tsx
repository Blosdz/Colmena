import { useMemo, useRef } from "react";
import { Chart } from "react-chartjs-2";
import type { Chart as ChartJS, ChartData, ChartOptions, Plugin } from "chart.js";
import { useQuery } from "@tanstack/react-query";

import {
  getNormalityHistogram,
  type NormalityTestResult,
} from "../../api/reports";
import { useBarPalette } from "../../hooks/useBarPalette";
import { useChartColors } from "../../hooks/useChartColors";
import { withAlpha } from "../../utils/chartColors";
import { normalityDecision } from "../../utils/normality";
import { LoadingState } from "../ui/LoadingState";
import { makeBarValueLabelPlugin } from "../telemetry/chartPlugins";
import { ensureChartsRegistered } from "../telemetry/chartSetup";
import { ChartColorPicker } from "./ChartColorPicker";
import { ExportChartButton } from "./ExportChartButton";

ensureChartsRegistered();

const DECISION_TONE_COLORS: Record<string, string> = {
  "text-success": "#059669",
  "text-danger": "#DC2626",
  "text-muted": "#6B7280",
};

interface NormalityHistogramCardProps {
  formId: string;
  result: NormalityTestResult;
  /** Desactiva la animación para que el canvas quede pintado de forma síncrona al montar (captura para export). */
  exportMode?: boolean;
  /** Se dispara con la instancia de Chart.js apenas está construida (útil para capturar en export). */
  onChartReady?: (chart: ChartJS<"bar" | "line">) => void;
}

/**
 * Histograma del puntaje agregado con la curva normal teórica superpuesta.
 * La curva viene del backend ya escalada a conteos (densidad × n × ancho de bin).
 */
export function NormalityHistogramCard({
  formId,
  result,
  exportMode = false,
  onChartReady,
}: NormalityHistogramCardProps) {
  const targetType = result.target_type;
  const targetId = result.target_id;
  const chartRef = useRef<ChartJS<"bar" | "line"> | null>(null);

  const histogramQuery = useQuery({
    queryKey: ["project-reports-normality-histogram", formId, targetType, targetId],
    queryFn: () => getNormalityHistogram(formId, targetType, targetId),
    enabled: Boolean(formId && targetId),
  });

  const histogram = histogramQuery.data;

  const chartKey = `normality-${targetType}-${targetId}`;
  // La paleta la sortea el backend y se cachea por gráfico.
  const palette = useBarPalette(histogram?.bins.length ?? 0, chartKey);
  const defaultColors = useMemo(() => palette.colors ?? [], [palette.colors]);
  const binLabels = useMemo(
    () => (histogram?.bins ?? []).map((bin) => `${bin.bin_start.toFixed(1)}–${bin.bin_end.toFixed(1)}`),
    [histogram],
  );
  const chartColors = useChartColors(formId, chartKey, histogram?.bins.length ?? 0, defaultColors);
  const binColors = chartColors.colors;

  const chart = useMemo(() => {
    if (!histogram || histogram.bins.length === 0) return null;

    const barPoints = histogram.bins.map((bin) => ({
      x: (bin.bin_start + bin.bin_end) / 2,
      y: bin.count,
    }));
    const binWidth = histogram.bins[0].bin_end - histogram.bins[0].bin_start;
    const decision = normalityDecision({ classification: result.classification });

    const data: ChartData<"bar" | "line"> = {
      datasets: [
        {
          type: "bar" as const,
          label: "Frecuencia observada",
          data: barPoints,
          backgroundColor: binColors.map((color) => withAlpha(color, 0.6)),
          borderColor: binColors,
          borderWidth: 1,
          barThickness: "flex" as const,
          categoryPercentage: 1,
          barPercentage: 0.98,
        },
        {
          type: "line" as const,
          label: "Curva normal",
          data: histogram.curve,
          borderColor: "#1C1F24",
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.3,
        },
      ],
    };

    const options: ChartOptions<"bar" | "line"> = {
      responsive: true,
      maintainAspectRatio: false,
      animation: exportMode ? false : undefined,
      layout: { padding: { top: 20 } },
      plugins: {
        title: {
          display: true,
          text: decision.text,
          color: DECISION_TONE_COLORS[decision.tone] ?? "#1C1F24",
          font: { size: 12, weight: 600 },
          padding: { bottom: 8 },
        },
        // La leyenda y los títulos de eje van dentro del lienzo a propósito: es
        // lo único que llega al PNG del reporte, el encabezado de la tarjeta no.
        legend: {
          display: true,
          position: "bottom",
          labels: { boxWidth: 12, boxHeight: 8, font: { size: 11 }, color: "#6B7280" },
        },
        tooltip: {
          callbacks: {
            title: (items) => {
              // `== null` y no `=== undefined`: Chart.js tipa el valor como
              // `number | null` para los puntos sin dato.
              const x = items[0]?.parsed?.x;
              if (x == null) return "";
              return `${(x - binWidth / 2).toFixed(1)} – ${(x + binWidth / 2).toFixed(1)}`;
            },
            label: (ctx) => {
              const y = ctx.parsed.y;
              if (y == null) return "";
              return ctx.dataset.type === "line"
                ? `Normal teórica: ${y.toFixed(1)}`
                : `Frecuencia: ${y}`;
            },
          },
        },
      },
      scales: {
        x: {
          type: "linear",
          grid: { display: false },
          ticks: { maxTicksLimit: 8 },
          title: {
            display: true,
            text: "Puntaje",
            font: { size: 12, weight: 600 },
            color: "#6B7280",
          },
        },
        y: {
          beginAtZero: true,
          grid: { color: "#F0F1F3" },
          ticks: { precision: 0 },
          title: {
            display: true,
            text: "Frecuencia",
            font: { size: 12, weight: 600 },
            color: "#6B7280",
          },
        },
      },
    };

    const plugins: Plugin<"bar" | "line">[] = [
      makeBarValueLabelPlugin((index) => String(histogram.bins[index]?.count ?? "")) as Plugin<"bar" | "line">,
    ];

    return { data, options, plugins };
  }, [histogram, binColors, result.classification, exportMode]);

  return (
    <div className="rounded-[18px] border border-border bg-white p-4 shadow-card">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-dark">{result.target_name}</h3>
          <p className="text-xs text-muted">
            {histogram?.mean != null && histogram?.std != null
              ? `M = ${histogram.mean.toFixed(2)} · DE = ${histogram.std.toFixed(2)} · n = ${histogram.valid_n}`
              : `n = ${result.valid_n}`}
          </p>
        </div>
        <div className="flex shrink-0 items-start gap-2">
          <span
            className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.06em] ${
              result.classification === "normal"
                ? "bg-success/10 text-success"
                : result.classification === "non_normal"
                  ? "bg-danger/10 text-danger"
                  : "bg-surfaceSoft text-muted"
            }`}
          >
            {normalityDecision(result).text}
          </span>
          {chart && !exportMode ? (
            <ChartColorPicker
              labels={binLabels}
              colors={binColors}
              onSave={chartColors.save}
              onReset={chartColors.reset}
              isSaving={chartColors.isSaving}
              isCustom={chartColors.isCustom}
            />
          ) : null}
          {chart ? (
            <ExportChartButton
              formId={formId}
              chartId={chartKey}
              chartType="histogram"
              title={result.target_name}
              getImage={() => chartRef.current?.toBase64Image() ?? null}
            />
          ) : null}
        </div>
      </div>
      <div className="h-48">
        {histogramQuery.isLoading || palette.isPending ? (
          <LoadingState label="Generando histograma..." />
        ) : chart ? (
          <Chart
            ref={(instance) => {
              chartRef.current = instance ?? null;
              if (instance) onChartReady?.(instance);
            }}
            type="bar"
            data={chart.data}
            options={chart.options}
            plugins={chart.plugins}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted">
            Sin datos suficientes para el histograma.
          </div>
        )}
      </div>
    </div>
  );
}
