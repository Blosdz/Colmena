import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, FileBarChart2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { listProjectForms } from "../api/forms";
import { getProject } from "../api/projects";
import {
  exportReportChartsZip,
  getCorrelationsByVariable,
  getNormalityByVariable,
  getReliabilityByDimension,
  getReliabilityByInstrument,
  runPairCorrelation,
  type CorrelationMatrixCell,
  type CorrelationMatrixReport,
  type CorrelationMethod,
  type NormalityMethod,
  type NormalityReport,
  type NormalityTestResult,
  type ReliabilityReport,
  type ReliabilityTarget,
} from "../api/reports";
import { PageHeader } from "../components/layout/PageHeader";
import { AlphaBarChart } from "../components/reports/AlphaBarChart";
import { CorrelationScatterChart } from "../components/reports/CorrelationScatterChart";
import { NormalityHistogramCard } from "../components/reports/NormalityHistogramCard";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { LoadingState } from "../components/ui/LoadingState";
import { Select, SelectOption } from "../components/ui/Select";

const ALPHA_CLASSIFICATION_LABELS: Record<string, string> = {
  excelente: "Excelente",
  bueno: "Bueno",
  aceptable: "Aceptable",
  cuestionable: "Cuestionable",
  pobre: "Pobre",
  inaceptable: "Inaceptable",
};

const NORMALITY_METHOD_LABELS: Record<string, string> = {
  shapiro: "Shapiro-Wilk",
  lilliefors: "Kolmogorov-Smirnov (Lilliefors)",
  dagostino: "D'Agostino-Pearson",
};

function formatNumber(value: number | null | undefined, decimals = 3): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(decimals);
}

function formatPValue(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (value < 0.001) return "< .001";
  return value.toFixed(3);
}

function alphaToneClass(alpha: number | null): string {
  if (alpha === null) return "text-muted";
  if (alpha >= 0.8) return "text-success";
  if (alpha >= 0.7) return "text-dark";
  return "text-danger";
}

function getPrimaryForm<T extends { status: string }>(forms: T[]) {
  return forms.find((form) => form.status === "published") ?? forms[0] ?? null;
}

// ---------- Módulo 1: Alfa de Cronbach ----------

function ReliabilityRows({ label, targets }: { label: string; targets: ReliabilityTarget[] }) {
  if (targets.length === 0) return null;
  return (
    <>
      <tr>
        <td
          className="bg-surfaceSoft/60 px-4 py-1.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-muted"
          colSpan={5}
        >
          {label}
        </td>
      </tr>
      {targets.map((target) => (
        <tr key={target.target_id}>
          <td className="px-4 py-2 font-medium text-dark">{target.target_name}</td>
          <td className="px-4 py-2 tabular-nums text-dark">{target.item_count}</td>
          <td className="px-4 py-2 tabular-nums text-dark">{target.result.n_valid_cases}</td>
          <td className={`px-4 py-2 font-semibold tabular-nums ${alphaToneClass(target.result.alpha)}`}>
            {formatNumber(target.result.alpha)}
          </td>
          <td className="px-4 py-2 text-dark">
            {ALPHA_CLASSIFICATION_LABELS[target.result.classification] ?? target.result.classification}
          </td>
        </tr>
      ))}
    </>
  );
}

function CronbachSection({
  variableReport,
  dimensionReport,
}: {
  variableReport: ReliabilityReport;
  dimensionReport: ReliabilityReport;
}) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold text-dark">Alfa de Cronbach</h2>
        <p className="text-sm text-muted">
          Consistencia interna de cada variable (todos sus ítems juntos) y de cada dimensión (solo sus
          ítems). Se requieren al menos 2 ítems por conjunto.
        </p>
      </div>
      <div className="overflow-hidden rounded-[18px] border border-border bg-white shadow-card">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-surfaceSoft text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">
                <th className="px-4 py-2.5">Variable / Dimensión</th>
                <th className="w-28 px-4 py-2.5">N° de ítems</th>
                <th className="w-28 px-4 py-2.5">Casos válidos</th>
                <th className="w-36 px-4 py-2.5">Alfa de Cronbach</th>
                <th className="w-40 px-4 py-2.5">Interpretación</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <ReliabilityRows label="Variables" targets={variableReport.results} />
              <ReliabilityRows label="Dimensiones" targets={dimensionReport.results} />
            </tbody>
          </table>
        </div>
        <div className="border-t border-border bg-surfaceSoft/60 px-4 py-2 text-[11px] text-muted">
          α ≥ 0.9 Excelente · 0.8–0.9 Bueno · 0.7–0.8 Aceptable · 0.6–0.7 Cuestionable · &lt; 0.6
          Inaceptable. Esta prueba mide consistencia interna, no correlación entre variables distintas.
        </div>
      </div>
      <AlphaBarChart
        variableTargets={variableReport.results}
        dimensionTargets={dimensionReport.results}
      />
    </section>
  );
}

// ---------- Módulo 2: Pruebas de Normalidad ----------

function normalityDecision(result: NormalityTestResult): { text: string; tone: string } {
  if (result.classification === "normal") return { text: "Normal → Pearson", tone: "text-success" };
  if (result.classification === "non_normal") return { text: "No normal → Spearman", tone: "text-danger" };
  return { text: "No concluyente", tone: "text-muted" };
}

function NormalityRows({ label, results }: { label: string; results: NormalityTestResult[] }) {
  if (results.length === 0) return null;
  return (
    <>
      <tr>
        <td
          className="bg-surfaceSoft/60 px-4 py-1.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-muted"
          colSpan={6}
        >
          {label}
        </td>
      </tr>
      {results.map((result) => {
        const decision = normalityDecision(result);
        return (
          <tr key={result.target_id}>
            <td className="px-4 py-2 font-medium text-dark">{result.target_name}</td>
            <td className="px-4 py-2 text-dark">
              {NORMALITY_METHOD_LABELS[result.method] ?? result.method}
            </td>
            <td className="px-4 py-2 tabular-nums text-dark">{result.valid_n}</td>
            <td className="px-4 py-2 tabular-nums text-dark">{formatNumber(result.statistic)}</td>
            <td className="px-4 py-2 tabular-nums text-dark">{formatPValue(result.p_value)}</td>
            <td className={`px-4 py-2 font-semibold ${decision.tone}`}>{decision.text}</td>
          </tr>
        );
      })}
    </>
  );
}

function NormalitySection({
  formId,
  method,
  onMethodChange,
  variableReport,
}: {
  formId: string;
  method: NormalityMethod;
  onMethodChange: (method: NormalityMethod) => void;
  variableReport: NormalityReport;
}) {
  const chartableResults = variableReport.results.filter((result) => result.valid_n >= 5);
  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-dark">Pruebas de normalidad</h2>
          <p className="text-sm text-muted">
            Se aplica sobre el puntaje agregado por participante (suma de ítems), nunca sobre las
            preguntas individuales. La decisión orienta la elección entre Pearson y Spearman.
          </p>
        </div>
        <Select
          aria-label="Prueba de normalidad"
          className="!h-9 !text-sm"
          value={method}
          onChange={(event) => onMethodChange(event.target.value as NormalityMethod)}
        >
          <SelectOption value="auto">Automático (n ≤ 50 → Shapiro-Wilk; n &gt; 50 → K-S)</SelectOption>
          <SelectOption value="shapiro">Shapiro-Wilk</SelectOption>
          <SelectOption value="lilliefors">Kolmogorov-Smirnov (Lilliefors)</SelectOption>
        </Select>
      </div>
      <div className="overflow-hidden rounded-[18px] border border-border bg-white shadow-card">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-surfaceSoft text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">
                <th className="px-4 py-2.5">Variable / Dimensión</th>
                <th className="w-56 px-4 py-2.5">Prueba aplicada</th>
                <th className="w-20 px-4 py-2.5">n</th>
                <th className="w-28 px-4 py-2.5">Estadístico</th>
                <th className="w-24 px-4 py-2.5">p</th>
                <th className="w-48 px-4 py-2.5">Decisión</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <NormalityRows label="Variables" results={variableReport.results} />
            </tbody>
          </table>
        </div>
        <div className="border-t border-border bg-surfaceSoft/60 px-4 py-2 text-[11px] text-muted">
          p &gt; {variableReport.alpha} → no se rechaza la normalidad (distribución normal) · p ≤{" "}
          {variableReport.alpha} → distribución no normal.
        </div>
      </div>
      {chartableResults.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {chartableResults.map((result) => (
            <NormalityHistogramCard
              key={`${result.target_type}-${result.target_id}`}
              formId={formId}
              result={result}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

// ---------- Módulo 3: Correlaciones (Spearman / Pearson / Kendall) ----------

const CORRELATION_METHOD_LABELS: Record<string, string> = {
  pearson: "Pearson (r)",
  spearman: "Spearman (ρ)",
  kendall: "Kendall (τ)",
  point_biserial: "Punto-biserial",
  not_applicable: "No aplicable",
};

const CORRELATION_MAGNITUDE_LABELS: Record<string, string> = {
  very_weak: "Muy débil",
  weak: "Débil",
  moderate: "Moderada",
  strong: "Fuerte",
  very_strong: "Muy fuerte",
  not_applicable: "No aplicable",
};

function correlationDirection(coefficient: number | null): { text: string; tone: string } {
  if (coefficient === null || Number.isNaN(coefficient)) return { text: "—", tone: "text-muted" };
  if (Math.abs(coefficient) < 1e-12) return { text: "Sin relación", tone: "text-muted" };
  return coefficient > 0
    ? { text: "Positiva", tone: "text-success" }
    : { text: "Negativa", tone: "text-danger" };
}

function correlationSignificance(value: string, alpha: number): { text: string; tone: string } {
  if (value === "statistically_significant") {
    return { text: `Significativa (p < ${alpha})`, tone: "text-success" };
  }
  if (value === "not_statistically_significant") return { text: "No significativa", tone: "text-muted" };
  return { text: "No aplicable", tone: "text-muted" };
}

function uniqueCorrelationPairs(report: CorrelationMatrixReport): CorrelationMatrixCell[] {
  const order = new Map(report.targets.map((target, index) => [target.target_id, index]));
  return report.cells.filter((cell) => {
    const rowIndex = order.get(cell.row_target_id) ?? -1;
    const columnIndex = order.get(cell.column_target_id) ?? -1;
    return rowIndex >= 0 && columnIndex >= 0 && rowIndex < columnIndex;
  });
}

function CorrelationPairExplorer({
  formId,
  method,
  report,
}: {
  formId: string;
  method: CorrelationMethod;
  report: CorrelationMatrixReport;
}) {
  const targets = report.targets;
  const [xTargetId, setXTargetId] = useState(targets[0]?.target_id ?? "");
  const [yTargetId, setYTargetId] = useState(targets[1]?.target_id ?? "");

  const xLabel = targets.find((target) => target.target_id === xTargetId)?.label ?? "";
  const yLabel = targets.find((target) => target.target_id === yTargetId)?.label ?? "";
  const samePair = Boolean(xTargetId) && xTargetId === yTargetId;

  const pairQuery = useQuery({
    queryKey: ["project-reports-correlation-explorer", formId, xTargetId, yTargetId, method],
    queryFn: () =>
      runPairCorrelation(formId, {
        x: { target_type: "project_variable", target_id: xTargetId },
        y: { target_type: "project_variable", target_id: yTargetId },
        method,
      }),
    enabled: Boolean(formId && xTargetId && yTargetId) && !samePair,
  });

  const pairResult = pairQuery.data?.result;

  return (
    <div className="space-y-3">
      <div className="rounded-[18px] border border-border bg-white p-4 shadow-card">
        <h3 className="mb-3 text-sm font-semibold text-dark">Explorar un par de variables</h3>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">
              Variable X
            </label>
            <Select
              aria-label="Variable X"
              className="!h-9 !text-sm"
              value={xTargetId}
              onChange={(event) => setXTargetId(event.target.value)}
            >
              {targets.map((target) => (
                <SelectOption key={target.target_id} value={target.target_id}>
                  {target.label}
                </SelectOption>
              ))}
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">
              Variable Y
            </label>
            <Select
              aria-label="Variable Y"
              className="!h-9 !text-sm"
              value={yTargetId}
              onChange={(event) => setYTargetId(event.target.value)}
            >
              {targets.map((target) => (
                <SelectOption key={target.target_id} value={target.target_id}>
                  {target.label}
                </SelectOption>
              ))}
            </Select>
          </div>
        </div>
      </div>
      {samePair ? (
        <div className="rounded-[18px] border border-border bg-white px-4 py-8 text-center text-sm text-muted shadow-card">
          Elige dos variables distintas para calcular la correlación.
        </div>
      ) : pairQuery.isLoading ? (
        <div className="rounded-[18px] border border-border bg-white px-4 py-8 text-center text-sm text-muted shadow-card">
          Calculando correlación...
        </div>
      ) : pairResult && pairResult.x_values && pairResult.y_values ? (
        <CorrelationScatterChart
          xLabel={xLabel}
          yLabel={yLabel}
          xValues={pairResult.x_values}
          yValues={pairResult.y_values}
          coefficient={pairResult.coefficient}
          pValue={pairResult.p_value}
          method={pairResult.method_used}
          alpha={report.alpha}
        />
      ) : (
        <div className="rounded-[18px] border border-border bg-white px-4 py-8 text-center text-sm text-muted shadow-card">
          Sin datos suficientes para graficar este par.
        </div>
      )}
    </div>
  );
}

function CorrelationSection({
  formId,
  method,
  onMethodChange,
  report,
  isLoading,
  isError,
}: {
  formId: string;
  method: CorrelationMethod;
  onMethodChange: (method: CorrelationMethod) => void;
  report: CorrelationMatrixReport | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  const pairs = report ? uniqueCorrelationPairs(report) : [];

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-dark">Correlaciones entre variables</h2>
          <p className="text-sm text-muted">
            Mide si dos variables cambian juntas y en qué dirección, a partir del puntaje agregado por
            participante. Cuando la prueba de normalidad indica que los datos no son normales, corresponde
            usar Spearman en lugar de Pearson.
          </p>
        </div>
        <Select
          aria-label="Método de correlación"
          className="!h-9 !text-sm"
          value={method}
          onChange={(event) => onMethodChange(event.target.value as CorrelationMethod)}
        >
          <SelectOption value="auto">Automático (según normalidad)</SelectOption>
          <SelectOption value="spearman">Spearman (ρ)</SelectOption>
          <SelectOption value="pearson">Pearson (r)</SelectOption>
          <SelectOption value="kendall">Kendall (τ)</SelectOption>
        </Select>
      </div>
      {report && report.targets.length > 1 ? (
        <CorrelationPairExplorer formId={formId} method={method} report={report} />
      ) : null}
      {isLoading ? (
        <div className="rounded-[18px] border border-border bg-white px-4 py-8 text-center text-sm text-muted shadow-card">
          Calculando correlaciones...
        </div>
      ) : isError || !report || pairs.length === 0 ? (
        <div className="rounded-[18px] border border-border bg-white px-4 py-8 text-center text-sm text-muted shadow-card">
          Se necesitan al menos dos variables del proyecto con puntaje calculado para estimar correlaciones.
        </div>
      ) : (
        <div className="overflow-hidden rounded-[18px] border border-border bg-white shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border bg-surfaceSoft text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">
                  <th className="px-4 py-2.5">Par de variables</th>
                  <th className="w-40 px-4 py-2.5">Método aplicado</th>
                  <th className="w-16 px-4 py-2.5">n</th>
                  <th className="w-24 px-4 py-2.5">Coeficiente</th>
                  <th className="w-20 px-4 py-2.5">p</th>
                  <th className="w-28 px-4 py-2.5">Dirección</th>
                  <th className="w-28 px-4 py-2.5">Magnitud</th>
                  <th className="w-48 px-4 py-2.5">Significancia</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {pairs.map((cell) => {
                  const direction = correlationDirection(cell.coefficient);
                  const significance = correlationSignificance(cell.significance, report.alpha);
                  return (
                    <tr key={`${cell.row_target_id}-${cell.column_target_id}`}>
                      <td className="px-4 py-2 font-medium text-dark">
                        {cell.row_label} – {cell.column_label}
                      </td>
                      <td className="px-4 py-2 text-dark">
                        {CORRELATION_METHOD_LABELS[cell.method_used] ?? cell.method_used}
                      </td>
                      <td className="px-4 py-2 tabular-nums text-dark">{cell.valid_n}</td>
                      <td className="px-4 py-2 font-semibold tabular-nums text-dark">
                        {formatNumber(cell.coefficient)}
                      </td>
                      <td className="px-4 py-2 tabular-nums text-dark">{formatPValue(cell.p_value)}</td>
                      <td className={`px-4 py-2 font-semibold ${direction.tone}`}>{direction.text}</td>
                      <td className="px-4 py-2 text-dark">
                        {CORRELATION_MAGNITUDE_LABELS[cell.magnitude] ?? cell.magnitude}
                      </td>
                      <td className={`px-4 py-2 font-semibold ${significance.tone}`}>{significance.text}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="border-t border-border bg-surfaceSoft/60 px-4 py-2 text-[11px] text-muted">
            Escala de interpretación: 0.00–0.19 muy débil · 0.20–0.39 débil · 0.40–0.59 moderada · 0.60–0.79
            fuerte · 0.80–1.00 muy fuerte. p &lt; {report.alpha} → correlación estadísticamente significativa.
            La correlación no implica causalidad.
          </div>
        </div>
      )}
    </section>
  );
}

// ---------- Página ----------

export function ProjectReportsPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const [normalityMethod, setNormalityMethod] = useState<NormalityMethod>("auto");
  const [correlationMethod, setCorrelationMethod] = useState<CorrelationMethod>("auto");

  const projectQuery = useQuery({
    queryKey: ["project-reports-project", projectId],
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });
  const formsQuery = useQuery({
    queryKey: ["project-reports-forms", projectId],
    queryFn: () => listProjectForms(projectId),
    enabled: Boolean(projectId),
  });

  const primaryForm = getPrimaryForm(formsQuery.data?.items ?? []);
  const formId = primaryForm?.id ?? "";

  const reliabilityVariablesQuery = useQuery({
    queryKey: ["project-reports-reliability-variables", formId],
    queryFn: () => getReliabilityByInstrument(formId),
    enabled: Boolean(formId),
  });
  const reliabilityDimensionsQuery = useQuery({
    queryKey: ["project-reports-reliability-dimensions", formId],
    queryFn: () => getReliabilityByDimension(formId),
    enabled: Boolean(formId),
  });
  const normalityVariablesQuery = useQuery({
    queryKey: ["project-reports-normality-variables", formId, normalityMethod],
    queryFn: () => getNormalityByVariable(formId, normalityMethod),
    enabled: Boolean(formId),
  });
  const correlationVariablesQuery = useQuery({
    queryKey: ["project-reports-correlations-variables", formId, correlationMethod],
    queryFn: () => getCorrelationsByVariable(formId, correlationMethod),
    enabled: Boolean(formId),
    retry: false,
  });

  const exportChartsMutation = useMutation({
    mutationFn: async () => {
      const blob = await exportReportChartsZip(formId, correlationMethod);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `reportes-graficas-${formId}.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    },
  });

  if (projectQuery.isLoading || formsQuery.isLoading) {
    return <LoadingState label="Cargando reportes..." />;
  }

  if (projectQuery.isError || formsQuery.isError || !projectQuery.data || !primaryForm) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader
          title="Reportes"
          description="Alfa de Cronbach y pruebas de normalidad del instrumento."
        />
        <div className="mt-6 flex flex-1 flex-col items-center justify-center rounded-[24px] border border-dashed border-border bg-white px-6 py-16 text-center shadow-card">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber/10 text-amber">
            <FileBarChart2 className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold text-dark">Aún no hay formulario</h3>
          <p className="mt-2 max-w-md text-sm text-muted">
            Crea el instrumento del proyecto y recolecta respuestas para generar los reportes
            estadísticos.
          </p>
          <Link className="colmena-button-primary mt-5 inline-flex items-center" to={`/project/${projectId}`}>
            Ir al constructor
          </Link>
        </div>
      </div>
    );
  }

  const reportsLoading =
    reliabilityVariablesQuery.isLoading ||
    reliabilityDimensionsQuery.isLoading ||
    normalityVariablesQuery.isLoading;
  if (reportsLoading) {
    return <LoadingState label="Calculando estadísticos..." />;
  }

  const reportsError =
    reliabilityVariablesQuery.isError ||
    reliabilityDimensionsQuery.isError ||
    normalityVariablesQuery.isError;
  if (
    reportsError ||
    !reliabilityVariablesQuery.data ||
    !reliabilityDimensionsQuery.data ||
    !normalityVariablesQuery.data
  ) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Reportes"
          description="Alfa de Cronbach y pruebas de normalidad del instrumento."
        />
        <div className="rounded-[18px] border border-border bg-white px-4 py-8 text-center text-sm text-muted shadow-card">
          No se pudieron calcular los reportes. Verifica que el formulario tenga respuestas registradas.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Reportes"
        description="Consistencia interna (Alfa de Cronbach), normalidad y correlaciones de los puntajes, por variable y por dimensión."
        actions={
          <button
            className="colmena-button-secondary inline-flex items-center justify-center"
            disabled={exportChartsMutation.isPending}
            onClick={() => exportChartsMutation.mutate()}
            type="button"
          >
            <Download className="mr-2 h-4 w-4" />
            {exportChartsMutation.isPending ? "Generando gráficas..." : "Exportar gráficas"}
          </button>
        }
      />
      {exportChartsMutation.isError ? (
        <p className="text-sm text-danger">
          No se pudieron generar las gráficas. Verifica que existan al menos 5 casos válidos por variable.
        </p>
      ) : null}
      <CronbachSection
        variableReport={reliabilityVariablesQuery.data}
        dimensionReport={reliabilityDimensionsQuery.data}
      />
      <NormalitySection
        formId={formId}
        method={normalityMethod}
        onMethodChange={setNormalityMethod}
        variableReport={normalityVariablesQuery.data}
      />
      <CorrelationSection
        formId={formId}
        method={correlationMethod}
        onMethodChange={setCorrelationMethod}
        report={correlationVariablesQuery.data}
        isLoading={correlationVariablesQuery.isLoading}
        isError={correlationVariablesQuery.isError}
      />
    </div>
  );
}
