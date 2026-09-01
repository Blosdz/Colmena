import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Archive, Check, Copy, Send } from 'lucide-react';

import { useActiveProject } from '../../../hooks/useActiveProject.js';
import { getProject } from '../../../api/projects.js';
import { archiveStudy, closeStudy, createStudy, listStudies, openStudy } from '../../../api/studies.js';
import { listSurveys } from '../../../api/surveys.js';

import { PageHeader } from '../../../components/layout/PageHeader.jsx';
import { Card } from '../../../components/ui/Card.jsx';
import { Button } from '../../../components/ui/Button.jsx';
import { PrimaryAction } from '../../../components/ui/PrimaryAction.jsx';
import { Modal } from '../../../components/ui/Modal.jsx';
import { StatusPill } from '../../../components/ui/StatusPill.jsx';
import { EmptyState } from '../../../components/ui/EmptyState.jsx';
import { LoadingState } from '../../../components/ui/LoadingState.jsx';
import FormField from '../../../components/ui/FormField.jsx';
import { ProjectMissingState } from '../../../components/colmena/ProjectMissingState.jsx';
import { displayLabel } from '../../../utils/labels.js';

const STUDY_TYPES = [
  { value: 'ACADEMIC', label: 'Académico' },
  { value: 'CENSO', label: 'CensoPÁS' },
  { value: 'CUSTOM', label: 'Personalizado' },
  { value: 'RESEARCH', label: 'Investigación' },
];

const STUDY_TONE = { DRAFT: 'draft', OPEN: 'active', CLOSED: 'collecting', ARCHIVED: 'neutral' };

const schema = z.object({
  name: z.string().min(1, 'Ingresa un nombre'),
  surveyId: z.coerce.number().positive('Selecciona un formulario'),
  studyType: z.string().min(1),
  minPublishableN: z.coerce.number().min(1).default(5),
});

function NewStudyModal({ surveys, projectType, onClose, onCreate, isSubmitting }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { surveyId: surveys[0]?.id || '', studyType: projectType === 'CENSO' ? 'CENSO' : 'ACADEMIC', minPublishableN: 5 },
  });

  const formId = 'new-study-form';

  return (
    <Modal
      title="Nuevo estudio"
      subtitle="Un estudio abre la recolección de respuestas y genera la URL pública."
      onClose={onClose}
      size="md"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form={formId} variant="primary" loading={isSubmitting}>
            Crear estudio
          </Button>
        </>
      }
    >
      <form id={formId} className="flex flex-col gap-4" onSubmit={handleSubmit(onCreate)} noValidate>
        <FormField label="Nombre" placeholder="Aplicación 2026-I" error={errors.name?.message} {...register('name')} />
        <label className="flex flex-col gap-2">
          <span className="colmena-label">Formulario</span>
          <select className="colmena-input h-10 px-4 text-sm text-dark" {...register('surveyId')}>
            {surveys.map((survey) => (
              <option key={survey.id} value={survey.id}>
                {survey.name}
              </option>
            ))}
          </select>
          {errors.surveyId ? <span className="text-xs font-medium text-danger">{errors.surveyId.message}</span> : null}
        </label>
        {projectType === 'CENSO' ? (
          <input type="hidden" value="CENSO" {...register('studyType')} />
        ) : (
          <label className="flex flex-col gap-2">
            <span className="colmena-label">Tipo</span>
            <select className="colmena-input h-10 px-4 text-sm text-dark" {...register('studyType')}>
              {STUDY_TYPES.map((type) => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </label>
        )}
        <FormField
          label="N mínimo publicable"
          type="number"
          hint="Mínimo de respuestas válidas por celda para poder publicar resultados desagregados."
          {...register('minPublishableN')}
        />
      </form>
    </Modal>
  );
}

function CopyLinkButton({ url }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button
      type="button"
      onClick={copy}
      className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-white text-amber transition hover:border-amber/40"
      title={url}
    >
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );
}

function StudiesTable({ studies, onOpen, onClose, onArchive, isMutating }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="bg-surfaceSoft">
            {['Estudio', 'Tipo', 'Estado', 'Link público', ''].map((head) => (
              <th
                key={head}
                className="border-b border-r border-border px-4 py-2.5 text-[11px] font-bold uppercase tracking-[0.06em] text-muted last:border-r-0"
              >
                {head}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {studies.map((study) => {
            const publicUrl = `${window.location.origin}/encuesta/${study.public_id}`;
            return (
              <tr key={study.id} className="transition hover:bg-[#fafbfc]">
                <td className="border-b border-r border-border px-4 py-3 font-medium text-dark">{study.name}</td>
                <td className="border-b border-r border-border px-4 py-3">
                  <StatusPill label={displayLabel(study.study_type)} tone="neutral" />
                </td>
                <td className="border-b border-r border-border px-4 py-3">
                  <StatusPill label={displayLabel(study.status)} tone={STUDY_TONE[study.status] || 'neutral'} />
                </td>
                <td className="border-b border-r border-border px-4 py-3">
                  {study.status === 'OPEN' ? (
                    <div className="flex items-center gap-2">
                      <span className="max-w-[220px] truncate font-mono text-xs text-yellowDark">{publicUrl}</span>
                      <CopyLinkButton url={publicUrl} />
                    </div>
                  ) : (
                    <span className="text-xs text-muted">—</span>
                  )}
                </td>
                <td className="border-b border-border px-3 py-3">
                  <div className="flex justify-end gap-1.5">
                    {study.status === 'DRAFT' ? (
                      <button type="button" onClick={() => onOpen(study.id)} disabled={isMutating} className="colmena-button-sm-primary">
                        <Send size={13} className="mr-1" />
                        Abrir
                      </button>
                    ) : null}
                    {study.status === 'OPEN' ? (
                      <button type="button" onClick={() => onClose(study.id)} className="colmena-button-sm-secondary">
                        Cerrar
                      </button>
                    ) : null}
                    {study.status === 'CLOSED' ? (
                      <button type="button" onClick={() => onArchive(study.id)} className="colmena-button-sm-secondary">
                        <Archive size={13} className="mr-1" />
                        Archivar
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function ProjectLinkPage() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();
  const [showNewStudy, setShowNewStudy] = useState(false);
  useActiveProject(projectId);

  const { data: project, isLoading: isLoadingProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
  });

  const { data: surveysData, isLoading: isLoadingSurveys } = useQuery({
    queryKey: ['surveys', projectId],
    queryFn: () => listSurveys(projectId, { page: 1, pageSize: 100 }),
    enabled: Boolean(projectId),
  });
  const surveys = surveysData?.items || [];

  const { data, isLoading } = useQuery({
    queryKey: ['studies', projectId],
    queryFn: () => listStudies(projectId, { page: 1, pageSize: 50 }),
    enabled: Boolean(projectId),
  });
  const studies = data?.items ?? [];

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['studies', projectId] });

  const createMutation = useMutation({
    mutationFn: (values) =>
      createStudy(projectId, {
        survey_id: values.surveyId,
        name: values.name,
        study_type: values.studyType,
        min_publishable_n: values.minPublishableN,
      }),
    onSuccess: () => {
      invalidate();
      setShowNewStudy(false);
    },
  });

  const lifecycleMutation = useMutation({
    mutationFn: ({ action, studyId }) => {
      if (action === 'open') return openStudy(studyId);
      if (action === 'close') return closeStudy(studyId);
      return archiveStudy(studyId);
    },
    onSuccess: invalidate,
  });

  if (isLoadingProject) return <LoadingState label="Cargando..." />;
  if (!project) return <ProjectMissingState />;

  return (
    <div className="colmena-page">
      <PageHeader
        eyebrow="Link"
        title="Link y respuestas"
        description="Publica aplicaciones del formulario y gestiona sus respuestas."
        actions={surveys.length ? <PrimaryAction onClick={() => setShowNewStudy(true)}>Nuevo estudio</PrimaryAction> : null}
       
      />

      {showNewStudy ? (
        <NewStudyModal
          surveys={surveys}
          projectType={project.project_type}
          onClose={() => setShowNewStudy(false)}
          onCreate={(values) => createMutation.mutate(values)}
          isSubmitting={createMutation.isPending}
        />
      ) : null}

      {isLoadingSurveys ? (
        <LoadingState label="Cargando formularios..." />
      ) : surveys.length === 0 ? (
        <Card className="py-10">
          <EmptyState title="Primero crea un formulario." description="Publica las variables y preguntas del Constructor antes de crear un estudio." />
        </Card>
      ) : isLoading ? (
        <LoadingState label="Cargando estudios..." />
      ) : studies.length === 0 ? (
        <Card className="py-10">
          <EmptyState title="Todavía no hay estudios." description="Crea uno para abrir la recolección de respuestas.">
            <PrimaryAction onClick={() => setShowNewStudy(true)}>Nuevo estudio</PrimaryAction>
          </EmptyState>
        </Card>
      ) : (
        <div>
          <Card padded={false} className="rounded-none border-x-0">
            <StudiesTable
              studies={studies}
              isMutating={lifecycleMutation.isPending}
              onOpen={(id) => lifecycleMutation.mutate({ action: 'open', studyId: id })}
              onClose={(id) => lifecycleMutation.mutate({ action: 'close', studyId: id })}
              onArchive={(id) => lifecycleMutation.mutate({ action: 'archive', studyId: id })}
            />
          </Card>
        </div>
      )}
    </div>
  );
}
