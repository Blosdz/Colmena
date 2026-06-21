import { useQueries, useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { listProjectForms } from "../api/forms";
import { listProjects } from "../api/projects";
import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";

export function ArchiveFormsPage() {
  const projectsQuery = useQuery({
    queryKey: ["archive-forms-projects"],
    queryFn: listProjects,
  });

  const formsQueries = useQueries({
    queries: (projectsQuery.data?.items ?? []).map((project) => ({
      queryKey: ["archive-forms-project", project.id],
      queryFn: () => listProjectForms(project.id),
      enabled: Boolean(project.id),
    })),
  });

  if (projectsQuery.isLoading) {
    return <LoadingState label="Cargando formularios..." />;
  }

  if (projectsQuery.isError) {
    return <ErrorState message={(projectsQuery.error as Error).message} />;
  }

  if (formsQueries.some((query) => query.isLoading)) {
    return <LoadingState label="Cargando formularios..." />;
  }

  const formsError = formsQueries.find((query) => query.isError)?.error;
  if (formsError) {
    return <ErrorState message={(formsError as Error).message} />;
  }

  const forms = (projectsQuery.data?.items ?? []).flatMap((project, index) =>
    (formsQueries[index]?.data?.items ?? []).map((form) => ({
      ...form,
      projectTitle: project.title,
      projectId: project.id,
    })),
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Formularios guardados"
        description="Esta vista es secundaria. Se usa solo para reabrir formularios ya vinculados a un proyecto."
        actions={
          <Link className="colmena-button-secondary inline-flex items-center justify-center" to="/archive/projects">
            Ver proyectos
          </Link>
        }
      />

      <section className="rounded-[28px] border border-border bg-white px-6 py-6 shadow-card">
        {forms.length === 0 ? (
          <EmptyState
            title="Aun no hay formularios"
            description="Crea un proyecto y luego estructura el formulario desde el flujo principal."
          />
        ) : (
          <div className="overflow-hidden rounded-[22px] border border-border">
            <div className="grid grid-cols-[minmax(0,1.4fr)_minmax(0,1.2fr)_140px] gap-4 border-b border-border bg-[#FCFCFB] px-5 py-3 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              <span>Formulario</span>
              <span>Proyecto</span>
              <span>Accion</span>
            </div>
            <div className="divide-y divide-border">
              {forms.map((form) => (
                <div className="grid grid-cols-[minmax(0,1.4fr)_minmax(0,1.2fr)_140px] items-center gap-4 px-5 py-4" key={form.id}>
                  <div className="space-y-1">
                    <p className="text-base font-semibold text-dark">{form.title}</p>
                    <p className="text-sm text-muted">{form.status}</p>
                  </div>
                  <p className="text-sm text-muted">{form.projectTitle}</p>
                  <Link
                    className="inline-flex h-10 items-center justify-center gap-2 rounded-[16px] border border-border px-4 text-sm font-medium text-dark transition hover:bg-[#FBF7EE]"
                    to={`/project/${form.projectId}/form`}
                  >
                    Abrir
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
