import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { listProjectForms } from "../api/forms";
import { getProject } from "../api/projects";
import { PageHeader } from "../components/layout/PageHeader";
import { ApaTableViewer } from "../components/results/ApaTableViewer";
import { ChartViewer } from "../components/results/ChartViewer";
import { WordReportPanel } from "../components/results/WordReportPanel";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { LoadingState } from "../components/ui/LoadingState";

function getPrimaryForm<T extends { status: string }>(forms: T[]) {
  return forms.find((form) => form.status === "published") ?? forms[0] ?? null;
}

export function ProjectReportsPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

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

  if (projectQuery.isLoading || formsQuery.isLoading) {
    return <LoadingState label="Preparando reportes..." />;
  }

  const primaryForm = getPrimaryForm(formsQuery.data?.items ?? []);

  // Si falla la carga del proyecto (mock) o no hay formulario, mostramos el empty state útil
  if (projectQuery.isError || formsQuery.isError || !projectQuery.data || !primaryForm) {
    return (
      <div className="flex h-full flex-col">
        <PageHeader title="Reportes y Entregables" description="Genera tablas APA, gráficos y exporta tus resultados a Word o PDF." />
        
        <div className="flex-1 flex flex-col items-center justify-center mt-6 rounded-[24px] border border-[#E6E8EB] bg-white p-12 text-center shadow-sm">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[#FFF8E7] text-[#FF6A2A] mb-6">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
          </div>
          <h2 className="text-2xl font-bold text-dark mb-2">Aún no hay resultados para reportar</h2>
          <p className="text-muted max-w-md mb-8 leading-relaxed">
            Para generar tu informe de investigación, primero necesitas procesar los resultados estadísticos del proyecto.
          </p>
          <div className="flex gap-4">
            <Link className="colmena-button-primary" to={`/project/${projectId}/results`}>
              Ir a Resultados
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Reportes"
        description="Aquí preparas tablas APA, gráficos editables, Excel y el informe Word/PDF."
        actions={
          <Link className="colmena-button-secondary inline-flex items-center justify-center" to={`/project/${projectId}/results`}>
            Volver a resultados
          </Link>
        }
      />

      <div className="grid gap-5 xl:grid-cols-2">
        <section className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
          <h2 className="text-lg font-semibold text-dark">Tablas APA</h2>
          <div className="mt-4">
            <ApaTableViewer formId={primaryForm.id} />
          </div>
        </section>

        <section className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
          <h2 className="text-lg font-semibold text-dark">Gráficos premium</h2>
          <div className="mt-4">
            <ChartViewer formId={primaryForm.id} />
          </div>
        </section>
      </div>

      <section className="rounded-[24px] border border-border bg-white px-5 py-5 shadow-card">
        <h2 className="text-lg font-semibold text-dark">Informe Word</h2>
        <div className="mt-4">
          <WordReportPanel formId={primaryForm.id} />
        </div>
      </section>
    </div>
  );
}
