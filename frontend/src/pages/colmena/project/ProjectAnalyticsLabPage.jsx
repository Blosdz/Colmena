import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  ShieldCheck,
  Target,
  Users,
} from 'lucide-react';

import { useActiveProject } from '../../../hooks/useActiveProject.js';
import { getProject } from '../../../api/projects.js';
import { getProjectTelemetry } from '../../../api/telemetry.js';
import {
  getCensopasResults,
  getCensopasUnitResults,
  getResultsOverview,
  listStudies,
  listStudyUnitTypes,
} from '../../../api/studies.js';
import { PageHeader } from '../../../components/layout/PageHeader.jsx';
import { Card } from '../../../components/ui/Card.jsx';
import { Button } from '../../../components/ui/Button.jsx';
import { EmptyState } from '../../../components/ui/EmptyState.jsx';
import { LoadingState } from '../../../components/ui/LoadingState.jsx';
import { ProjectMissingState } from '../../../components/colmena/ProjectMissingState.jsx';
import StudySelector from '../../../components/colmena/StudySelector.jsx';

const COLORS = {
  favorable: '#24A886',
  intermediate: '#F2B84B',
  unfavorable: '#E05959',
  ink: '#183238',
  turquoise: '#11B7B2',
};

function pct(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return `${Number(value).toFixed(digits)}%`;
}

function number(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return Number(value).toFixed(digits);
}

function duration(seconds) {
  if (seconds === null || seconds === undefined) return '—';
  const minutes = Math.floor(Number(seconds) / 60);
  return `${minutes} min ${Math.round(Number(seconds) % 60)} s`;
}

function wilsonInterval(count, total) {
  if (!total) return [0, 0];
  const z = 1.96;
  const p = count / total;
  const denominator = 1 + (z * z) / total;
  const center = (p + (z * z) / (2 * total)) / denominator;
  const margin = (z / denominator) * Math.sqrt((p * (1 - p)) / total + (z * z) / (4 * total * total));
  return [Math.max(0, center - margin) * 100, Math.min(1, center + margin) * 100];
}

function levelTone(level) {
  if (level === 'RIESGO_ALTO') return { label: 'Riesgo alto', color: COLORS.unfavorable, bg: 'rgba(224,89,89,.12)' };
  if (level === 'FACTOR_PROTECTOR') return { label: 'Factor protector', color: COLORS.favorable, bg: 'rgba(36,168,134,.12)' };
  if (level === 'RIESGO_MEDIO') return { label: 'Riesgo medio', color: '#9A6900', bg: 'rgba(242,184,75,.18)' };
  return { label: 'Revisión', color: '#64748B', bg: '#F1F5F9' };
}

function actionFor(name) {
  const token = name.toLowerCase();
  if (token.includes('ritmo') || token.includes('exigencia')) return 'Revisar dotación, carga y pausas por turno.';
  if (token.includes('rol') || token.includes('influencia')) return 'Clarificar funciones y ampliar participación operativa.';
  if (token.includes('liderazgo') || token.includes('apoyo')) return 'Entrenar supervisión y formalizar rutinas de apoyo.';
  if (token.includes('confianza') || token.includes('justicia')) return 'Reforzar transparencia, consulta y criterios de decisión.';
  if (token.includes('inseguridad') || token.includes('compens')) return 'Comunicar cambios laborales y revisar mecanismos de reconocimiento.';
  return 'Diseñar una intervención organizacional específica y medible.';
}

function SectionHeading({ kicker, title, description, action }) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-amber">{kicker}</p>
        <h2 className="mt-1 text-lg font-extrabold tracking-tight text-dark">{title}</h2>
        {description ? <p className="mt-1 max-w-3xl text-xs leading-5 text-muted">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

function ExecutiveMetric({ icon: Icon, label, value, detail, tone = 'amber' }) {
  const styles = tone === 'danger'
    ? 'from-[#FCE8E8] to-white text-danger'
    : tone === 'turquoise'
      ? 'from-[#E3F7F5] to-white text-turquoise'
      : 'from-[#FFF5D9] to-white text-yellowDark';
  return (
    <div className={`rounded-2xl border border-white/70 bg-gradient-to-br ${styles} p-4 shadow-[0_12px_30px_rgba(24,50,56,.07)]`}>
      <div className="flex items-start justify-between gap-3">
        <div><p className="text-[10px] font-extrabold uppercase tracking-[0.12em] opacity-70">{label}</p><p className="mt-2 text-2xl font-black tracking-tight text-dark">{value}</p></div>
        <span className="rounded-xl bg-white/80 p-2 shadow-sm"><Icon size={17} /></span>
      </div>
      <p className="mt-2 text-[11px] leading-4 text-muted">{detail}</p>
    </div>
  );
}

function DistributionBar({ row }) {
  return (
    <div className="flex h-7 min-w-[260px] overflow-hidden rounded-lg border border-white shadow-inner">
      {[
        ['favorable_pct', COLORS.favorable],
        ['intermediate_pct', COLORS.intermediate],
        ['unfavorable_pct', COLORS.unfavorable],
      ].map(([key, color]) => {
        const value = Number(row[key] || 0);
        return value > 0 ? <div key={key} style={{ width: `${value}%`, backgroundColor: color }} className="flex items-center justify-center text-[10px] font-extrabold text-white">{value >= 9 ? pct(value, 0) : ''}</div> : null;
      })}
    </div>
  );
}

function DimensionTable({ rows }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-border/80 bg-white">
      <table className="min-w-[1120px] w-full text-left text-xs">
        <thead className="bg-[#16363A] text-white">
          <tr>
            {['Dim.', 'Dimensión', 'n', 'Favorable n (%)', 'Intermedio n (%)', 'Desfavorable n (%)', 'Distribución', 'Puntaje', 'IC 95% desf.', 'Nivel'].map((label) => <th key={label} className="px-3 py-3 font-bold">{label}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const interval = wilsonInterval(row.unfavorable_n, row.n_valid);
            const tone = levelTone(row.collective_classification);
            return (
              <tr key={row.construct_id} className="border-t border-border/70 align-middle hover:bg-surfaceSoft/60">
                <td className="px-3 py-3 font-mono font-bold text-muted">{row.construct_code}</td>
                <td className="max-w-[220px] px-3 py-3 font-semibold text-dark">{row.construct_name}</td>
                <td className="px-3 py-3 font-mono">{row.n_valid}</td>
                <td className="px-3 py-3 font-mono text-emerald-700">{row.favorable_n} ({pct(row.favorable_pct)})</td>
                <td className="px-3 py-3 font-mono text-yellowDark">{row.intermediate_n} ({pct(row.intermediate_pct)})</td>
                <td className="px-3 py-3 font-mono text-danger">{row.unfavorable_n} ({pct(row.unfavorable_pct)})</td>
                <td className="px-3 py-3"><DistributionBar row={row} /></td>
                <td className="px-3 py-3 font-mono font-bold">{number(row.construct_score)} / 100</td>
                <td className="px-3 py-3 font-mono">{number(interval[0])}–{number(interval[1])}%</td>
                <td className="px-3 py-3"><span className="inline-flex whitespace-nowrap rounded-full px-2.5 py-1 text-[10px] font-extrabold" style={{ color: tone.color, backgroundColor: tone.bg }}>{tone.label}</span></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function SubdimensionTable({ rows }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-border/80 bg-white">
      <table className="min-w-[900px] w-full text-left text-xs">
        <thead className="bg-surfaceSoft text-dark">
          <tr>{['Prioridad', 'Código', 'Subdimensión', 'Dim.', 'n', '% favorable', '% intermedio', '% desfavorable', 'Puntaje', 'Nivel', 'Pregunta preventiva'].map((label) => <th key={label} className="px-3 py-3 font-bold">{label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const tone = levelTone(row.collective_classification);
            return (
              <tr key={row.construct_id} className="border-t border-border/70 align-top hover:bg-surfaceSoft/50">
                <td className="px-3 py-3"><span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-dark text-[10px] font-extrabold text-white">{index + 1}</span></td>
                <td className="px-3 py-3 font-mono text-muted">{row.construct_code}</td>
                <td className="px-3 py-3 font-semibold text-dark">{row.construct_name}</td>
                <td className="px-3 py-3 font-mono">{row.dimension_code}</td>
                <td className="px-3 py-3 font-mono">{row.n_valid}</td>
                <td className="px-3 py-3 font-mono text-emerald-700">{pct(row.favorable_pct)}</td>
                <td className="px-3 py-3 font-mono text-yellowDark">{pct(row.intermediate_pct)}</td>
                <td className="px-3 py-3 font-mono font-bold text-danger">{pct(row.unfavorable_pct)}</td>
                <td className="px-3 py-3 font-mono">{number(row.construct_score)}</td>
                <td className="px-3 py-3"><span className="rounded-full px-2 py-1 text-[10px] font-bold" style={{ color: tone.color, backgroundColor: tone.bg }}>{tone.label}</span></td>
                <td className="max-w-[260px] px-3 py-3 leading-5 text-muted">{actionFor(row.construct_name)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Heatmap({ rows, dimensions, thresholds }) {
  const warning = Number(thresholds?.risk_warning || 35);
  const critical = Number(thresholds?.risk_critical || 50);
  const units = [...new Map(rows.map((row) => [row.unit_id, { id: row.unit_id, name: row.unit_name }])).values()];
  const map = new Map(rows.map((row) => [`${row.construct_id}:${row.unit_id}`, row]));
  const heat = (value) => {
    if (value >= critical) return { background: '#E05959', color: 'white' };
    if (value >= warning) return { background: '#F5C85B', color: '#563B00' };
    return { background: '#BDE8D9', color: '#145B4B' };
  };
  return (
    <div className="overflow-x-auto rounded-2xl border border-border bg-white">
      <table className="min-w-[760px] w-full text-xs">
        <thead><tr className="bg-[#16363A] text-white"><th className="px-3 py-3 text-left">Dimensión</th>{units.map((unit) => <th key={unit.id} className="px-3 py-3 text-center">{unit.name}<span className="mt-1 block text-[9px] font-normal text-white/60">n = {rows.find((row) => row.unit_id === unit.id)?.n_valid || '—'}</span></th>)}</tr></thead>
        <tbody>{dimensions.map((dimension) => <tr key={dimension.construct_id} className="border-t border-border"><td className="px-3 py-3 font-semibold text-dark"><span className="mr-2 font-mono text-muted">{dimension.construct_code}</span>{dimension.construct_name}</td>{units.map((unit) => { const value = map.get(`${dimension.construct_id}:${unit.id}`); return <td key={unit.id} className="p-2"><div className="rounded-lg px-2 py-3 text-center font-mono font-extrabold" style={value?.suppressed ? { background: '#E2E8F0', color: '#64748B' } : heat(Number(value?.unfavorable_pct || 0))}>{value?.suppressed ? 'Suprimido' : pct(value?.unfavorable_pct || 0)}</div></td>; })}</tr>)}</tbody>
      </table>
    </div>
  );
}

function QualityTable({ telemetry, expectedWorkers, officialEnabled, minimumCell }) {
  const valid = telemetry?.valid_count || 0;
  const coverage = expectedWorkers ? (valid / expectedWorkers) * 100 : null;
  const rows = [
    ['Cobertura válida', coverage === null ? 'Sin marco' : pct(coverage), '≥ 80% recomendado', coverage !== null && coverage >= 80 ? 'Cumple' : 'Vigilar'],
    ['Completitud de sesiones', pct((telemetry?.completion_rate || 0) * 100), '≥ 90%', (telemetry?.completion_rate || 0) >= .9 ? 'Cumple' : 'Vigilar'],
    ['Casos excluidos', String(telemetry?.excluded_count ?? 0), 'Trazabilidad visible', 'Cumple'],
    ['Duración promedio', duration(telemetry?.avg_duration_seconds), 'Revisar respuestas extremas', 'Informativo'],
    ['Celda mínima por área', `n = ${minimumCell || '—'}`, 'n ≥ 5', minimumCell >= 5 ? 'Cumple' : 'Suprimida'],
    ['Consistencia interna', 'No calculada', 'α/ω con reglas oficiales', 'Pendiente'],
    ['Equivalencia oficial', officialEnabled ? 'Habilitada' : 'Deshabilitada', 'Manifiesto + baremo autorizado', officialEnabled ? 'Cumple' : 'Demo'],
  ];
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-white">
      <table className="w-full text-left text-xs"><thead className="bg-surfaceSoft"><tr>{['Control', 'Resultado', 'Criterio', 'Estado'].map((label) => <th key={label} className="px-4 py-3 font-bold">{label}</th>)}</tr></thead><tbody>{rows.map(([label, value, rule, state]) => <tr key={label} className="border-t border-border"><td className="px-4 py-3 font-semibold text-dark">{label}</td><td className="px-4 py-3 font-mono">{value}</td><td className="px-4 py-3 text-muted">{rule}</td><td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-[10px] font-bold ${state === 'Cumple' ? 'bg-emerald-50 text-emerald-700' : state === 'Vigilar' ? 'bg-amber/15 text-yellowDark' : 'bg-slate-100 text-slate-600'}`}>{state}</span></td></tr>)}</tbody></table>
    </div>
  );
}

export default function ProjectAnalyticsLabPage() {
  const { projectId } = useParams();
  useActiveProject(projectId);
  const [studyId, setStudyId] = useState(null);

  const { data: project, isLoading: isLoadingProject } = useQuery({ queryKey: ['project', projectId], queryFn: () => getProject(projectId) });
  const { data: studiesPage } = useQuery({ queryKey: ['studies', projectId, 'premium'], queryFn: () => listStudies(projectId, { page: 1, pageSize: 100 }) });
  const { data: telemetry } = useQuery({ queryKey: ['projectTelemetry', projectId], queryFn: () => getProjectTelemetry(projectId), enabled: Boolean(projectId) });
  const { data: overview, isLoading: overviewLoading } = useQuery({ queryKey: ['resultsOverview', studyId], queryFn: () => getResultsOverview(studyId), enabled: Boolean(studyId) });
  const { data: censopas, isLoading: censopasLoading } = useQuery({ queryKey: ['censopasResults', studyId], queryFn: () => getCensopasResults(studyId), enabled: Boolean(studyId) });
  const { data: unitTypes = [] } = useQuery({ queryKey: ['studyUnitTypes', studyId], queryFn: () => listStudyUnitTypes(studyId), enabled: Boolean(studyId) });
  const areaType = unitTypes.find((item) => item.code === 'AREA') || unitTypes[0];
  const { data: unitResults } = useQuery({ queryKey: ['censopasUnitResults', studyId, areaType?.id], queryFn: () => getCensopasUnitResults(studyId, areaType.id), enabled: Boolean(studyId && areaType?.id) });

  useEffect(() => {
    if (!studyId && studiesPage?.items?.length) setStudyId(studiesPage.items[0].id);
  }, [studyId, studiesPage]);

  const enriched = useMemo(() => {
    const structure = new Map((overview?.results || []).map((row) => [row.construct_id, row]));
    return (censopas?.results || []).map((row) => ({ ...structure.get(row.construct_id), ...row }));
  }, [overview, censopas]);

  if (isLoadingProject) return <LoadingState label="Cargando tablero…" />;
  if (!project) return <ProjectMissingState />;

  const selectedTelemetry = (telemetry?.studies || []).find((item) => Number(item.study_id) === Number(studyId));
  const dimensions = enriched.filter((row) => row.construct_type === 'DIMENSION' && !row.suppressed).sort((a, b) => a.construct_code.localeCompare(b.construct_code));
  const dimensionById = new Map(dimensions.map((row) => [row.construct_id, row]));
  const subdimensions = enriched.filter((row) => row.construct_type === 'SUBDIMENSION' && !row.suppressed).map((row) => ({ ...row, dimension_code: dimensionById.get(row.parent_id)?.construct_code || '—' })).sort((a, b) => Number(b.unfavorable_pct || 0) - Number(a.unfavorable_pct || 0));
  const unitDimensionRows = (unitResults?.results || []).filter((row) => dimensions.some((dimension) => dimension.construct_id === row.construct_id));
  const expectedWorkers = Number(project.metadata?.expected_worker_count || 0) || null;
  const thresholds = {
    coverage_target: 85,
    coverage_critical: 65,
    completion_target: 90,
    risk_warning: 35,
    risk_critical: 50,
    ...(project.metadata?.thresholds || {}),
  };
  const validCount = selectedTelemetry?.valid_count || overview?.n_completed || 0;
  const coverage = expectedWorkers ? (validCount / expectedWorkers) * 100 : null;
  const highRiskSubdimensions = subdimensions.filter((row) => Number(row.unfavorable_pct || 0) >= Number(thresholds.risk_critical) || row.collective_classification === 'RIESGO_ALTO');
  const highestRisk = subdimensions[0];
  const minimumCell = unitDimensionRows.length ? Math.min(...unitDimensionRows.map((row) => row.n_valid)) : null;
  const chartDimensions = dimensions.map((row) => ({ name: row.construct_code, favorable: row.favorable_pct, intermedio: row.intermediate_pct, desfavorable: row.unfavorable_pct, score: row.construct_score }));
  const radarData = dimensions.map((row) => ({ dimension: row.construct_code, riesgo: Number(row.construct_score || 0), fullMark: 100 }));
  const topTen = subdimensions.slice(0, 10).map((row) => ({ name: row.construct_name, desfavorable: row.unfavorable_pct, score: row.construct_score }));
  const loading = overviewLoading || censopasLoading;

  return (
    <div className="colmena-page pb-16">
      <PageHeader eyebrow="Panel visual · CENSOPAS-COPSOQ" title={project.name} description="Dashboard ejecutivo, resultados por dimensión y subdimensión, precisión, segmentación segura y Balanced Scorecard preventivo." actions={<Link to={`/colmena/project/${projectId}/reports`}><Button size="sm"><FileText size={14} /> Generar expediente</Button></Link>} />

      <Card className="overflow-hidden border-0 bg-gradient-to-br from-[#102F33] via-[#183E42] to-[#17635F] p-0 text-white shadow-[0_28px_70px_rgba(16,47,51,.22)]">
        <div className="grid gap-6 p-6 lg:grid-cols-[1.35fr_.65fr] lg:p-8">
          <div>
            <p className="text-[10px] font-extrabold uppercase tracking-[0.2em] text-[#8FE4DD]">Panel ejecutivo · datos sintéticos</p>
            <h2 className="mt-3 text-2xl font-black tracking-tight sm:text-3xl">Diagnóstico psicosocial para decisión preventiva</h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/70">Versión {overview?.instrument_version_code || '—'} · {validCount} registros válidos · privacidad n ≥ {overview?.min_publishable_n || 5}. Umbrales exploratorios sin equivalencia oficial.</p>
            <div className="mt-5 flex flex-wrap gap-2">{['Dashboard', 'Dimensiones', '20 subdimensiones', 'Áreas', 'Precisión', 'BSC'].map((label) => <a key={label} href={`#${label.toLowerCase().replace('20 ', '').replace('á', 'a').replace('ó', 'o')}`} className="rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[11px] font-bold text-white/80 backdrop-blur-xl hover:bg-white/20">{label}</a>)}</div>
          </div>
          <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-xl">
            <p className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-white/55">Aplicación analizada</p>
            <div className="mt-3 [&_label]:text-white/70 [&_select]:border-white/20 [&_select]:bg-white/10 [&_select]:text-white"><StudySelector projectId={projectId} studyId={studyId} onStudyChange={setStudyId} /></div>
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs"><div className="rounded-xl bg-black/15 p-3"><span className="block text-white/50">Algoritmo</span><strong className="mt-1 block">CENSOPAS v2</strong></div><div className="rounded-xl bg-black/15 p-3"><span className="block text-white/50">Estado</span><strong className="mt-1 block">Provisional</strong></div></div>
          </div>
        </div>
      </Card>

      {!studyId || loading ? <LoadingState label="Construyendo expediente estadístico…" /> : !dimensions.length ? <Card><EmptyState title="No hay resultados CENSOPAS calculados" description="Ejecuta el scoring del estudio para activar el tablero." /></Card> : <>
        <section id="dashboard" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
          <ExecutiveMetric icon={Users} label="Válidas" value={validCount} detail={`de ${expectedWorkers || 'marco no informado'} trabajadores`} tone="turquoise" />
          <ExecutiveMetric icon={Activity} label="Cobertura" value={coverage === null ? '—' : pct(coverage)} detail="denominador del centro visible" />
          <ExecutiveMetric icon={CheckCircle2} label="Completitud" value={pct((selectedTelemetry?.completion_rate || 0) * 100)} detail={`${selectedTelemetry?.excluded_count || 0} sesiones excluidas`} tone="turquoise" />
          <ExecutiveMetric icon={AlertTriangle} label="Riesgo alto" value={highRiskSubdimensions.length} detail={`de ${subdimensions.length} subdimensiones`} tone="danger" />
          <ExecutiveMetric icon={Target} label="Mayor brecha" value={highestRisk ? pct(highestRisk.unfavorable_pct) : '—'} detail={highestRisk?.construct_name || 'Sin datos'} tone="danger" />
          <ExecutiveMetric icon={Clock} label="Tiempo medio" value={duration(selectedTelemetry?.avg_duration_seconds)} detail="por sesión completada" />
        </section>

        <section id="dimensiones">
          <Card>
            <SectionHeading kicker="8.4 Resultados por dimensión" title="Distribución de niveles y precisión" description="La tabla reproduce el orden de lectura del modelo: denominador, conteos, porcentajes, distribución, puntaje, intervalo de confianza y clasificación." />
            <div className="grid gap-5 xl:grid-cols-[1.55fr_.75fr]">
              <div className="h-[360px] rounded-2xl border border-border bg-white p-4"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartDimensions} layout="vertical" margin={{ left: 18, right: 16 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} /><YAxis dataKey="name" type="category" width={42} /><Tooltip formatter={(value) => pct(value)} /><Legend /><Bar dataKey="favorable" name="Favorable" stackId="risk" fill={COLORS.favorable}><LabelList dataKey="favorable" position="center" formatter={(value) => value >= 9 ? pct(value, 0) : ''} fill="#fff" fontSize={10} /></Bar><Bar dataKey="intermedio" name="Intermedio" stackId="risk" fill={COLORS.intermediate}><LabelList dataKey="intermedio" position="center" formatter={(value) => value >= 9 ? pct(value, 0) : ''} fill="#fff" fontSize={10} /></Bar><Bar dataKey="desfavorable" name="Desfavorable" stackId="risk" fill={COLORS.unfavorable}><LabelList dataKey="desfavorable" position="center" formatter={(value) => value >= 9 ? pct(value, 0) : ''} fill="#fff" fontSize={10} /></Bar></BarChart></ResponsiveContainer></div>
              <div className="h-[360px] rounded-2xl border border-border bg-gradient-to-br from-surfaceSoft to-white p-4"><p className="mb-2 text-center text-xs font-bold text-dark">Índice analítico 0–100</p><ResponsiveContainer width="100%" height="92%"><RadarChart data={radarData}><PolarGrid stroke="#CBD5E1" /><PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fontWeight: 700 }} /><Radar dataKey="riesgo" stroke={COLORS.turquoise} fill={COLORS.turquoise} fillOpacity={0.28} /></RadarChart></ResponsiveContainer></div>
            </div>
            <div className="mt-5"><DimensionTable rows={dimensions} /></div>
            <p className="mt-3 text-[11px] leading-5 text-muted">IC 95%: intervalo de Wilson para la proporción desfavorable. En este demo los umbrales son exploratorios; la equivalencia oficial permanece bloqueada.</p>
          </Card>
        </section>

        <section id="subdimensiones">
          <Card>
            <SectionHeading kicker="8.6–8.7 Subdimensiones" title="Ranking completo de veinte subdimensiones" description="Ordenamiento por porcentaje desfavorable, manteniendo dimensión de origen, n, puntaje y pregunta preventiva." />
            <div className="mb-5 h-[430px] rounded-2xl border border-border bg-white p-4"><ResponsiveContainer width="100%" height="100%"><BarChart data={topTen} layout="vertical" margin={{ left: 120, right: 30 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} /><YAxis dataKey="name" type="category" width={160} tick={{ fontSize: 10 }} /><Tooltip formatter={(value) => pct(value)} /><Bar dataKey="desfavorable" name="% desfavorable" fill={COLORS.unfavorable} radius={[0, 7, 7, 0]}><LabelList dataKey="desfavorable" position="right" formatter={(value) => pct(value)} fill={COLORS.ink} fontSize={10} fontWeight={700} /></Bar></BarChart></ResponsiveContainer></div>
            <SubdimensionTable rows={subdimensions} />
          </Card>
        </section>

        <section id="areas">
          <Card>
            <SectionHeading kicker="8.8–8.9 Localización" title="Mapa de calor por área" description="Porcentaje desfavorable por dimensión y área. Cada encabezado muestra el denominador; las celdas menores al umbral se suprimen desde el backend." />
            {unitDimensionRows.length ? <Heatmap rows={unitDimensionRows} dimensions={dimensions} thresholds={thresholds} /> : <EmptyState title="Sin desglose publicable por área" description="Configura unidades y respeta n ≥ 5 para activar el mapa." />}
            <div className="mt-4 flex flex-wrap gap-3 text-[11px]"><span className="rounded-full bg-[#BDE8D9] px-3 py-1 font-bold text-[#145B4B]">&lt; 25% · menor prioridad</span><span className="rounded-full bg-[#F5C85B] px-3 py-1 font-bold text-[#563B00]">25–49,9% · vigilancia</span><span className="rounded-full bg-[#E05959] px-3 py-1 font-bold text-white">≥ 50% · prioridad alta</span></div>
          </Card>
        </section>

        <section id="precision" className="grid gap-4 xl:grid-cols-[1.05fr_.95fr]">
          <Card>
            <SectionHeading kicker="Calidad" title="Control estadístico y gobernanza" description="El reporte declara qué se calculó, qué falta y qué análisis no debe habilitarse todavía." />
            <QualityTable telemetry={selectedTelemetry} expectedWorkers={expectedWorkers} officialEnabled={censopas?.official_equivalence_enabled} minimumCell={minimumCell} />
          </Card>
          <Card>
            <SectionHeading kicker="Participación" title="Evolución de captura" description="Sesiones iniciadas y completadas por fecha, con el mismo denominador del estudio." />
            <div className="h-[330px]"><ResponsiveContainer width="100%" height="100%"><AreaChart data={selectedTelemetry?.series || []}><defs><linearGradient id="captureGradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor={COLORS.turquoise} stopOpacity={.34} /><stop offset="100%" stopColor={COLORS.turquoise} stopOpacity={.03} /></linearGradient></defs><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" tick={{ fontSize: 10 }} /><YAxis allowDecimals={false} /><Tooltip /><Legend /><Area type="monotone" dataKey="started" name="Iniciadas" stroke={COLORS.intermediate} fill="transparent" strokeWidth={2} /><Area type="monotone" dataKey="completed" name="Completadas" stroke={COLORS.turquoise} fill="url(#captureGradient)" strokeWidth={2.5} /></AreaChart></ResponsiveContainer></div>
          </Card>
        </section>

        <section id="bsc">
          <Card>
            <SectionHeading kicker="Balanced Scorecard" title="Tablero preventivo y cartera de intervención" description="Cada hallazgo se convierte en objetivo, línea base, meta, responsable, plazo e indicador verificable." action={<Link to={`/colmena/project/${projectId}/reports`} className="text-xs font-bold text-amber">Abrir expediente →</Link>} />
            <div className="overflow-x-auto rounded-2xl border border-border bg-white"><table className="min-w-[900px] w-full text-left text-xs"><thead className="bg-[#16363A] text-white"><tr>{['Perspectiva', 'Objetivo', 'Indicador', 'Línea base', 'Meta 90 días', 'Brecha', 'Responsable', 'Semáforo'].map((label) => <th key={label} className="px-3 py-3 font-bold">{label}</th>)}</tr></thead><tbody>{[
              ['Salud y prevención', 'Reducir focos críticos', 'Subdimensiones en riesgo alto', highRiskSubdimensions.length, Math.max(0, highRiskSubdimensions.length - 2), highRiskSubdimensions.length ? '-2' : '0', 'Comité SST', highRiskSubdimensions.length ? 'Rojo' : 'Verde'],
              ['Procesos', 'Elevar participación', 'Cobertura válida', coverage === null ? '—' : pct(coverage), '≥ 90%', coverage === null ? 'Sin marco' : `${number(Math.max(0, 90 - coverage))} pp`, 'RR.HH.', coverage !== null && coverage >= 90 ? 'Verde' : 'Ámbar'],
              ['Liderazgo', 'Cerrar acciones prioritarias', '% acciones verificadas', '0%', '≥ 80%', '80 pp', 'Gerencias de área', 'Rojo'],
              ['Gobernanza', 'Proteger anonimato', 'Celdas publicadas con n ≥ 5', '100%', '100%', '0 pp', 'Responsable de datos', 'Verde'],
            ].map((row) => <tr key={row[1]} className="border-t border-border">{row.slice(0,7).map((cell, index) => <td key={index} className={`px-3 py-3 ${index === 1 ? 'font-semibold text-dark' : index >= 3 && index <= 5 ? 'font-mono' : ''}`}>{cell}</td>)}<td className="px-3 py-3"><span className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${row[7] === 'Verde' ? 'bg-emerald-50 text-emerald-700' : row[7] === 'Ámbar' ? 'bg-amber/15 text-yellowDark' : 'bg-red-50 text-danger'}`}>{row[7]}</span></td></tr>)}</tbody></table></div>

            <div className="mt-5 overflow-x-auto rounded-2xl border border-border bg-white"><table className="min-w-[900px] w-full text-left text-xs"><thead className="bg-surfaceSoft"><tr>{['ID', 'Riesgo prioritario', '% desfavorable', 'Medida organizacional', 'Indicador', 'Responsable', 'Plazo', 'Estado'].map((label) => <th key={label} className="px-3 py-3 font-bold">{label}</th>)}</tr></thead><tbody>{subdimensions.slice(0, 6).map((row, index) => <tr key={row.construct_id} className="border-t border-border"><td className="px-3 py-3 font-mono">A-{String(index + 1).padStart(2, '0')}</td><td className="px-3 py-3 font-semibold text-dark">{row.construct_name}</td><td className="px-3 py-3 font-mono font-bold text-danger">{pct(row.unfavorable_pct)}</td><td className="max-w-[280px] px-3 py-3 text-muted">{actionFor(row.construct_name)}</td><td className="px-3 py-3">Reducción del % desfavorable</td><td className="px-3 py-3">Gerencia + SST</td><td className="px-3 py-3 font-mono">90 días</td><td className="px-3 py-3"><span className="rounded-full bg-red-50 px-2 py-1 text-[10px] font-bold text-danger">Pendiente</span></td></tr>)}</tbody></table></div>
          </Card>
        </section>

        <Card className="border-amber/25 bg-amber/5">
          <div className="flex items-start gap-3"><ShieldCheck className="mt-0.5 shrink-0 text-amber" size={20} /><div><p className="text-sm font-bold text-dark">Lectura metodológica del demo</p><p className="mt-1 text-xs leading-5 text-muted">Los conteos, porcentajes, intervalos y mapas de área provienen de {overview.n_completed} sesiones válidas sintéticas persistidas. La concordancia ítem-subdimensión y los umbrales son exploratorios. No debe presentarse como evaluación oficial ni como expediente SUNAFIL hasta cargar el manifiesto y baremo autorizados.</p></div></div>
        </Card>
      </>}
    </div>
  );
}