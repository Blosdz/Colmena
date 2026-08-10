import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Clock3, Download, Pause, Play, RefreshCw } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { getDescriptiveOverview, getDescriptives } from "../api/descriptives";
import { exportExcel } from "../api/datasets";
import { listProjectForms } from "../api/forms";
import { getProject } from "../api/projects";
import { PageHeader } from "../components/layout/PageHeader";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { ResponsesDatabaseView } from "../components/telemetry/ResponsesDatabaseView";
import { TelemetryChartsGrid } from "../components/telemetry/TelemetryChartsGrid";
import { ALL_QUESTIONS_KEY, TelemetryGroupSelector } from "../components/telemetry/TelemetryGroupSelector";
import { useTelemetrySocket } from "../components/telemetry/useTelemetrySocket";
import { LoadingState } from "../components/ui/LoadingState";
import { formatDate } from "../utils/formatters";

const POLL_MS = 8000;

function getPrimaryForm<T extends { status: string }>(forms: T[]) {
  return forms.find((form) => form.status === "published") ?? forms[0] ?? null;
}

/** Indicador de auto-actualización: punto pulsante, última hora y controles. */
function LiveIndicator({
  live,
  realtime,
  lastUpdatedAt,
  isFetching,
  onToggle,
  onRefresh,
}: {
  live: boolean;
  realtime: boolean;
  lastUpdatedAt: number;
  isFetching: boolean;
  onToggle: () => void;
  onRefresh: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="inline-flex items-center gap-2 rounded-full bg-surfaceSoft px-3 py-1.5 text-xs font-medium text-muted">
        <span className="relative flex h-2.5 w-2.5">
          {live ? (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
          ) : null}
          <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${live ? "bg-success" : "bg-muted"}`} />
        </span>
        {live ? (realtime ? "En vivo · tiempo real" : "En vivo · sondeo") : "Pausado"}
        {lastUpdatedAt ? <span className="text-muted/70">· {formatDate(new Date(lastUpdatedAt).toISOString())}</span> : null}
      </span>
      <button
        className="colmena-button-secondary inline-flex items-center justify-center"
        onClick={onToggle}
        type="button"
      >
        {live ? <Pause className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
        {live ? "Pausar" : "Reanudar"}
      </button>
      <button
        className="colmena-button-secondary inline-flex items-center justify-center"
        onClick={onRefresh}
        type="button"
      >
        <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
        Actualizar
      </button>
    </div>
  );
}

export function ProjectTelemetryPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const [live, setLive] = useState(true);
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const queryClient = useQueryClient();

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

  // Tiempo real por WebSocket: al llegar una respuesta se invalidan las queries
  // de telemetría. El polling de 8 s queda solo como respaldo si el socket cae.
  const wsConnected = useTelemetrySocket(primaryForm?.id, live, () => {
    queryClient.invalidateQueries({
      predicate: (query) => String(query.queryKey[0]).startsWith("project-telemetry-"),
    });
  });
  const refetchInterval = live && !wsConnected ? POLL_MS : (false as const);

  const overviewQuery = useQuery({
    queryKey: ["project-telemetry-overview", primaryForm?.id],
    queryFn: () => getDescriptiveOverview(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
    refetchInterval,
    refetchIntervalInBackground: false,
  });
  const descriptivesQuery = useQuery({
    queryKey: ["project-telemetry-descriptives", primaryForm?.id],
    queryFn: () => getDescriptives(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
    refetchInterval,
    refetchIntervalInBackground: false,
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
        <PageHeader title="Respuestas" description="Resumen en vivo de las respuestas por pregunta." />

        <div className="flex-1 flex flex-col items-center justify-center mt-6 rounded-[24px] border border-[#E6E8EB] bg-white p-12 text-center shadow-sm">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-amber/10 text-amber mb-6">
            <Activity className="h-10 w-10" />
          </div>
          <h2 className="text-2xl font-bold text-dark mb-2">Aún no hay respuestas</h2>
          <p className="text-muted max-w-md mb-8 leading-relaxed">
            Tu instrumento está listo, pero necesitas compartirlo con tus participantes para empezar a recibir datos.
            Una vez que ingresen respuestas, verás los gráficos de cada pregunta aquí.
          </p>
          <div className="flex gap-4">
            <Link className="colmena-button-secondary" to={`/project/${projectId}/form`}>
              Revisar formulario
            </Link>
            <Link className="colmena-button-primary" to={`/project/${projectId}/link`}>
              Publicar link de encuesta
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (overviewQuery.isLoading || descriptivesQuery.isLoading) {
    return <LoadingState label="Cargando base de respuestas..." />;
  }

  if (overviewQuery.isError || descriptivesQuery.isError) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader title="Respuestas" description="Resumen en vivo de las respuestas por pregunta." />

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
            <Link className="colmena-button-secondary" to={`/project/${projectId}/link`}>
              Ver link
            </Link>
            <button className="colmena-button-primary flex items-center gap-2" onClick={() => descriptivesQuery.refetch()}>
              <Clock3 className="h-4 w-4" /> Actualizar datos
            </button>
          </div>
        </div>
      </div>
    );
  }

  const overview = overviewQuery.data;
  const questions = descriptivesQuery.data?.questions ?? [];
  const dimensions = descriptivesQuery.data?.dimensions ?? [];
  const instruments = descriptivesQuery.data?.instruments ?? [];
  const projectVariables = descriptivesQuery.data?.project_variables ?? [];
  const totalResponses = overview?.total_responses ?? 0;

  const defaultGroup = dimensions[0]
    ? `dimension:${dimensions[0].dimension_id}`
    : projectVariables[0]
      ? `variable:${projectVariables[0].variable_id}`
      : ALL_QUESTIONS_KEY;
  const effectiveGroup = selectedGroup ?? defaultGroup;
  const [groupKind, groupId] = effectiveGroup.split(":");
  const filterKind: "all" | "dimension" | "variable" =
    groupKind === "dimension" ? "dimension" : groupKind === "variable" ? "variable" : "all";
  const filteredQuestions =
    filterKind === "dimension"
      ? questions.filter((question) => question.dimension_id === groupId)
      : filterKind === "variable"
        ? questions.filter((question) => question.project_variable_id === groupId)
        : questions;
  const filterName =
    filterKind === "dimension"
      ? (dimensions.find((dimension) => dimension.dimension_id === groupId)?.name ?? null)
      : filterKind === "variable"
        ? (projectVariables.find((variable) => variable.variable_id === groupId)?.name ?? null)
        : null;

  const lastUpdatedAt = descriptivesQuery.dataUpdatedAt;
  const isFetching = descriptivesQuery.isFetching || overviewQuery.isFetching;

  const refreshAll = () => {
    overviewQuery.refetch();
    descriptivesQuery.refetch();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Respuestas"
        description={`${totalResponses} ${totalResponses === 1 ? "respuesta" : "respuestas"} · resumen en vivo por pregunta.`}
        actions={
          <button
            className="colmena-button-secondary inline-flex items-center justify-center"
            disabled={exportMutation.isPending}
            onClick={() => exportMutation.mutate()}
            type="button"
          >
            <Download className="mr-2 h-4 w-4" />
            {exportMutation.isPending ? "Generando Excel..." : "Exportar Excel"}
          </button>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <TelemetryGroupSelector
          dimensions={dimensions}
          instruments={instruments}
          projectVariables={projectVariables}
          value={effectiveGroup}
          onChange={setSelectedGroup}
        />
        <LiveIndicator
          live={live}
          realtime={wsConnected}
          lastUpdatedAt={lastUpdatedAt}
          isFetching={isFetching}
          onToggle={() => setLive((prev) => !prev)}
          onRefresh={refreshAll}
        />
      </div>

      <TelemetryChartsGrid questions={filteredQuestions} formId={primaryForm.id} />

      <div className="space-y-3">
        <div>
          <h2 className="text-lg font-semibold text-dark">Base de datos de respuestas</h2>
          <p className="text-sm text-muted">
            Cada fila es una respuesta; las columnas se agrupan por dimensión
            {filterName ? ` · filtrado por "${filterName}"` : ""}.
          </p>
        </div>
        <ResponsesDatabaseView formId={primaryForm.id} filterKind={filterKind} filterName={filterName} />
      </div>
    </div>
  );
}
