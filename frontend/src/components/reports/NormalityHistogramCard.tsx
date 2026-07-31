import { useMemo } from "react";
import { Chart } from "react-chartjs-2";
import type { ChartData, ChartOptions } from "chart.js";
import { useQuery } from "@tanstack/react-query";

import { getNormalityHistogram, type NormalityTestResult } from "../../api/reports";
import { LoadingState } from "../ui/LoadingState";
import { ensureChartsRegistered } from "../telemetry/chartSetup";

ensureChartsRegistered();

interface NormalityHistogramCardProps {
  formId: string;
  result: NormalityTestResult;
}

/**
 * Histograma del puntaje agregado con la curva normal teórica superpuesta.
 * La curva viene del backend ya escalada a conteos (densidad × n × ancho de bin).
 */
export function NormalityHistogramCard({ formId, result }: NormalityHistogramCardProps) {
  const targetType = result.target_type;
  const targetId = result.target_id;

  const histogramQuery = useQuery({
    queryKey: ["project-reports-normality-histogram", formId, targetType, targetId],
    queryFn: () => getNormalityHistogram(formId, targetType, targetId),
    enabled: Boolean(formId && targetId),
  });

  const histogram = histogramQuery.data;

  const chart = useMemo(() => {
    if (!histogram || histogram.bins.length === 0) return null;

    const barPoints = histogram.bins.map((bin) => ({
      x: (bin.bin_start + bin.bin_end) / 2,
      y: bin.count,
    }));
    const binWidth = histogram.bins[0].bin_end - histogram.bins[0].bin_start;
    const isNormal = result.classification === "normal";

    const data: ChartData<"bar" | "line"> = {
      datasets: [
        {
          type: "bar" as const,
          label: "Frecuencia",
          data: barPoints,
          backgroundColor: isNormal ? "#11B7B266" : "#F5B21A66",
          borderColor: isNormal ? "#11B7B2" : "#D99712",
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
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              const x = items[0]?.parsed?.x;
              if (x === undefined) return "";
              return `${(x - binWidth / 2).toFixed(1)} – ${(x + binWidth / 2).toFixed(1)}`;
            },
            label: (ctx) =>
              ctx.dataset.type === "line"
                ? `Normal teórica: ${ctx.parsed.y.toFixed(1)}`
                : `Frecuencia: ${ctx.parsed.y}`,
          },
        },
      },
      scales: {
        x: {
          type: "linear",
          grid: { display: false },
          ticks: { maxTicksLimit: 8 },
        },
        y: {
          beginAtZero: true,
          grid: { color: "#F0F1F3" },
          ticks: { precision: 0 },
        },
      },
    };

    return { data, options };
  }, [histogram, result.classification]);

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
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.06em] ${
            result.classification === "normal"
              ? "bg-success/10 text-success"
              : result.classification === "non_normal"
                ? "bg-danger/10 text-danger"
                : "bg-surfaceSoft text-muted"
          }`}
        >
          {result.classification === "normal"
            ? "Normal"
            : result.classification === "non_normal"
              ? "No normal"
              : "No concluyente"}
        </span>
      </div>
      <div className="h-48">
        {histogramQuery.isLoading ? (
          <LoadingState label="Generando histograma..." />
        ) : chart ? (
          <Chart type="bar" data={chart.data} options={chart.options} />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted">
            Sin datos suficientes para el histograma.
          </div>
        )}
      </div>
    </div>
  );
}
