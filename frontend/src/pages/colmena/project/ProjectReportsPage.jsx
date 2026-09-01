import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { AlertTriangle, Download, FileText, RefreshCw, ShieldCheck } from 'lucide-react';

import { useAuth } from '../../../auth/AuthContext.jsx';
import { useActiveProject } from '../../../hooks/useActiveProject.js';
import { getProject } from '../../../api/projects.js';
import { getStudy } from '../../../api/studies.js';
import { getCensopasReadiness } from '../../../api/instruments.js';
import {
  createReportPreview,
  getReportDownloadUrl,
  getReportPreviewPdfUrl,
} from '../../../api/reports.js';

import { PageHeader } from '../../../components/layout/PageHeader.jsx';
import { Card } from '../../../components/ui/Card.jsx';
import { Button } from '../../../components/ui/Button.jsx';
import { LoadingState } from '../../../components/ui/LoadingState.jsx';
import { EmptyState } from '../../../components/ui/EmptyState.jsx';
import { ProjectMissingState } from '../../../components/colmena/ProjectMissingState.jsx';
import StudySelector from '../../../components/colmena/StudySelector.jsx';
import CensopasReadinessPanel from '../../../components/colmena/instruments/CensopasReadinessPanel.jsx';

const SECTIONS = [
  { key: 'portada', label: 'Portada' },
  { key: 'resumen_ejecutivo', label: 'Resumen ejecutivo' },
  { key: 'ficha_tecnica', label: 'Ficha técnica' },
  { key: 'calidad_datos', label: 'Calidad de datos (participación)' },
  { key: 'resultados_globales', label: 'Resultados globales' },
  { key: 'dimensiones', label: 'Dimensiones' },
  { key: 'subdimensiones', label: 'Subdimensiones' },
  { key: 'unidades_seguras', label: 'Unidades seguras' },
  { key: 'variables_descriptivas', label: 'Variables descriptivas' },
  { key: 'hallazgos_premium', label: 'Hallazgos premium' },
  { key: 'plan_accion', label: 'Plan de acción' },
  { key: 'anexos', label: 'Anexos' },
  { key: 'trazabilidad', label: 'Trazabilidad' },
  { key: 'firmas', label: 'Firmas' },
];

export default function ProjectReportsPage() {
  const { projectId } = useParams();
  const { user } = useAuth();
  useActiveProject(projectId);

  const [studyId, setStudyId] = useState(null);
  const [sections, setSections] = useState([]);
  const [reportMode, setReportMode] = useState('PROVISIONAL');
  const [outputFormat, setOutputFormat] = useState('DOCX');
  // Estado del preview (IDLE/GENERATING/READY/STALE/ERROR/EXPORTING) — la
  // configuración con la que se generó el preview vigente vive aparte para
  // poder compararla contra la actual y marcar STALE sin re-disparar nada.
  const [previewState, setPreviewState] = useState('IDLE');
  const [preview, setPreview] = useState(null);
  const [generatedConfig, setGeneratedConfig] = useState(null);

  const { data: project, isLoading: isLoadingProject } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
  });

  const { data: study } = useQuery({
    queryKey: ['study', studyId],
    queryFn: () => getStudy(studyId),
    enabled: Boolean(studyId),
  });

  const { data: readiness, isFetching: isLoadingReadiness } = useQuery({
    queryKey: ['censopas-readiness', study?.instrument_version_id],
    queryFn: () => getCensopasReadiness(study.instrument_version_id),
    enabled: Boolean(study?.instrument_version_id),
  });

  const currentConfig = { studyId, sections: [...sections].sort(), reportMode, outputFormat };

  const previewMutation = useMutation({
    mutationFn: () =>
      createReportPreview(studyId, {
        requested_by_user_id: user.id,
        report_mode: reportMode,
        output_format: outputFormat,
        sections,
      }),
    onMutate: () => setPreviewState('GENERATING'),
    onSuccess: (data) => {
      setPreview(data);
      setGeneratedConfig(currentConfig);
      setPreviewState('READY');
    },
    onError: () => setPreviewState('ERROR'),
  });

  useEffect(() => {
    if (previewState === 'READY' && generatedConfig && JSON.stringify(generatedConfig) !== JSON.stringify(currentConfig)) {
      setPreviewState('STALE');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studyId, sections, reportMode, outputFormat]);

  const toggleSection = (key) => {
    setSections((prev) => (prev.includes(key) ? prev.filter((s) => s !== key) : [...prev, key]));
  };

  const resetPreview = () => {
    setPreview(null);
    setGeneratedConfig(null);
    setPreviewState('IDLE');
  };

  if (isLoadingProject) return <LoadingState label="Cargando..." />;
  if (!project) return <ProjectMissingState />;

  const canExport = previewState === 'READY' && preview;
  const exportUrl = preview
    ? outputFormat === 'PDF'
      ? getReportPreviewPdfUrl(preview.preview_id)
      : getReportDownloadUrl(preview.preview_id)
    : null;

  return (
    <div className="colmena-page">
      <PageHeader eyebrow="Reportes" title={project.name} description="Genera reportes estructurados a partir de los análisis del estudio." />

      <div className="grid gap-4 md:grid-cols-[360px_1fr]">
        <Card className="flex flex-col gap-5">
          <div className="flex flex-col gap-3">
            <p className="colmena-label">Estudio</p>
            <StudySelector
              projectId={projectId}
              studyId={studyId}
              onStudyChange={(value) => {
                setStudyId(value);
                resetPreview();
              }}
            />
            {studyId ? <CensopasReadinessPanel readiness={readiness} isLoading={isLoadingReadiness} /> : null}
          </div>

          <div>
            <p className="colmena-label mb-2">Secciones a incluir</p>
            <div className="flex flex-wrap gap-2">
              {SECTIONS.map((section) => (
                <button
                  key={section.key}
                  type="button"
                  onClick={() => toggleSection(section.key)}
                  className={`colmena-badge cursor-pointer ${sections.includes(section.key) ? 'bg-amber text-white' : 'bg-amber/10 text-yellowDark'}`}
                >
                  {section.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="colmena-label mb-2">Nivel metodológico</p>
            <div className="grid gap-2 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => setReportMode('PROVISIONAL')}
                className={'rounded-xl border p-3 text-left ' + (reportMode === 'PROVISIONAL' ? 'border-amber bg-amber/5' : 'border-border bg-surface')}
              >
                <FileText size={16} className="mb-1.5 text-amber" />
                <span className="block text-xs font-semibold text-dark">Provisional</span>
              </button>
              <button
                type="button"
                disabled={!readiness?.ready_for_official_reporting}
                onClick={() => setReportMode('OFFICIAL')}
                className={'rounded-xl border p-3 text-left ' + (reportMode === 'OFFICIAL' ? 'border-turquoise bg-turquoise/5' : 'border-border bg-surface') + ' disabled:cursor-not-allowed disabled:opacity-50'}
              >
                <ShieldCheck size={16} className="mb-1.5 text-turquoise" />
                <span className="block text-xs font-semibold text-dark">Oficial</span>
              </button>
            </div>
          </div>

          <div>
            <label className="colmena-label mb-2 block" htmlFor="report-output-format">Formato de salida</label>
            <select
              id="report-output-format"
              className="colmena-input w-full"
              value={outputFormat}
              onChange={(event) => setOutputFormat(event.target.value)}
            >
              <option value="DOCX">Word (.docx)</option>
              <option value="PDF">PDF (.pdf)</option>
            </select>
          </div>

          <p className="text-xs text-muted">
            Este estudio requiere un mínimo de <strong className="text-dark">{study?.min_publishable_n ?? '—'}</strong> respuestas
            válidas por celda para publicar resultados desagregados. El backend aplica esta regla al generar el reporte.
          </p>

          <Button
            variant="primary"
            size="md"
            onClick={() => previewMutation.mutate()}
            disabled={!studyId || previewState === 'GENERATING'}
            loading={previewState === 'GENERATING'}
            className="w-full"
          >
            <RefreshCw size={16} />
            Actualizar vista previa
          </Button>
        </Card>

        <Card className="flex min-h-[520px] flex-col gap-3" padding="roomy">
          {previewState === 'IDLE' ? (
            <EmptyState
              title="Configura y genera la vista previa"
              description="Elige un estudio y las secciones a incluir, luego pulsa «Actualizar vista previa»."
            />
          ) : null}
          {previewState === 'GENERATING' ? <LoadingState label="Generando vista previa del reporte…" /> : null}
          {previewState === 'ERROR' ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
              <AlertTriangle size={28} className="text-danger" />
              <p className="text-sm font-medium text-danger">No pudimos generar la vista previa.</p>
              <Button variant="secondary" size="sm" onClick={() => previewMutation.mutate()}>
                Reintentar
              </Button>
            </div>
          ) : null}
          {(previewState === 'READY' || previewState === 'STALE' || previewState === 'EXPORTING') && preview ? (
            <>
              {previewState === 'STALE' ? (
                <p className="rounded-xl border border-amber/30 bg-amber/10 px-3 py-2 text-xs font-medium text-yellowDark">
                  La configuración cambió. Actualiza la vista previa antes de exportar.
                </p>
              ) : null}
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted">{preview.pages ? `${preview.pages} páginas` : ''}</span>
              </div>
              <iframe
                title="Vista previa del reporte"
                src={getReportPreviewPdfUrl(preview.preview_id)}
                className="min-h-[560px] flex-1 rounded-xl border border-border"
              />
            </>
          ) : null}

          <div className="flex justify-end gap-3 border-t border-border pt-3">
            <a
              href={canExport ? exportUrl : undefined}
              target="_blank"
              rel="noreferrer"
              onClick={(event) => {
                if (!canExport) event.preventDefault();
                else setPreviewState('EXPORTING');
              }}
              className={`colmena-button-primary ${canExport ? '' : 'pointer-events-none opacity-50'}`}
            >
              <Download size={16} className="mr-2" />
              Exportar {outputFormat === 'PDF' ? 'PDF' : 'Word'}
            </a>
          </div>
        </Card>
      </div>
    </div>
  );
}
