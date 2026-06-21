import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getProject } from "../api/projects";
import { FormWizard } from "../components/forms-wizard/FormWizard";
import { PageHeader } from "../components/layout/PageHeader";
import { ProjectMissingState } from "../components/study/ProjectMissingState";
import { StudyFlowStepper } from "../components/study/StudyFlowStepper";
import { useActiveStudy } from "../components/study/useActiveStudy";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";

const builderSteps = [
  "Proyecto",
  "Variable principal",
  "Dimensiones",
  "Instrumento",
  "Ítems",
  "Escala de respuesta",
  "Baremos y calificación",
  "Escala de control",
  "Revisión y publicación",
];

export function StudyBuilderPage() {
  const { projectId = "" } = useParams();
  useActiveStudy(projectId);

  const projectQuery = useQuery({
    queryKey: ["project-builder-project", projectId],
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId),
  });

  if (projectQuery.isLoading) {
    return <LoadingState label="Preparando configuración del proyecto..." />;
  }

  if (projectQuery.isError) {
    return <ErrorState message={(projectQuery.error as Error).message} />;
  }

  if (!projectQuery.data) {
    return <ProjectMissingState description="No pudimos abrir la configuración de este proyecto." />;
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Crear proyecto"
        description="Aquí defines variable, dimensiones, instrumento, ítems, escala, baremos y publicación."
        actions={
          <Link className="colmena-button-secondary inline-flex items-center justify-center" to={`/project/${projectId}`}>
            Volver al proyecto
          </Link>
        }
      />

      <StudyFlowStepper
        steps={builderSteps.map((step, index) => ({
          label: step,
          status: index === builderSteps.length - 1 ? "pending" : "in_progress",
        }))}
      />

      <FormWizard projectId={projectId} projectTitle={projectQuery.data.title} />
    </div>
  );
}
