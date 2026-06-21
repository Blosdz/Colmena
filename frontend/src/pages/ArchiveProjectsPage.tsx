import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Search } from "lucide-react";
import { Link } from "react-router-dom";

import { listProjects } from "../api/projects";
import { PageHeader } from "../components/layout/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PrimaryAction } from "../components/ui/PrimaryAction";

export function ArchiveProjectsPage() {
  const projectsQuery = useQuery({
    queryKey: ["archive-projects"],
    queryFn: listProjects,
  });

  if (projectsQuery.isLoading) {
    return <LoadingState label="Cargando proyectos..." />;
  }

  if (projectsQuery.isError) {
    return <ErrorState message={(projectsQuery.error as Error).message} />;
  }

  const projects = projectsQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Abrir proyecto existente"
        description="Esta vista solo sirve para retomar un proyecto ya creado. El flujo principal sigue empezando en Crear proyecto."
        actions={
          <Link to="/project/new">
            <PrimaryAction>Crear proyecto</PrimaryAction>
          </Link>
        }
      />

      <section className="rounded-[28px] border border-border bg-white px-6 py-6 shadow-card">
        <div className="flex h-12 max-w-[420px] items-center gap-3 rounded-[18px] border border-border px-4">
          <Search className="h-4 w-4 text-muted" />
          <span className="text-sm text-muted">Buscar proyecto existente...</span>
        </div>

        {projects.length === 0 ? (
          <div className="mt-6">
            <EmptyState
              title="Aun no hay proyectos"
              description="Empieza creando el proyecto y luego define variable, formulario y reportes."
            />
          </div>
        ) : (
          <div className="mt-6 overflow-hidden rounded-[22px] border border-border">
            <div className="grid grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_160px] gap-4 border-b border-border bg-[#FCFCFB] px-5 py-3 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              <span>Proyecto</span>
              <span>Contexto</span>
              <span>Accion</span>
            </div>
            <div className="divide-y divide-border">
              {projects.map((project) => (
                <div className="grid grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_160px] items-center gap-4 px-5 py-4" key={project.id}>
                  <div className="space-y-1">
                    <p className="text-base font-semibold text-dark">{project.title}</p>
                    <p className="text-sm text-muted">{project.status}</p>
                  </div>
                  <p className="text-sm text-muted">
                    {[project.institution, project.career].filter(Boolean).join(" · ") || "Sin contexto adicional"}
                  </p>
                  <Link
                    className="inline-flex h-10 items-center justify-center gap-2 rounded-[16px] border border-border px-4 text-sm font-medium text-dark transition hover:bg-[#FBF7EE]"
                    to={`/project/${project.id}`}
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
