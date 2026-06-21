import { useMutation, useQuery } from "@tanstack/react-query";
import { Activity, CheckCircle2, Clock3, Download, Search, Users } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { exportExcel, getCompleteness, getDatasetPreview } from "../api/datasets";
import { getPublicLink, listProjectForms, listQuestions, listResponses } from "../api/forms";
import { getProject } from "../api/projects";
import { PageHeader } from "../components/layout/PageHeader";
import { DataTelemetryPanel } from "../components/results/DataTelemetryPanel";
import { type ResponseKpiCardConfig, ResponseKpiGridCards } from "../components/results/ResponseKpiGrid";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { LoadingState } from "../components/ui/LoadingState";
import { formatDate } from "../utils/formatters";

function getPrimaryForm<T extends { status: string }>(forms: T[]) {
  return forms.find((form) => form.status === "published") ?? forms[0] ?? null;
}

function toPercent(value: number) {
  return `${Math.round(value)}%`;
}

export function ProjectTelemetryPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const projectQuery = useQuery({
    queryKey: ["project-telemetry-project", projectId],
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });
  const formsQuery = useQuery({
    queryKey: ["project-telemetry-forms", projectId],
    queryFn: () => listProjectForms(projectId),
    enabled: Boolean(projectId),
  });

  const primaryForm = getPrimaryForm(formsQuery.data?.items ?? []);

  const responsesQuery = useQuery({
    queryKey: ["project-telemetry-responses", primaryForm?.id],
    queryFn: () => listResponses(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const questionsQuery = useQuery({
    queryKey: ["project-telemetry-questions", primaryForm?.id],
    queryFn: () => listQuestions(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const completenessQuery = useQuery({
    queryKey: ["project-telemetry-completeness", primaryForm?.id],
    queryFn: () => getCompleteness(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const datasetPreviewQuery = useQuery({
    queryKey: ["project-telemetry-preview", primaryForm?.id],
    queryFn: () => getDatasetPreview(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const publicLinkQuery = useQuery({
    queryKey: ["project-telemetry-link", primaryForm?.id],
    queryFn: async () => {
      try {
        return await getPublicLink(primaryForm!.id);
      } catch {
        return null;
      }
    },
    enabled: Boolean(primaryForm?.id),
  });
  const exportMutation = useMutation({
    mutationFn: () => exportExcel(primaryForm!.id),
  });

  if (projectQuery.isLoading || formsQuery.isLoading) {
    return <LoadingState label="Cargando telemetría..." />;
  }

  // Si falla la carga del proyecto (ej. mock local) o no hay formulario, mostramos el empty state útil
  if (projectQuery.isError || formsQuery.isError || !projectQuery.data || !primaryForm) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader title="Telemetría de Datos" description="Monitorea la recolección de respuestas en tiempo real." />
        
        <div className="flex-1 flex flex-col items-center justify-center mt-6 rounded-[24px] border border-[#E6E8EB] bg-white p-12 text-center shadow-sm">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-amber/10 text-amber mb-6">
            <Activity className="h-10 w-10" />
          </div>
          <h2 className="text-2xl font-bold text-dark mb-2">Aún no hay respuestas</h2>
          <p className="text-muted max-w-md mb-8 leading-relaxed">
            Tu instrumento está listo, pero necesitas compartirlo con tus participantes para empezar a recibir datos. 
            Una vez que ingresen respuestas, verás métricas de calidad y completitud aquí.
          </p>
          <div className="flex gap-4">
            <Link className="colmena-button-secondary" to={`/project/${projectId}/form`}>
              Revisar formulario
            </Link>
            <button className="colmena-button-primary">
              Publicar link de encuesta
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (responsesQuery.isLoading || questionsQuery.isLoading || completenessQuery.isLoading || datasetPreviewQuery.isLoading) {
    return <LoadingState label="Cargando base de respuestas..." />;
  }

  if (responsesQuery.isError || questionsQuery.isError || completenessQuery.isError || datasetPreviewQuery.isError) {
    // Si fallan las respuestas, mostramos el mismo empty state
    return (
      <div className="flex h-full flex-col">
        <PageHeader title="Telemetría de Datos" description="Monitorea la recolección de respuestas en tiempo real." />
        
        <div className="flex-1 flex flex-col items-center justify-center mt-6 rounded-[24px] border border-[#E6E8EB] bg-white p-12 text-center shadow-sm">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-amber/10 text-amber mb-6">
            <Activity className="h-10 w-10" />
          </div>
          <h2 className="text-2xl font-bold text-dark mb-2">Aún no hay respuestas</h2>
          <p className="text-muted max-w-md mb-8 leading-relaxed">
            El link de la encuesta ya está activo, pero nadie ha respondido todavía.
            Comparte el enlace con tu población de estudio.
          </p>
          <div className="flex gap-4">
            <button className="colmena-button-secondary">
              Copiar link
            </button>
            <button className="colmena-button-primary flex items-center gap-2" onClick={() => responsesQuery.refetch()}>
              <Clock3 className="h-4 w-4" /> Actualizar datos
            </button>
          </div>
        </div>
      </div>
    );
  }

  const responses = responsesQuery.data?.items ?? [];
  const totalQuestions = questionsQuery.data?.items?.length ?? 0;
  const totalResponses = responses.length;
  const validResponses = responses.filter((response) => response.status === "submitted").length;
  const incompleteResponses =
    totalQuestions > 0 ? responses.filter((response) => response.answers.length < totalQuestions).length : 0;
  const completionAverage =
    totalResponses > 0 && totalQuestions > 0
      ? responses.reduce((sum, response) => sum + Math.min(100, (response.answers.length / totalQuestions) * 100), 0) /
        totalResponses
      : 0;
  const latestResponse = responses
    .map((response) => response.submitted_at || response.created_at)
    .filter(Boolean)
    .sort()
    .at(-1);

  const kpis: ResponseKpiCardConfig[] = [
    { title: "Respuestas totales", value: totalResponses, delta: "base actual", hint: "captura del formulario", icon: Users },
    { title: "Respuestas válidas", value: validResponses, delta: "listas para lectura", hint: "envíos completos", icon: CheckCircle2 },
    { title: "Incompletas", value: incompleteResponses, delta: incompleteResponses > 0 ? "revisar" : "sin alertas", hint: "requieren seguimiento", icon: Activity },
    { title: "Completitud promedio", value: toPercent(completionAverage), delta: "sobre ítems", hint: "promedio de avance", icon: Clock3 },
    { title: "Última respuesta", value: latestResponse ? formatDate(latestResponse) : "Sin datos", delta: "captura reciente", hint: publicLinkQuery.data?.public_url ? "link activo" : "sin link", icon: Users },
  ];

  const omissionLeader = (completenessQuery.data?.items ?? [])
    .slice()
    .sort((left, right) => right.missing_percent - left.missing_percent)
    .slice(0, 2)
    .map((item) => `${item.label} (${item.missing_percent.toFixed(1)}%)`)
    .join(" · ");

  return (
    <div className="space-y-8">
      <PageHeader
        title="Telemetría"
        description="Aquí se revisa completitud, omisiones, registros válidos y la calidad general de la base."
        actions={
          <div className="flex flex-wrap gap-3">
            <Link className="colmena-button-secondary inline-flex items-center justify-center" to={`/project/${projectId}/link`}>
              Ver link y respuestas
            </Link>
            <Link className="colmena-button-secondary inline-flex items-center justify-center" to={`/project/${projectId}/results`}>
              Calcular resultados
            </Link>
            <button className="colmena-button-secondary inline-flex items-center justify-center" disabled={exportMutation.isPending} onClick={() => exportMutation.mutate()} type="button">
              <Download className="mr-2 h-4 w-4" />
              {exportMutation.isPending ? "Generando Excel..." : "Exportar Excel"}
            </button>
          </div>
        }
      />

      <ResponseKpiGridCards cards={kpis} />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-5">
          <section className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-dark">Tabla de respuestas</h2>
              <div className="flex h-11 min-w-[240px] items-center gap-3 rounded-[18px] border border-border px-4">
                <Search className="h-4 w-4 text-muted" />
                <span className="text-sm text-muted">Buscar por código o fecha...</span>
              </div>
            </div>

            <div className="mt-5 overflow-hidden rounded-[20px] border border-border">
              <div className="grid grid-cols-[0.8fr_1fr_0.9fr_0.8fr_0.8fr] gap-4 border-b border-border bg-[#FCFCFB] px-4 py-3 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                <span>ID</span>
                <span>Fecha</span>
                <span>Código</span>
                <span>Estado</span>
                <span>Completitud</span>
              </div>
              <div className="divide-y divide-border">
                {responses.length === 0 ? (
                  <div className="px-4 py-6 text-sm text-muted">Aún no hay respuestas capturadas.</div>
                ) : (
                  responses.slice(0, 10).map((response) => {
                    const completion = totalQuestions > 0 ? Math.min(100, (response.answers.length / totalQuestions) * 100) : 0;
                    return (
                      <div className="grid grid-cols-[0.8fr_1fr_0.9fr_0.8fr_0.8fr] gap-4 px-4 py-4 text-sm" key={response.id}>
                        <span className="text-dark">{response.id.slice(0, 6)}</span>
                        <span className="text-muted">{formatDate(response.submitted_at || response.created_at)}</span>
                        <span className="text-dark">{response.respondent_code || response.id.slice(0, 4)}</span>
                        <span className="text-dark">{response.status}</span>
                        <span className="text-dark">{toPercent(completion)}</span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </section>

          <section className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
            <h2 className="text-lg font-semibold text-dark">Base de respuestas</h2>
            <div className="mt-4 overflow-x-auto rounded-[20px] border border-border">
              <table className="min-w-full divide-y divide-border text-sm">
                <thead className="bg-[#FCFCFB]">
                  <tr>
                    {(datasetPreviewQuery.data?.columns ?? []).slice(0, 6).map((column) => (
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.08em] text-muted" key={column.name}>
                        {column.label || column.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border bg-white">
                  {(datasetPreviewQuery.data?.rows ?? []).slice(0, 6).map((row, index) => (
                    <tr key={index}>
                      {(datasetPreviewQuery.data?.columns ?? []).slice(0, 6).map((column) => (
                        <td className="px-4 py-3 text-dark" key={`${index}-${column.name}`}>
                          {String(row[column.name] ?? "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <DataTelemetryPanel
          items={[
            ["Link publico", publicLinkQuery.data?.public_url ? "Activo" : "Pendiente"],
            ["Total registros", String(totalResponses)],
            ["Registros válidos", String(validResponses)],
            ["Completitud promedio", toPercent(completionAverage)],
            ["Mayor omisión", omissionLeader || "Sin datos suficientes"],
          ]}
          statusLabel={
            totalResponses === 0
              ? "Base en construcción"
              : completionAverage >= 85
                ? "Lista para descriptivos"
                : completionAverage >= 65
                  ? "Requiere limpieza"
                  : "Base en construcción"
          }
          title="Telemetría de calidad"
        />
      </div>
    </div>
  );
}
