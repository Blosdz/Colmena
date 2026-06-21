import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Layers3, Sigma, SlidersHorizontal } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { listDimensions, listInstruments, listProjectForms, listQuestions } from "../api/forms";
import { getProject, listProjectVariables } from "../api/projects";
import { getScoringResults, listScoringConfigs, runScoring } from "../api/scoring";
import { PageHeader } from "../components/layout/PageHeader";
import { AnalysisRunner } from "../components/results/AnalysisRunner";
import { BaremoSummaryPanel } from "../components/results/BaremoSummaryPanel";
import { DescriptivePanel } from "../components/results/DescriptivePanel";
import { InstrumentStructurePanel } from "../components/results/InstrumentStructurePanel";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PrimaryAction } from "../components/ui/PrimaryAction";

function getPrimaryForm<T extends { status: string }>(forms: T[]) {
  return forms.find((form) => form.status === "published") ?? forms[0] ?? null;
}

const analysisModules = [
  { title: "Descriptivos", description: "Resume promedios, dispersión y distribución básica del instrumento.", icon: BarChart3 },
  { title: "Normalidad", description: "Revisa si la base cumple supuestos básicos para pruebas posteriores.", icon: SlidersHorizontal },
  { title: "Correlaciones y comparaciones", description: "Ejecuta análisis guiados de relación, comparación y asociación.", icon: Sigma },
  { title: "Calificación y baremos", description: "Procesa scoring, ítems invertidos, baremos y escalas de control.", icon: Layers3 },
];

export function ProjectResultsPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);
  const queryClient = useQueryClient();

  const projectQuery = useQuery({
    queryKey: ["project-results-project", projectId],
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });
  const variablesQuery = useQuery({
    queryKey: ["project-results-variables", projectId],
    queryFn: () => listProjectVariables(projectId),
    enabled: Boolean(projectId),
  });
  const formsQuery = useQuery({
    queryKey: ["project-results-forms", projectId],
    queryFn: () => listProjectForms(projectId),
    enabled: Boolean(projectId),
  });

  const primaryForm = getPrimaryForm(formsQuery.data?.items ?? []);

  const instrumentsQuery = useQuery({
    queryKey: ["project-results-instruments", primaryForm?.id],
    queryFn: () => listInstruments(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const firstInstrument = instrumentsQuery.data?.items?.[0] ?? null;
  const dimensionsQuery = useQuery({
    queryKey: ["project-results-dimensions", firstInstrument?.id],
    queryFn: () => listDimensions(firstInstrument!.id),
    enabled: Boolean(firstInstrument?.id),
  });
  const questionsQuery = useQuery({
    queryKey: ["project-results-questions", primaryForm?.id],
    queryFn: () => listQuestions(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const scoringConfigsQuery = useQuery({
    queryKey: ["project-results-scoring-configs", primaryForm?.id],
    queryFn: () => listScoringConfigs(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const scoringResultsQuery = useQuery({
    queryKey: ["project-results-scoring-results", primaryForm?.id],
    queryFn: () => getScoringResults(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });

  const runScoringMutation = useMutation({
    mutationFn: () => runScoring(primaryForm!.id, { include_discarded: false, recalculate: true, store_result: true }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["project-results-scoring-results", primaryForm?.id] });
    },
  });

  if (projectQuery.isLoading || variablesQuery.isLoading || formsQuery.isLoading) {
    return <LoadingState label="Preparando resultados..." />;
  }

  // Si falla la carga del proyecto (mock) o no hay formulario, mostramos el empty state útil
  if (projectQuery.isError || variablesQuery.isError || formsQuery.isError || !projectQuery.data || !primaryForm) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader title="Resultados Estadísticos" description="Procesa descriptivos, normalidad, comparaciones, scoring y baremos del proyecto." />
        
        <div className="flex-1 flex flex-col items-center justify-center mt-6 rounded-[24px] border border-[#E6E8EB] bg-white p-12 text-center shadow-sm">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[#E8FAF9] text-[#0C9897] mb-6">
            <Sigma className="h-10 w-10" />
          </div>
          <h2 className="text-2xl font-bold text-dark mb-2">Primero recolecta respuestas</h2>
          <p className="text-muted max-w-md mb-8 leading-relaxed">
            Para generar análisis estadísticos y calcular baremos, necesitas un conjunto de datos base. 
            Revisa la telemetría para ver cuántas respuestas tienes acumuladas.
          </p>
          <div className="flex gap-4">
            <Link className="colmena-button-secondary" to={`/project/${projectId}/telemetry`}>
              Revisar telemetría
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (instrumentsQuery.isLoading || dimensionsQuery.isLoading || questionsQuery.isLoading || scoringConfigsQuery.isLoading || scoringResultsQuery.isLoading) {
    return <LoadingState label="Cargando módulos de resultados..." />;
  }

  if (instrumentsQuery.isError || dimensionsQuery.isError || questionsQuery.isError || scoringConfigsQuery.isError || scoringResultsQuery.isError) {
    return (
      <ErrorState
        message={((instrumentsQuery.error || dimensionsQuery.error || questionsQuery.error || scoringConfigsQuery.error || scoringResultsQuery.error) as Error).message}
      />
    );
  }

  const variableName = variablesQuery.data?.items?.[0]?.name ?? "Variable principal";
  const dimensions = dimensionsQuery.data?.items ?? [];
  const questions = questionsQuery.data?.items ?? [];
  const scoringConfigs = scoringConfigsQuery.data?.items ?? [];
  const scoringResults = scoringResultsQuery.data;

  const questionCountByDimension = dimensions.map((dimension, index) => ({
    name: dimension.name,
    items: questions.filter((question) => question.dimension_id === dimension.id).length,
    color: ["bg-[#356DFF]", "bg-turquoise", "bg-amber", "bg-[#7C4CE0]", "bg-[#EF5B93]"][index % 5],
  }));

  return (
    <div className="space-y-8">
      <PageHeader
        title="Resultados"
        description="Aquí se procesan descriptivos, normalidad, comparaciones, scoring y baremos del proyecto."
        actions={
          <div className="flex flex-wrap gap-3">
            <PrimaryAction loading={runScoringMutation.isPending} onClick={() => runScoringMutation.mutate()} type="button">
              Calcular resultados
            </PrimaryAction>
            <Link className="colmena-button-secondary inline-flex items-center justify-center" to={`/project/${projectId}/telemetry`}>
              Revisar telemetría
            </Link>
          </div>
        }
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-5">
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {analysisModules.map((module) => (
              <div className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card" key={module.title}>
                <div className="flex h-12 w-12 items-center justify-center rounded-[18px] bg-[#FFF6DE] text-[#9A6A00]">
                  <module.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-dark">{module.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted">{module.description}</p>
              </div>
            ))}
          </section>

          <section className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
            <InstrumentStructurePanel dimensions={questionCountByDimension} variableName={variableName} />
          </section>

          <section className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
            <h2 className="text-lg font-semibold text-dark">Descriptivos del proyecto</h2>
            <div className="mt-4">
              <DescriptivePanel formId={primaryForm.id} />
            </div>
          </section>

          <section className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
            <h2 className="text-lg font-semibold text-dark">Análisis guiado</h2>
            <div className="mt-4">
              <AnalysisRunner formId={primaryForm.id} />
            </div>
          </section>
        </div>

        <BaremoSummaryPanel
          configCount={scoringConfigs.length}
          name={scoringConfigs[0]?.name || "Sin baremos configurados"}
          scaleLabel={
            scoringResults
              ? `${scoringResults.valid_responses} válidas · ${scoringResults.warning_responses} con advertencia`
              : "Aún no se ejecutó la calificación"
          }
        />
      </div>
    </div>
  );
}
