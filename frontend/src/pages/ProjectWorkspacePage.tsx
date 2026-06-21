import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getPublicLink, listProjectForms, listResponses } from "../api/forms";
import { getProject, listProjectVariables } from "../api/projects";
import { listControlScales, listScoringConfigs } from "../api/scoring";
import { PageHeader } from "../components/layout/PageHeader";
import { ProjectMissingState } from "../components/study/ProjectMissingState";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PrimaryAction } from "../components/ui/PrimaryAction";
import { cn } from "../utils/cn";

function getPrimaryForm<T extends { status: string }>(forms: T[]) {
  return forms.find((form) => form.status === "published") ?? forms[0] ?? null;
}

function StatusBadge({ status }: { status: "pending" | "in_progress" | "complete" }) {
  const label = status === "complete" ? "Listo" : status === "in_progress" ? "En curso" : "Pendiente";
  return (
    <span
      className={cn(
        "rounded-full px-3 py-1 text-xs font-medium",
        status === "complete" && "bg-[#EAF9EF] text-success",
        status === "in_progress" && "bg-[#FFF6DE] text-[#9A6A00]",
        status === "pending" && "bg-[#F5F6F7] text-muted",
      )}
    >
      {label}
    </span>
  );
}

function ProcessRow({
  title,
  description,
  actionLabel,
  href,
  status,
}: {
  title: string;
  description: string;
  actionLabel: string;
  href: string;
  status: "pending" | "in_progress" | "complete";
}) {
  return (
    <div className="flex flex-col gap-4 rounded-[22px] border border-border bg-white px-5 py-5 md:flex-row md:items-center md:justify-between">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-lg font-semibold text-dark">{title}</h3>
          <StatusBadge status={status} />
        </div>
        <p className="text-sm leading-6 text-muted">{description}</p>
      </div>
      <Link className="colmena-button-secondary inline-flex h-11 items-center justify-center whitespace-nowrap" to={href}>
        {actionLabel}
      </Link>
    </div>
  );
}

export function ProjectWorkspacePage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const projectQuery = useQuery({
    queryKey: ["project-workspace-project", projectId],
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });
  const variablesQuery = useQuery({
    queryKey: ["project-workspace-variables", projectId],
    queryFn: () => listProjectVariables(projectId),
    enabled: Boolean(projectId),
  });
  const formsQuery = useQuery({
    queryKey: ["project-workspace-forms", projectId],
    queryFn: () => listProjectForms(projectId),
    enabled: Boolean(projectId),
  });

  const primaryForm = getPrimaryForm(formsQuery.data?.items ?? []);

  const responsesQuery = useQuery({
    queryKey: ["project-workspace-responses", primaryForm?.id],
    queryFn: () => listResponses(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const scoringConfigsQuery = useQuery({
    queryKey: ["project-workspace-scoring", primaryForm?.id],
    queryFn: () => listScoringConfigs(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const controlScalesQuery = useQuery({
    queryKey: ["project-workspace-control", primaryForm?.id],
    queryFn: () => listControlScales(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const publicLinkQuery = useQuery({
    queryKey: ["project-workspace-public-link", primaryForm?.id],
    queryFn: async () => {
      try {
        return await getPublicLink(primaryForm!.id);
      } catch {
        return null;
      }
    },
    enabled: Boolean(primaryForm?.id),
  });

  if (projectQuery.isLoading || variablesQuery.isLoading || formsQuery.isLoading) {
    return <LoadingState label="Cargando proyecto..." />;
  }

  if (projectQuery.isError || variablesQuery.isError || formsQuery.isError) {
    return <ErrorState message={((projectQuery.error || variablesQuery.error || formsQuery.error) as Error).message} />;
  }

  if (!projectQuery.data) {
    return <ProjectMissingState />;
  }

  const variableCount = variablesQuery.data?.items?.length ?? 0;
  const formCount = formsQuery.data?.items?.length ?? 0;
  const responseCount = responsesQuery.data?.items?.length ?? 0;
  const scoringCount = scoringConfigsQuery.data?.items?.length ?? 0;
  const controlCount = controlScalesQuery.data?.length ?? 0;
  const hasLink = Boolean(publicLinkQuery.data?.public_url);

  const flow = [
    "Proyecto",
    "Variable",
    "Dimensiones",
    "Instrumento",
    "Items",
    "Escala",
    "Baremos",
    "Link",
    "Respuestas",
    "Resultados",
    "Informe",
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={projectQuery.data.title}
        description="Aqui se define la variable, se construye el formulario, se publica el link y se preparan resultados y reportes."
        actions={
          <Link to={`/project/${projectId}/builder`}>
            <PrimaryAction>Editar proyecto</PrimaryAction>
          </Link>
        }
      />

      <section className="rounded-[28px] border border-border bg-white px-7 py-7 shadow-card">
        <h2 className="text-xl font-semibold text-dark">Ruta metodologica</h2>
        <div className="mt-5 flex flex-wrap gap-3">
          {flow.map((step, index) => (
            <span
              className="rounded-[18px] border border-border bg-[#FCFCFB] px-4 py-3 text-sm font-medium text-dark"
              key={step}
            >
              <span className="mr-2 text-[#B47700]">{index + 1}</span>
              {step}
            </span>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-dark">Configuracion del formulario</h2>
          <p className="text-sm text-muted">
            Primero se construye la logica del instrumento: variable, dimensiones, items, escala y baremos.
          </p>
        </div>
        <ProcessRow
          title="Definir variable principal"
          description={variableCount > 0 ? `${variableCount} variable(s) registradas.` : "Registra la variable principal y su definicion."}
          actionLabel="Definir variable"
          href={`/project/${projectId}/builder`}
          status={variableCount > 0 ? "complete" : "in_progress"}
        />
        <ProcessRow
          title="Agregar dimensiones"
          description="Organiza la variable en dimensiones e indicadores antes de cargar preguntas."
          actionLabel="Agregar dimensiones"
          href={`/project/${projectId}/builder`}
          status={variableCount > 0 ? "in_progress" : "pending"}
        />
        <ProcessRow
          title="Crear instrumento e importar items"
          description={formCount > 0 ? "El proyecto ya tiene un formulario asociado." : "Crea el instrumento o pega las preguntas desde una tabla."}
          actionLabel="Crear instrumento"
          href={`/project/${projectId}/builder`}
          status={formCount > 0 ? "in_progress" : "pending"}
        />
        <ProcessRow
          title="Configurar escala y baremos"
          description={scoringCount > 0 ? `${scoringCount} regla(s) de calificacion configuradas.` : "Asigna valores, items invertidos y baremos del instrumento."}
          actionLabel="Configurar baremos"
          href={`/project/${projectId}/builder`}
          status={scoringCount > 0 ? "complete" : formCount > 0 ? "in_progress" : "pending"}
        />
        <ProcessRow
          title="Ajustar escala de control"
          description={controlCount > 0 ? `${controlCount} escala(s) de control activas.` : "Activa esta parte solo si tu instrumento la necesita."}
          actionLabel="Configurar control"
          href={`/project/${projectId}/builder`}
          status={controlCount > 0 ? "complete" : "pending"}
        />
      </section>

      <section className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-dark">Publicacion, respuestas y salida</h2>
          <p className="text-sm text-muted">
            Cuando el formulario esta listo, se genera el link, se reciben respuestas y luego se calculan resultados y reportes.
          </p>
        </div>
        <ProcessRow
          title="Diseño visual y sociodemográfico"
          description="Personaliza la apariencia y agrega variables exógenas como edad o sexo."
          actionLabel="Diseñar formulario"
          href={`/project/${projectId}/form`}
          status={formCount > 0 ? "in_progress" : "pending"}
        />
        <ProcessRow
          title="Publicar link"
          description={hasLink ? "El formulario ya tiene un link publico activo." : "Genera el link externo para que otras personas contesten."}
          actionLabel="Publicar link"
          href={`/project/${projectId}/link`}
          status={hasLink ? "complete" : formCount > 0 ? "in_progress" : "pending"}
        />
        <ProcessRow
          title="Ver respuestas"
          description={responseCount > 0 ? `${responseCount} respuesta(s) registradas.` : "Aqui veras la tabla basica de respuestas recibidas."}
          actionLabel="Ver respuestas"
          href={`/project/${projectId}/link`}
          status={responseCount > 0 ? "complete" : hasLink ? "in_progress" : "pending"}
        />
        <ProcessRow
          title="Revisar telemetria"
          description="Controla completitud, omisiones, registros validos y estado de la base."
          actionLabel="Revisar telemetria"
          href={`/project/${projectId}/telemetry`}
          status={responseCount > 0 ? "in_progress" : "pending"}
        />
        <ProcessRow
          title="Calcular resultados"
          description="Procesa descriptivos, normalidad, comparaciones, scoring y baremos."
          actionLabel="Calcular resultados"
          href={`/project/${projectId}/results`}
          status={responseCount > 0 ? "in_progress" : "pending"}
        />
        <ProcessRow
          title="Generar reporte"
          description="Prepara tablas APA, graficos e informe Word o PDF."
          actionLabel="Generar reporte"
          href={`/project/${projectId}/reports`}
          status={responseCount > 0 ? "in_progress" : "pending"}
        />
      </section>
    </div>
  );
}
