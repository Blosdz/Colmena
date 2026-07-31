import { useMemo } from "react";
import { Bar } from "react-chartjs-2";
import type { ChartData, ChartOptions } from "chart.js";

import type { ReliabilityTarget } from "../../api/reports";
import { ensureChartsRegistered } from "../telemetry/chartSetup";

ensureChartsRegistered();

const CLASSIFICATION_COLORS: Record<string, string> = {
  excelente: "#059669",
  bueno: "#11B7B2",
  aceptable: "#F5B21A",
  cuestionable: "#FF6A2A",
  pobre: "#DC2626",
  inaceptable: "#DC2626",
};

interface AlphaBarChartProps {
  variableTargets: ReliabilityTarget[];
  dimensionTargets: ReliabilityTarget[];
}

/** Barras horizontales del alfa de Cronbach por variable y dimensión (0 a 1). */
export function AlphaBarChart({ variableTargets, dimensionTargets }: AlphaBarChartProps) {
  const targets = useMemo(
    () => [...variableTargets, ...dimensionTargets].filter((t) => t.result.alpha !== null),
    [variableTargets, dimensionTargets],
  );

  const data = useMemo<ChartData<"bar">>(() => {
    return {
      labels: targets.map((t) => t.target_name),
      datasets: [
        {
          data: targets.map((t) => t.result.alpha ?? 0),
          backgroundColor: targets.map(
            (t) => CLASSIFICATION_COLORS[t.result.classification] ?? "#6B7280",
          ),
          borderRadius: 6,
          barThickness: 22,
        },
      ],
    };
  }, [targets]);

  const options = useMemo<ChartOptions<"bar">>(
    () => ({
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const target = targets[ctx.dataIndex];
              return `α = ${(target.result.alpha ?? 0).toFixed(3)} · ${target.item_count} ítems · ${target.result.classification}`;
            },
          },
        },
      },
      scales: {
        x: {
          min: 0,
          max: 1,
          grid: { color: "#F0F1F3" },
          ticks: { stepSize: 0.1 },
        },
        y: {
          grid: { display: false },
        },
      },
    }),
    [targets],
  );

  if (targets.length === 0) return null;

  return (
    <div className="rounded-[18px] border border-border bg-white p-4 shadow-card">
      <h3 className="mb-1 text-sm font-semibold text-dark">Alfa de Cronbach por conjunto de ítems</h3>
      <p className="mb-3 text-xs text-muted">
        La zona confiable empieza en α = 0.7; el color indica la clasificación de cada conjunto.
      </p>
      <div style={{ height: Math.max(160, targets.length * 34 + 60) }}>
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}
