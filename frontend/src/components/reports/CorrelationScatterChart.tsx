import { useMemo, useRef } from "react";
import { Chart } from "react-chartjs-2";
import type { Chart as ChartJS, ChartData, ChartOptions } from "chart.js";

import { ensureChartsRegistered } from "../telemetry/chartSetup";
import { ExportChartButton } from "./ExportChartButton";

ensureChartsRegistered();

const METHOD_SYMBOLS: Record<string, string> = {
  pearson: "r",
  spearman: "Rho",
  kendall: "Tau",
  point_biserial: "r pb",
};

/** Rango fraccionario (promedia empates), la transformación que usa Spearman/Kendall internamente. */
function rankTransform(values: number[]): number[] {
  const order = values.map((value, index) => ({ value, index })).sort((a, b) => a.value - b.value);
  const ranks = new Array<number>(values.length);
  let i = 0;
  while (i < order.length) {
    let j = i;
    while (j + 1 < order.length && order[j + 1].value === order[i].value) j += 1;
    const averageRank = (i + j) / 2 + 1;
    for (let k = i; k <= j; k += 1) ranks[order[k].index] = averageRank;
    i = j + 1;
  }
  return ranks;
}

function linearRegression(x: number[], y: number[]): { slope: number; intercept: number } | null {
  const n = x.length;
  if (n < 2) return null;
  const meanX = x.reduce((sum, value) => sum + value, 0) / n;
  const meanY = y.reduce((sum, value) => sum + value, 0) / n;
  let numerator = 0;
  let denominator = 0;
  for (let i = 0; i < n; i += 1) {
    numerator += (x[i] - meanX) * (y[i] - meanY);
    denominator += (x[i] - meanX) ** 2;
  }
  if (denominator === 0) return null;
  const slope = numerator / denominator;
  return { slope, intercept: meanY - slope * meanX };
}

/** Slug simple para identificar de forma estable una gráfica de correlación (sin IDs propios de target). */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

interface CorrelationScatterChartProps {
  formId: string;
  xLabel: string;
  yLabel: string;
  xValues: number[];
  yValues: number[];
  coefficient: number | null;
  pValue: number | null;
  method: string;
  alpha: number;
  /** Desactiva la animación para que el canvas quede pintado de forma síncrona al montar (captura para export). */
  exportMode?: boolean;
  /** Se dispara con la instancia de Chart.js apenas está construida (útil para capturar en export). */
  onChartReady?: (chart: ChartJS<"scatter" | "line">) => void;
}

/**
 * Dispersión X/Y con recta de tendencia y caja de estadísticos (Rho/r, p-value, R²).
 * Para Spearman/Kendall (métodos basados en rangos) grafica los rangos de cada valor,
 * no el valor crudo: es la transformación que esos coeficientes usan por definición, y
 * hace que el gráfico cambie de forma real al alternar el método, no solo los números.
 */
export function CorrelationScatterChart({
  formId,
  xLabel,
  yLabel,
  xValues,
  yValues,
  coefficient,
  pValue,
  method,
  alpha,
  exportMode = false,
  onChartReady,
}: CorrelationScatterChartProps) {
  const chartRef = useRef<ChartJS<"scatter" | "line"> | null>(null);
  const useRanks = method === "spearman" || method === "kendall";

  const [plotX, plotY] = useMemo(
    () => (useRanks ? [rankTransform(xValues), rankTransform(yValues)] : [xValues, yValues]),
    [xValues, yValues, useRanks],
  );

  const regression = useMemo(() => linearRegression(plotX, plotY), [plotX, plotY]);

  const axisXLabel = useRanks ? `Rango de ${xLabel}` : xLabel;
  const axisYLabel = useRanks ? `Rango de ${yLabel}` : yLabel;

  const data = useMemo<ChartData<"scatter" | "line">>(() => {
    const points = plotX.map((x, index) => ({ x, y: plotY[index] }));
    const datasets: ChartData<"scatter" | "line">["datasets"] = [
      {
        type: "scatter" as const,
        // Los ejes ya dicen qué variables son; en la leyenda basta con
        // distinguir los puntos de la recta de tendencia.
        label: "Observaciones",
        data: points,
        backgroundColor: "transparent",
        borderColor: "#2563EB",
        borderWidth: 1.5,
        pointRadius: 4,
        pointHoverRadius: 5,
      },
    ];
    if (regression && plotX.length > 0) {
      const minX = Math.min(...plotX);
      const maxX = Math.max(...plotX);
      datasets.push({
        type: "line" as const,
        label: "Tendencia",
        data: [
          { x: minX, y: regression.slope * minX + regression.intercept },
          { x: maxX, y: regression.slope * maxX + regression.intercept },
        ],
        borderColor: "#DC2626",
        borderWidth: 2,
        pointRadius: 0,
        tension: 0,
      });
    }
    return { datasets };
  }, [plotX, plotY, regression, axisXLabel, axisYLabel]);

  const options = useMemo<ChartOptions<"scatter" | "line">>(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      animation: exportMode ? false : undefined,
      plugins: {
        // Dentro del lienzo: es lo único que llega al PNG del reporte.
        legend: {
          display: true,
          position: "bottom",
          labels: { boxWidth: 12, boxHeight: 8, font: { size: 11 }, color: "#6B7280" },
        },
        tooltip: {
          callbacks: {
            label: (ctx) =>
              `${axisXLabel}: ${(ctx.parsed.x ?? 0).toFixed(2)} · ${axisYLabel}: ${(ctx.parsed.y ?? 0).toFixed(2)}`,
          },
        },
      },
      scales: {
        x: {
          type: "linear",
          title: { display: true, text: axisXLabel, color: "#6B7280", font: { size: 11 } },
          grid: { color: "#F0F1F3" },
        },
        y: {
          title: { display: true, text: axisYLabel, color: "#6B7280", font: { size: 11 } },
          grid: { color: "#F0F1F3" },
        },
      },
    }),
    [axisXLabel, axisYLabel, exportMode],
  );

  if (xValues.length === 0) return null;

  const rSquared = coefficient !== null ? coefficient ** 2 : null;
  const symbol = METHOD_SYMBOLS[method] ?? method;
  const pText = pValue === null ? "—" : pValue < alpha ? `< ${alpha}` : pValue.toFixed(3);

  return (
    <div className="relative rounded-[18px] border border-border bg-white p-4 shadow-card">
      <div className="absolute right-4 top-4 z-10">
        <ExportChartButton
          formId={formId}
          chartId={`correlation-${slugify(xLabel)}-${slugify(yLabel)}-${method}`}
          chartType="scatter"
          title={`${xLabel} vs ${yLabel}`}
          getImage={() => chartRef.current?.toBase64Image() ?? null}
        />
      </div>
      <div style={{ height: 300 }}>
        <Chart
          ref={(instance) => {
            chartRef.current = instance ?? null;
            if (instance) onChartReady?.(instance);
          }}
          type="scatter"
          data={data}
          options={options}
        />
      </div>
      <div className="absolute left-9 top-6 rounded-md border border-border bg-white/95 px-3 py-2 text-xs leading-relaxed text-dark shadow-soft">
        <div>
          {symbol}
          {useRanks ? " (rangos)" : ""} = {coefficient !== null ? coefficient.toFixed(2) : "—"}
        </div>
        <div>p-value {pText}</div>
        <div>R² = {rSquared !== null ? rSquared.toFixed(2) : "—"}</div>
      </div>
    </div>
  );
}
