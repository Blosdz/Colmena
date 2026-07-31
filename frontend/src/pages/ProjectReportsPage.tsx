import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileBarChart2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { listProjectForms } from "../api/forms";
import { getProject } from "../api/projects";
import {
  getNormalityByDimension,
  getNormalityByVariable,
  getReliabilityByDimension,
  getReliabilityByInstrument,
  type NormalityMethod,
  type NormalityReport,
  type NormalityTestResult,
  type ReliabilityReport,
  type ReliabilityTarget,
} from "../api/reports";
import { PageHeader } from "../components/layout/PageHeader";
import { AlphaBarChart } from "../components/reports/AlphaBarChart";
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
  dimensionReport,
}: {
  formId: string;
  method: NormalityMethod;
  onMethodChange: (method: NormalityMethod) => void;
  variableReport: NormalityReport;
  dimensionReport: NormalityReport;
}) {
  const chartableResults = [...variableReport.results, ...dimensionReport.results].filter(
    (result) => result.valid_n >= 5,
  );
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
              <NormalityRows label="Dimensiones" results={dimensionReport.results} />
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

// ---------- Página ----------

export function ProjectReportsPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const [normalityMethod, setNormalityMethod] = useState<NormalityMethod>("auto");

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
  const normalityDimensionsQuery = useQuery({
    queryKey: ["project-reports-normality-dimensions", formId, normalityMethod],
    queryFn: () => getNormalityByDimension(formId, normalityMethod),
    enabled: Boolean(formId),
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
    normalityVariablesQuery.isLoading ||
    normalityDimensionsQuery.isLoading;
  if (reportsLoading) {
    return <LoadingState label="Calculando estadísticos..." />;
  }

  const reportsError =
    reliabilityVariablesQuery.isError ||
    reliabilityDimensionsQuery.isError ||
    normalityVariablesQuery.isError ||
    normalityDimensionsQuery.isError;
  if (
    reportsError ||
    !reliabilityVariablesQuery.data ||
    !reliabilityDimensionsQuery.data ||
    !normalityVariablesQuery.data ||
    !normalityDimensionsQuery.data
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
        description="Consistencia interna (Alfa de Cronbach) y normalidad de los puntajes, por variable y por dimensión."
      />
      <CronbachSection
        variableReport={reliabilityVariablesQuery.data}
        dimensionReport={reliabilityDimensionsQuery.data}
      />
      <NormalitySection
        formId={formId}
        method={normalityMethod}
        onMethodChange={setNormalityMethod}
        variableReport={normalityVariablesQuery.data}
        dimensionReport={normalityDimensionsQuery.data}
      />
    </div>
  );
}
