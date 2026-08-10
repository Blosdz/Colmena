import { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import type { Chart as ChartJS, ChartData, ChartOptions, Plugin } from "chart.js";

import { useBarPalette } from "../../hooks/useBarPalette";
import { useChartColors } from "../../hooks/useChartColors";
import { LEGEND_LABEL_STYLE, perBarLegendLabels } from "../../utils/chartLegend";
import { THREE_LEVEL_NAMES } from "../../utils/baremoCalculator";
import { ensureChartsRegistered } from "../telemetry/chartSetup";
import { ChartColorPicker } from "./ChartColorPicker";

ensureChartsRegistered();

/** Forma m\u00ednima que necesita este gr\u00e1fico: la cumplen tanto `BaremoResolvedLevel`
 * (resoluci\u00f3n del backend) como los niveles derivados de una tabla de baremo editable. */
export interface BaremoLevelDatum {
  label: string;
  percent: number;
  n: number;
  severity_order: number;
}

function normalizeLabel(label: string): string {
  return label
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}

/** Malo/Regular/Bueno cuando hay exactamente 3 niveles con esos nombres; si no, por severity_order. Mismo criterio que usaba el export matplotlib (order_baremo_levels). */
function orderLevels(levels: BaremoLevelDatum[]): BaremoLevelDatum[] {
  if (levels.length === 3) {
    const byLabel = new Map(levels.map((level) => [normalizeLabel(level.label), level]));
    const ordered = THREE_LEVEL_NAMES.map((name) => byLabel.get(normalizeLabel(name))).filter(
      (level): level is BaremoLevelDatum => Boolean(level),
    );
    if (ordered.length === 3) return ordered;
  }
  return [...levels].sort((a, b) => a.severity_order - b.severity_order);
}

/** Dibuja el porcentaje encima de cada barra — Chart.js no lo hace nativamente. Solo para este gráfico. */
const percentLabelPlugin: Plugin<"bar"> = {
  id: "baremoPercentLabel",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    const values = chart.data.datasets[0]?.data as number[] | undefined;
    if (!values) return;
    ctx.save();
    ctx.fillStyle = "#000000";
    ctx.font = "600 12px Inter, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    meta.data.forEach((bar, index) => {
      const value = values[index];
      if (value === undefined) return;
      ctx.fillText(`${value.toFixed(1)}%`, bar.x, bar.y - 4);
    });
    ctx.restore();
  },
};

/**
 * Semáforo pastel fijo para el caso más común (3 niveles), ordenado de peor a
 * mejor igual que `orderLevels`: Malo, Regular, Bueno. Un documento formal no
 * debería depender de un sorteo de color entre recargas.
 */
const PASTEL_SEMAPHORE_COLORS = ["#F0A8A8", "#F5D68A", "#A8D5B5"];

interface BaremoLevelsChartProps {
  variableLabel: string;
  levels: BaremoLevelDatum[];
  /** Identifica este gráfico para la paleta personalizada guardada y la del backend. Debe ser estable (no depender de `variableLabel`, que es editable). */
  chartKey: string;
  formId: string;
  /** Desactiva la animación para que el canvas quede pintado de forma síncrona al montar (captura para export). */
  exportMode?: boolean;
  /** Se dispara con la instancia de Chart.js apenas está construida (útil para capturar en export). */
  onChartReady?: (chart: ChartJS<"bar">) => void;
}

/**
 * Barras verticales del porcentaje de casos por nivel de baremo (Malo/Regular/
 * Bueno), coloreadas semáforo pastel rojo/ámbar/verde.
 */
export function BaremoLevelsChart({
  variableLabel,
  levels,
  chartKey,
  formId,
  exportMode = false,
  onChartReady,
}: BaremoLevelsChartProps) {
  const ordered = useMemo(() => orderLevels(levels), [levels]);
  const isThreeLevel = ordered.length === 3;
  // Con 3 niveles el semáforo pastel es fijo (documento sobrio, sin sorteo
  // entre recargas); con cualquier otro número de niveles se conserva la
  // paleta del backend que usa el resto de gráficas, para que el color en
  // pantalla y el del PNG del reporte coincidan. `count = 0` evita pedirle al
  // backend una paleta que no se va a usar.
  const palette = useBarPalette(isThreeLevel ? 0 : ordered.length, chartKey);
  const defaultColors = useMemo(
    () => (isThreeLevel ? PASTEL_SEMAPHORE_COLORS : (palette.colors ?? [])),
    [isThreeLevel, palette.colors],
  );
  const isPending = isThreeLevel ? false : palette.isPending;
  const chartColors = useChartColors(formId, chartKey, ordered.length, defaultColors);
  const colors = chartColors.colors;

  const categories = useMemo(() => ordered.map((level) => level.label), [ordered]);
  const percents = useMemo(() => ordered.map((level) => level.percent), [ordered]);
  const captions = useMemo(
    () => ordered.map((level) => `${level.percent.toFixed(1)}% · n = ${level.n}`),
    [ordered],
  );
  const valueLabels = useMemo(
    () => ordered.map((level) => `${level.percent.toFixed(1)}%`),
    [ordered],
  );
  const yMax = useMemo(
    () => Math.max(100, ...ordered.map((level) => level.percent)) + 10,
    [ordered],
  );

  const data = useMemo<ChartData<"bar">>(
    () => ({
      labels: categories,
      datasets: [
        {
          label: "Porcentaje de casos",
          data: percents,
          backgroundColor: colors,
          borderRadius: 6,
          barThickness: 48,
        },
      ],
    }),
    [categories, percents, colors],
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
          title: {
            display: true,
            text: "Nivel",
            font: { size: 12, weight: 600 },
            color: "#6B7280",
          },
        },
        y: {
          min: 0,
          max: yMax,
          grid: { color: "#F0F1F3" },
          ticks: { callback: (value) => `${value}%` },
          title: {
            display: true,
            text: "Porcentaje de casos",
            font: { size: 12, weight: 600 },
            color: "#6B7280",
          },
        },
      },
    }),
    [captions, valueLabels, yMax, exportMode],
  );

  if (ordered.length === 0) return null;

  return (
    <div className="rounded-[18px] border border-border bg-white p-4 shadow-card">
      <div className="mb-3 flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-dark">Nivel de {variableLabel}</h3>
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
      </div>
      {isPending ? (
        <div style={{ height: 320 }} />
      ) : (
        <div style={{ height: 320 }}>
          <Bar
            ref={(instance) => {
              if (instance) onChartReady?.(instance);
            }}
            data={data}
            options={options}
            plugins={[percentLabelPlugin]}
          />
        </div>
      )}
    </div>
  );
}
