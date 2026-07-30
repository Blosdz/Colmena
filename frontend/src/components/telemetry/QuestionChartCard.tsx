import { useMemo, useState } from "react";
import { Bar, Pie } from "react-chartjs-2";
import type { ChartData, ChartOptions } from "chart.js";
import { BarChart3, PieChart } from "lucide-react";

import type { QuestionDescriptive } from "../../types/analysis";
import {
  frequenciesToChartData,
  palette,
  pickChartType,
  totalFrequency,
} from "../../utils/telemetryChart";
import { ensureChartsRegistered } from "./chartSetup";

ensureChartsRegistered();

type ChartView = "pie" | "bar";

function NumericSummary({ question }: { question: QuestionDescriptive }) {
  const n = question.numeric;
  if (!n) return null;
  const cells: Array<[string, string]> = [
    ["Media", n.mean != null ? n.mean.toFixed(2) : "—"],
    ["Mediana", n.median != null ? n.median.toFixed(2) : "—"],
    ["Desv. est.", n.standard_deviation != null ? n.standard_deviation.toFixed(2) : "—"],
    ["Mín", n.minimum != null ? String(n.minimum) : "—"],
    ["Máx", n.maximum != null ? String(n.maximum) : "—"],
    ["N válido", String(n.valid_n)],
  ];
  return (
    <div className="grid grid-cols-3 gap-2">
      {cells.map(([label, value]) => (
        <div key={label} className="rounded-[10px] border border-border bg-surfaceSoft px-2 py-2 text-center">
          <div className="text-sm font-semibold text-dark">{value}</div>
          <div className="mt-0.5 text-[9px] uppercase tracking-[0.06em] text-muted">{label}</div>
        </div>
      ))}
    </div>
  );
}

/** Tabla de frecuencias (categoría / conteo / %) que acompaña al gráfico de cada pregunta. */
function FrequencyTable({
  labels,
  colors,
  values,
  total,
}: {
  labels: string[];
  colors: string[];
  values: number[];
  total: number;
}) {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border">
      <table className="w-full border-collapse text-[12px]">
        <thead>
          <tr className="bg-surfaceSoft text-[10px] uppercase tracking-[0.06em] text-muted">
            <th className="px-3 py-1.5 text-left font-semibold">Categoría</th>
            <th className="px-3 py-1.5 text-right font-semibold">N</th>
            <th className="px-3 py-1.5 text-right font-semibold">%</th>
          </tr>
        </thead>
        <tbody>
          {labels.map((label, index) => (
            <tr key={`${label}-${index}`} className="border-t border-border">
              <td className="px-3 py-1.5 text-dark">
                <span className="mr-2 inline-block h-2 w-2 shrink-0 rounded-full align-middle" style={{ backgroundColor: colors[index] }} />
                <span className="truncate align-middle" title={label}>{label}</span>
              </td>
              <td className="px-3 py-1.5 text-right tabular-nums text-dark">{values[index]}</td>
              <td className="px-3 py-1.5 text-right tabular-nums text-muted">
                {total > 0 ? `${((values[index] / total) * 100).toFixed(0)}%` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Botones para alternar el tipo de gráfico de la pregunta (pastel / barras). */
function ViewToggle({ view, onChange }: { view: ChartView; onChange: (v: ChartView) => void }) {
  const item = (value: ChartView, Icon: typeof PieChart, label: string) => {
    const active = view === value;
    return (
      <button
        type="button"
        aria-label={label}
        title={label}
        aria-pressed={active}
        onClick={() => onChange(value)}
        className={`inline-flex h-8 w-8 items-center justify-center rounded-[10px] transition-colors ${
          active ? "bg-white text-dark shadow-sm" : "text-muted hover:text-dark"
        }`}
      >
        <Icon className="h-4 w-4" />
      </button>
    );
  };
  return (
    <div className="inline-flex shrink-0 items-center gap-1 rounded-[12px] bg-surfaceSoft p-1">
      {item("pie", PieChart, "Ver como pastel")}
      {item("bar", BarChart3, "Ver como barras")}
    </div>
  );
}

export function QuestionChartCard({ question }: { question: QuestionDescriptive }) {
  const baseType = pickChartType(question);
  const isNumeric = baseType === "numeric";
  const [view, setView] = useState<ChartView>(baseType === "doughnut" ? "pie" : "bar");

  const datum = useMemo(
    () => frequenciesToChartData(question.frequencies, { showPercent: true }),
    [question.frequencies],
  );
  const total = totalFrequency(question.frequencies);
  const colors = useMemo(() => palette(datum.labels.length), [datum.labels.length]);

  const title = question.label || question.code || "Pregunta";

  const header = (
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <h3 className="text-base font-medium leading-snug text-dark" title={title}>
          {title}
        </h3>
        <p className="mt-1 text-sm text-muted">
          {question.valid_n} respuestas
          {question.missing_n > 0 ? ` · ${question.missing_n} sin responder` : ""}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {question.code ? (
          <span className="rounded-full bg-surfaceSoft px-2.5 py-1 text-[11px] font-medium text-muted">
            {question.code}
          </span>
        ) : null}
        {!isNumeric && total > 0 ? <ViewToggle view={view} onChange={setView} /> : null}
      </div>
    </div>
  );

  let chart: React.ReactNode = null;
  let table: React.ReactNode = null;

  if (isNumeric) {
    chart = <NumericSummary question={question} />;
  } else if (total === 0) {
    chart = (
      <div className="flex h-[140px] items-center justify-center rounded-[12px] border border-dashed border-border text-xs text-muted">
        Sin respuestas aún
      </div>
    );
  } else {
    table = <FrequencyTable labels={datum.labels} colors={colors} values={datum.values} total={total} />;

    if (view === "pie") {
      const data: ChartData<"pie"> = {
        labels: datum.labels,
        datasets: [
          {
            data: datum.values,
            backgroundColor: colors,
            borderColor: "#FFFFFF",
            borderWidth: 2,
            hoverOffset: 6,
          },
        ],
      };
      const options: ChartOptions<"pie"> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `  ${datum.captions[ctx.dataIndex] ?? ctx.formattedValue}`,
            },
          },
        },
      };
      chart = (
        <div className="mx-auto h-[140px] w-[140px]">
          <Pie data={data} options={options} />
        </div>
      );
    } else {
      // Barras: horizontales si hay muchas categorías (etiquetas largas), verticales si son pocas.
      const horizontal = datum.labels.length > 6;
      const data: ChartData<"bar"> = {
        labels: datum.labels,
        datasets: [
          {
            data: datum.values,
            backgroundColor: colors,
            borderRadius: 6,
            maxBarThickness: 28,
          },
        ],
      };
      const options: ChartOptions<"bar"> = {
        indexAxis: horizontal ? "y" : "x",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `  ${datum.captions[ctx.dataIndex] ?? ctx.formattedValue}`,
            },
          },
        },
        scales: {
          x: {
            grid: { display: horizontal },
            ticks: horizontal ? { precision: 0 } : { autoSkip: false, maxRotation: 0, minRotation: 0, font: { size: 10 } },
          },
          y: {
            grid: { display: !horizontal },
            ticks: horizontal ? { font: { size: 10 } } : { precision: 0 },
            beginAtZero: true,
          },
        },
      };
      chart = (
        <div className="h-[150px]">
          <Bar data={data} options={options} />
        </div>
      );
    }
  }

  return (
    <section className="rounded-[18px] border border-border bg-white px-4 py-4 shadow-card">
      {header}
      <div className="mt-4">{chart}</div>
      {table ? <div className="mt-3">{table}</div> : null}
    </section>
  );
}
