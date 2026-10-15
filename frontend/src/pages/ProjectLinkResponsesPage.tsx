import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, ExternalLink, PauseCircle, PlayCircle, Share2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { closeForm, consolidateProjectForms, getPublicLink, listInstruments, listProjectForms, listResponses, publishForm, reopenForm } from "../api/forms";
import { getProject } from "../api/projects";
import { buildPublicFormUrl } from "../config/env";
import { PageHeader } from "../components/layout/PageHeader";
import { ProjectMissingState } from "../components/study/ProjectMissingState";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PrimaryAction } from "../components/ui/PrimaryAction";
import { formatDate } from "../utils/formatters";

function getPrimaryForm<T extends { status: string }>(forms: T[]) {
  return forms.find((form) => form.status === "published") ?? forms[0] ?? null;
}

async function copyText(value: string) {
  if (!navigator?.clipboard) {
    return;
  }
  await navigator.clipboard.writeText(value);
}

export function ProjectLinkResponsesPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);
  const queryClient = useQueryClient();

  const projectQuery = useQuery({
    queryKey: ["project-link-project", projectId],
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });
  const formsQuery = useQuery({
    queryKey: ["project-link-forms", projectId],
    queryFn: () => listProjectForms(projectId),
    enabled: Boolean(projectId),
  });

  const projectForms = formsQuery.data?.items ?? [];
  const primaryForm = getPrimaryForm(projectForms);
  const requiresConsolidation = projectForms.length > 1;
  const [selectedInstrumentIds, setSelectedInstrumentIds] = useState<string[]>([]);

  const publicLinkQuery = useQuery({
    queryKey: ["project-link-public", primaryForm?.id],
    queryFn: async () => {
      try {
        return await getPublicLink(primaryForm!.id);
      } catch {
        return null;
      }
    },
    enabled: Boolean(primaryForm?.id),
  });
  const responsesQuery = useQuery({
    queryKey: ["project-link-responses", primaryForm?.id],
    queryFn: () => listResponses(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });
  const instrumentsQuery = useQuery({
    queryKey: ["project-link-instruments", primaryForm?.id],
    queryFn: () => listInstruments(primaryForm!.id),
    enabled: Boolean(primaryForm?.id),
  });

  useEffect(() => {
    const instruments = instrumentsQuery.data?.items ?? [];
    if (instruments.length === 0) {
      setSelectedInstrumentIds([]);
      return;
    }
    const availableIds = new Set(instruments.map((instrument) => instrument.id));
    const publishedIds = (publicLinkQuery.data?.published_instrument_ids ?? []).filter((id) =>
      availableIds.has(id),
    );
    setSelectedInstrumentIds(
      publishedIds.length > 0 ? publishedIds : instruments.map((instrument) => instrument.id),
    );
  }, [instrumentsQuery.data, publicLinkQuery.data?.published_instrument_ids]);

  const publishMutation = useMutation({
    mutationFn: async () => {
      const targetForm = requiresConsolidation
        ? await consolidateProjectForms(projectId)
        : primaryForm!;
      if (requiresConsolidation) {
        const consolidatedInstruments = await listInstruments(targetForm.id);
        return publishForm(targetForm.id, consolidatedInstruments.items.map((item) => item.id));
      }
      return publishForm(targetForm.id, selectedInstrumentIds);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["project-link-forms", projectId] }),
        queryClient.invalidateQueries({ queryKey: ["project-link-public", primaryForm?.id] }),
        queryClient.invalidateQueries({ queryKey: ["project-link-responses", primaryForm?.id] }),
      ]);
    },
  });
  const closeMutation = useMutation({
    mutationFn: () => closeForm(primaryForm!.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["project-link-forms", projectId] });
    },
  });
  const reopenMutation = useMutation({
    mutationFn: () => reopenForm(primaryForm!.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["project-link-forms", projectId] });
    },
  });

  if (projectQuery.isLoading || formsQuery.isLoading || instrumentsQuery.isLoading) {
    return <LoadingState label="Preparando link y respuestas..." />;
  }

  if (projectQuery.isError || formsQuery.isError || instrumentsQuery.isError) {
    return <ErrorState message={((projectQuery.error || formsQuery.error || instrumentsQuery.error) as Error).message} />;
  }

  if (!projectQuery.data) {
    return <ProjectMissingState description="No pudimos abrir la publicación de este proyecto." />;
  }

  if (!primaryForm) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Link y respuestas"
          description="Primero necesitas crear el formulario y preparar el instrumento."
        />
        <EmptyState
          title="Aún no hay formulario"
          description="Crea el formulario antes de generar el link público y revisar respuestas."
        />
        <Link className="colmena-button-primary inline-flex items-center justify-center" to={`/project/${projectId}/form`}>
          Crear formulario
        </Link>
      </div>
    );
  }

  if (responsesQuery.isLoading) {
    return <LoadingState label="Cargando respuestas..." />;
  }

  if (responsesQuery.isError) {
    return <ErrorState message={(responsesQuery.error as Error).message} />;
  }

  const frontendPublicUrl = publicLinkQuery.data?.public_slug
    ? buildPublicFormUrl(publicLinkQuery.data.public_slug)
    : "";

  const isPublished = !requiresConsolidation && primaryForm.status === "published" && Boolean(frontendPublicUrl);
  const responses = responsesQuery.data?.items ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Link y respuestas"
        description="Publica el formulario, comparte el link y revisa las respuestas que van llegando."
        actions={
          <Link className="colmena-button-secondary inline-flex items-center justify-center" to={`/project/${projectId}/form`}>
            Volver al formulario
          </Link>
        }
      />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="rounded-[28px] border border-border bg-white px-7 py-7 shadow-card">
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold text-dark">{primaryForm.title}</h2>
            <p className="text-sm text-muted">{primaryForm.description || "Formulario listo para compartir."}</p>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-[22px] border border-border px-5 py-5">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Estado</p>
              <p className="mt-2 text-lg font-semibold text-dark">{isPublished ? "Publicado" : "Borrador"}</p>
            </div>
            <div className="rounded-[22px] border border-border px-5 py-5">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Respuestas recibidas</p>
              <p className="mt-2 text-lg font-semibold text-dark">{responses.length}</p>
            </div>
            <div className="rounded-[22px] border border-border px-5 py-5">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Ultima respuesta</p>
              <p className="mt-2 text-lg font-semibold text-dark">
                {responses[0]?.submitted_at ? formatDate(responses[0].submitted_at) : "Sin datos"}
              </p>
            </div>
          </div>

          <div className="mt-6 rounded-[22px] border border-border px-5 py-5">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Link publico</p>
            <p className="mt-2 break-all text-sm text-dark">{frontendPublicUrl || "Todavia no generado"}</p>
          </div>

          <div className="mt-6 border-t border-border pt-6">
            <h3 className="text-base font-semibold text-dark">Cuestionarios a publicar</h3>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {(instrumentsQuery.data?.items ?? []).map((instrument) => (
                <label
                  className="flex cursor-pointer items-center gap-3 border border-border bg-white px-4 py-3 text-sm text-dark"
                  key={instrument.id}
                >
                  <input
                    checked={selectedInstrumentIds.includes(instrument.id)}
                    className="h-4 w-4 accent-[#F5B21A]"
                    onChange={(event) => {
                      setSelectedInstrumentIds((current) =>
                        event.target.checked
                          ? [...current, instrument.id]
                          : current.filter((id) => id !== instrument.id),
                      );
                    }}
                    type="checkbox"
                  />
                  <span>{instrument.name}</span>
                </label>
              ))}
            </div>
            <p className="mt-3 text-xs text-muted">
              Los datos del participante se incluyen siempre. Selecciona al menos un cuestionario.
            </p>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <PrimaryAction disabled={selectedInstrumentIds.length === 0} loading={publishMutation.isPending} onClick={() => publishMutation.mutate()} type="button">
              <Share2 className="mr-2 h-4 w-4" />
              {requiresConsolidation
                ? "Publicar proyecto completo"
                : isPublished
                  ? "Actualizar publicación"
                  : "Publicar link"}
            </PrimaryAction>
            <button
              className="colmena-button-secondary inline-flex items-center justify-center"
              disabled={!frontendPublicUrl}
              onClick={() => void copyText(frontendPublicUrl)}
              type="button"
            >
              <Copy className="mr-2 h-4 w-4" />
              Copiar link
            </button>
            {frontendPublicUrl ? (
              <a
                className="colmena-button-secondary inline-flex items-center justify-center"
                href={frontendPublicUrl}
                rel="noreferrer"
                target="_blank"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                Abrir link
              </a>
            ) : null}
            {isPublished ? (
              <button className="colmena-button-secondary inline-flex items-center justify-center" disabled={closeMutation.isPending} onClick={() => closeMutation.mutate()} type="button">
                <PauseCircle className="mr-2 h-4 w-4" />
                Cerrar formulario
              </button>
            ) : (
              <button className="colmena-button-secondary inline-flex items-center justify-center" disabled={reopenMutation.isPending || primaryForm.status !== "closed"} onClick={() => reopenMutation.mutate()} type="button">
                <PlayCircle className="mr-2 h-4 w-4" />
                Reabrir formulario
              </button>
            )}
          </div>

          <div className="mt-6 overflow-hidden rounded-[20px] border border-border">
            <div className="grid grid-cols-[0.9fr_1fr_0.9fr_0.8fr] gap-4 border-b border-border bg-[#FCFCFB] px-4 py-3 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              <span>Respondiente</span>
              <span>Fecha</span>
              <span>IP de origen</span>
              <span>Estado</span>
            </div>
            <div className="divide-y divide-border">
              {responses.length === 0 ? (
                <div className="px-4 py-5 text-sm text-muted">Todavia no hay respuestas registradas.</div>
              ) : (
                responses.slice(0, 6).map((response) => (
                  <div className="grid grid-cols-[0.9fr_1fr_0.9fr_0.8fr] gap-4 px-4 py-4 text-sm" key={response.id}>
                    <span className="text-dark">{response.respondent_code || response.id.slice(0, 6)}</span>
                    <span className="text-muted">{formatDate(response.submitted_at || response.created_at)}</span>
                    <span className="font-mono text-xs text-muted">{response.respondent_ip || "—"}</span>
                    <span className="text-dark">{response.status}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="rounded-[28px] border border-border bg-white px-6 py-6 shadow-card">
          <h3 className="text-lg font-semibold text-dark">Antes de compartir</h3>
          <ul className="mt-4 space-y-3 text-sm text-muted">
            <li>• Revisa variable, dimensiones e instrumento.</li>
            <li>• Confirma que la escala y los baremos ya estén configurados.</li>
            <li>• Comparte el link solo cuando el formulario esté listo.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
