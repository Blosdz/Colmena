import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ClipboardList } from 'lucide-react';

import { useAuth } from '../../../auth/AuthContext.jsx';
import { useActiveProject } from '../../../hooks/useActiveProject.js';
import { useProjectInstruments } from '../../../hooks/useProjectInstruments.js';
import { getProject } from '../../../api/projects.js';
import { getInstrumentTree } from '../../../api/instruments.js';
import { createSurveyFromInstrument, listSurveys } from '../../../api/surveys.js';

import { PageHeader } from '../../../components/layout/PageHeader.jsx';
import { Card } from '../../../components/ui/Card.jsx';
import { PrimaryAction } from '../../../components/ui/PrimaryAction.jsx';
import { EmptyState } from '../../../components/ui/EmptyState.jsx';
import { LoadingState } from '../../../components/ui/LoadingState.jsx';
import { StatusPill } from '../../../components/ui/StatusPill.jsx';
import { ProjectMissingState } from '../../../components/colmena/ProjectMissingState.jsx';
import SurveyThemePicker from '../../../components/colmena/survey/SurveyThemePicker.jsx';
import { displayLabel } from '../../../utils/labels.js';

/**
 * El backend sólo permite poblar preguntas de un survey vía
 * POST /projects/{id}/surveys/from-instrument (no existe un endpoint para
 * agregar preguntas sueltas a un survey "libre" después de crearlo) — por
 * eso este paso reutiliza el cuestionario interno del proyecto sin exponerlo
 * como una variable o selector adicional en la interfaz.
 */
export default function ProjectFormPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  useActiveProject(projectId);

  const { data: project, isLoading: isLoadingProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
  });

  const { data: instruments = [], isLoading: isLoadingInstruments } = useProjectInstruments(
    projectId,
    project?.metadata,
  );
  const preferredInstrumentId = Number(project?.metadata?.instrument_id || 0);
  const activeInstrument =
    instruments.find((instrument) => instrument.id === preferredInstrumentId) || instruments[0] || null;
  const versionId = activeInstrument?.versionId;

  const { data: surveysData, isLoading: isLoadingSurveys } = useQuery({
    queryKey: ['surveys', projectId],
    queryFn: () => listSurveys(projectId, { page: 1, pageSize: 100 }),
    enabled: Boolean(projectId),
  });
  const survey = (surveysData?.items || []).find(
    (item) => Number(item.instrument_version_id) === Number(versionId),
  );
  const surveyId = survey?.id;

  const { data: tree } = useQuery({
    queryKey: ['instrumentTree', versionId],
    queryFn: () => getInstrumentTree(versionId),
    enabled: Boolean(versionId) && !surveyId,
  });

  const itemCount = tree ? (tree.variables || []).reduce(
    (total, variable) => total + variable.direct_items.length
      + variable.dimensions.reduce((subtotal, dimension) => subtotal + countItems(dimension), 0),
    0,
  ) : 0;

  const createSurveyMutation = useMutation({
    mutationFn: () =>
      createSurveyFromInstrument(projectId, {
        created_by_user_id: user.id,
        instrument_version_id: versionId,
        name: `${project.name} — Formulario`,
      }),
    onSuccess: (createdSurvey) => {
      queryClient.invalidateQueries({ queryKey: ['surveys', projectId] });
      queryClient.setQueryData(['survey', createdSurvey.id], createdSurvey);
    },
  });

  if (isLoadingProject) return <LoadingState label="Cargando..." />;
  if (!project) return <ProjectMissingState />;

  return (
    <div className="colmena-page">
      <PageHeader eyebrow="Formulario" title={project.name} description="Publica como formulario las variables, dimensiones y preguntas definidas en el Constructor." />

      {isLoadingInstruments ? (
        <LoadingState label="Cargando cuestionario..." />
      ) : !versionId ? (
        <Card>
          <EmptyState title="Primero define la estructura del proyecto." description="En Constructor, crea una variable y agrega sus dimensiones o preguntas directas." />
        </Card>
      ) : isLoadingSurveys ? (
        <LoadingState label="Cargando formularios..." />
      ) : surveyId ? (
        <>
          <Card>
            <div className="flex flex-col gap-3">
              <p className="text-sm font-semibold text-dark">{survey.name}</p>
              <div className="flex items-center gap-2">
                <StatusPill label={displayLabel(survey.survey_type)} tone="neutral" />
                <StatusPill label={displayLabel(survey.status)} tone={survey.status === 'ACTIVE' ? 'active' : 'draft'} />
              </div>
              <p className="text-sm text-muted">
                Continúa en{' '}
                <Link to={`/colmena/project/${projectId}/link`} className="font-medium text-amber hover:underline">
                  Link
                </Link>{' '}
                para abrir la recolección y obtener la URL pública.
              </p>
            </div>
          </Card>
          {survey ? (
            <Card>
              <SurveyThemePicker project={project} />
            </Card>
          ) : null}
        </>
      ) : (
        <Card>
          <EmptyState
            title={itemCount === 0 ? 'Todavía no hay preguntas.' : 'Listo para publicar el formulario.'}
            description={
              itemCount === 0
                ? 'Agrega al menos una pregunta como pregunta directa o dentro de una dimensión antes de crear el formulario.'
                : `${itemCount} pregunta(s) se incorporarán al formulario sin duplicarlas.`
            }
          >
            {itemCount === 0 ? (
              <div className="mx-auto flex h-10 w-11 items-center justify-center rounded-2xl bg-amber/10 text-amber">
                <ClipboardList size={20} />
              </div>
            ) : (
              <PrimaryAction onClick={() => createSurveyMutation.mutate()} loading={createSurveyMutation.isPending}>
                Crear formulario
              </PrimaryAction>
            )}
          </EmptyState>
        </Card>
      )}
    </div>
  );
}

function countItems(construct) {
  return construct.items.length + construct.subdimensions.reduce((total, sub) => total + countItems(sub), 0);
}
