import { useMemo, useRef } from "react";
import { Bar } from "react-chartjs-2";
import type { Chart as ChartJS, ChartData, ChartOptions } from "chart.js";

import type { ReliabilityTarget } from "../../api/reports";
import { useBarPalette } from "../../hooks/useBarPalette";
import { useChartColors } from "../../hooks/useChartColors";
import { LEGEND_LABEL_STYLE, perBarLegendLabels } from "../../utils/chartLegend";
import { makeBarValueLabelPlugin } from "../telemetry/chartPlugins";
import { ensureChartsRegistered } from "../telemetry/chartSetup";
import { ChartColorPicker } from "./ChartColorPicker";
import { ExportChartButton } from "./ExportChartButton";

ensureChartsRegistered();

interface AlphaBarChartProps {
  formId: string;
  variableTargets: ReliabilityTarget[];
  dimensionTargets: ReliabilityTarget[];
  /** Desactiva la animación para que el canvas quede pintado de forma síncrona al montar (captura para export). */
  exportMode?: boolean;
  /** Se dispara con la instancia de Chart.js apenas está construida (útil para capturar en export). */
  onChartReady?: (chart: ChartJS<"bar">) => void;
}

/** Barras verticales del alfa de Cronbach por variable y dimensión (0 a 1). */
export function AlphaBarChart({
  formId,
  variableTargets,
  dimensionTargets,
  exportMode = false,
  onChartReady,
}: AlphaBarChartProps) {
  const chartRef = useRef<ChartJS<"bar"> | null>(null);

  const targets = useMemo(
    () => [...variableTargets, ...dimensionTargets].filter((t) => t.result.alpha !== null),
    [variableTargets, dimensionTargets],
  );

  const chartKey = `reliability-alpha-${formId}`;
  const palette = useBarPalette(targets.length, chartKey);
  // Memoizado: `?? []` crearía un array nuevo en cada render y con él se
  // recalcularían los `useMemo` que dependen de los colores.
  const defaultColors = useMemo(() => palette.colors ?? [], [palette.colors]);
  const chartColors = useChartColors(formId, chartKey, targets.length, defaultColors);
  const colors = chartColors.colors;
  const categories = useMemo(() => targets.map((t) => t.target_name), [targets]);
  const values = useMemo(() => targets.map((t) => t.result.alpha ?? 0), [targets]);
  const captions = useMemo(
    () =>
      targets.map(
        (t) =>
          `α = ${(t.result.alpha ?? 0).toFixed(3)} · ${t.item_count} ítems · ${t.result.classification}`,
      ),
    [targets],
  );
  const valueLabels = useMemo(
    () => targets.map((t) => (t.result.alpha ?? 0).toFixed(3)),
    [targets],
  );

  const data = useMemo<ChartData<"bar">>(() => {
    return {
      labels: categories,
      datasets: [
        {
          label: "Alfa de Cronbach",
          data: values,
          backgroundColor: colors,
          borderRadius: 6,
          maxBarThickness: 48,
        },
      ],
    };
  }, [categories, values, colors]);

  const plugins = useMemo(
    () => [makeBarValueLabelPlugin((index) => valueLabels[index])],
    [valueLabels],
  );

  const options = useMemo<ChartOptions<"bar">>(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: exportMode ? false : undefined,
      layout: { padding: { top: 24 } },
      plugins: {
        // La leyenda y los títulos de eje van dentro del lienzo a propósito: es
        // lo único que llega al PNG del reporte, el encabezado de la tarjeta no.
        legend: {
          display: true,
          position: "bottom",
          labels: { ...LEGEND_LABEL_STYLE, generateLabels: perBarLegendLabels(valueLabels) },
          // Las entradas son barras de un mismo dataset: no hay nada que ocultar.
          onClick: () => {},
        },
        tooltip: {
          callbacks: { label: (ctx) => captions[ctx.dataIndex] ?? "" },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { maxRotation: 45, minRotation: 45, autoSkip: false },
          title: {
            display: true,
            text: "Conjunto de ítems",
            font: { size: 12, weight: 600 },
            color: "#6B7280",
          },
        },
        y: {
          min: 0,
          max: 1,
          grid: { color: "#F0F1F3" },
          ticks: { stepSize: 0.1 },
          title: {
            display: true,
            text: "α (alfa de Cronbach)",
            font: { size: 12, weight: 600 },
            color: "#6B7280",
          },
        },
      },
    }),
    [captions, valueLabels, exportMode],
  );

  if (targets.length === 0) return null;

  return (
    <div className="rounded-[18px] border border-border bg-white p-4 shadow-card">
      <div className="mb-1 flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-dark">Alfa de Cronbach por conjunto de ítems</h3>
        <div className="flex shrink-0 items-start gap-2">
          {exportMode ? null : (
            <ChartColorPicker
              labels={categories}
              colors={colors}
              onSave={chartColors.save}
              onReset={chartColors.reset}
              isSaving={chartColors.isSaving}
              isCustom={chartColors.isCustom}
            />
          )}
          <ExportChartButton
            formId={formId}
            chartId={chartKey}
            chartType="bar"
            title="Alfa de Cronbach por conjunto de ítems"
            getImage={() => chartRef.current?.toBase64Image() ?? null}
          />
        </div>
      </div>
      <p className="mb-3 text-xs text-muted">
        La zona confiable empieza en α = 0.7; la clasificación de cada conjunto aparece al pasar el
        cursor sobre su barra.
      </p>
      {palette.isPending ? (
        <div style={{ height: 360 }} />
      ) : (
        <div style={{ height: 360 }}>
          <Bar
            ref={(instance) => {
              chartRef.current = instance ?? null;
              if (instance) onChartReady?.(instance);
            }}
            data={data}
            options={options}
            plugins={plugins}
          />
        </div>
      )}
    </div>
  );
}
