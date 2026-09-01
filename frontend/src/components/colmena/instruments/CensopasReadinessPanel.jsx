import { AlertCircle, CheckCircle2, ShieldCheck } from 'lucide-react';

const COUNT_FIELDS = [
  ['Preguntas', 'questions'],
  ['Puntuables', 'scored'],
  ['Dimensiones', 'dimensions'],
  ['Subdimensiones', 'subdimensions'],
];

const ERROR_LABELS = {
  UNSUPPORTED_CENSOPAS_VERSION: 'La versión del instrumento no se reconoce como CENSOPAS corta ni media.',
  QUESTIONS_COUNT_MISMATCH: 'El número de preguntas no coincide con lo esperado para esta versión.',
  SCORED_COUNT_MISMATCH: 'El número de ítems puntuables no coincide con lo esperado.',
  DESCRIPTIVE_COUNT_MISMATCH: 'El número de preguntas descriptivas no coincide con lo esperado.',
  DIMENSIONS_COUNT_MISMATCH: 'El número de dimensiones no coincide con lo esperado.',
  SUBDIMENSIONS_COUNT_MISMATCH: 'El número de subdimensiones no coincide con lo esperado.',
  SCORED_QUESTIONS_OUTSIDE_DIMENSION_TREE: 'Hay preguntas puntuables sin enlazar a ninguna dimensión o subdimensión.',
  NON_SCORED_QUESTIONS_IN_SCORING_MATRIX: 'Hay preguntas enlazadas a un constructo que no están marcadas como puntuables.',
  MISSING_VALIDATED_SCORING_RULES: 'Faltan reglas de puntuación validadas para uno o más ítems puntuables.',
  EMPTY_SCORING_CONSTRUCTS: 'Una dimensión o subdimensión hoja todavía no tiene ítems enlazados.',
};

const WARNING_LABELS = {
  OFFICIAL_BAREM_NOT_AVAILABLE: 'Todavía no hay un baremo oficial activo — puedes generar resultados provisionales.',
  OFFICIAL_BAREM_INCOMPLETE: 'El baremo oficial existe pero no cubre todos los constructos puntuables.',
  OFFICIAL_EQUIVALENCE_DISABLED: 'La equivalencia oficial está deshabilitada para este instrumento.',
};

/** Checklist en vivo de `GET /instrument-versions/{id}/censopas/readiness`. */
export default function CensopasReadinessPanel({ readiness, isLoading }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck size={18} className="text-turquoise" />
          <div>
            <p className="text-sm font-semibold text-dark">Preparación CENSOPAS-COPSOQ</p>
            <p className="text-xs text-muted">
              {isLoading ? 'Verificando estructura…' : 'Versión ' + (readiness?.version_kind || 'desconocida')}
            </p>
          </div>
        </div>
        {readiness ? (
          <span className={'colmena-badge ' + (readiness.ready_for_scoring ? 'bg-turquoise/10 text-turquoise' : 'bg-danger/10 text-danger')}>
            {readiness.ready_for_scoring ? 'Listo para scoring' : 'Configuración incompleta'}
          </span>
        ) : null}
      </div>
      {readiness ? (
        <>
          <div className="grid gap-2 sm:grid-cols-4">
            {COUNT_FIELDS.map(([label, key]) => {
              const matches = readiness.actual?.[key] === readiness.expected?.[key];
              return (
                <div key={key} className="rounded-xl border border-border bg-background/60 p-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</p>
                  <p className={'mt-1 text-sm font-bold ' + (matches ? 'text-dark' : 'text-danger')}>
                    {readiness.actual?.[key] ?? 0} / {readiness.expected?.[key] ?? '—'}
                  </p>
                </div>
              );
            })}
          </div>

          {readiness.errors?.length ? (
            <ul className="mt-3 flex flex-col gap-1.5">
              {readiness.errors.map((code) => (
                <li key={code} className="flex items-start gap-2 rounded-xl border border-danger/20 bg-danger/5 px-3 py-2 text-xs text-danger">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  <span>{ERROR_LABELS[code] || code}</span>
                </li>
              ))}
            </ul>
          ) : null}

          {readiness.warnings?.length ? (
            <ul className="mt-2 flex flex-col gap-1.5">
              {readiness.warnings.map((code) => (
                <li key={code} className="flex items-start gap-2 rounded-xl border border-amber/20 bg-yellowSoft px-3 py-2 text-xs text-yellowDark">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  <span>{WARNING_LABELS[code] || code}</span>
                </li>
              ))}
            </ul>
          ) : null}

          <div className="mt-3 flex items-start gap-2 rounded-xl border border-border px-3 py-2">
            {readiness.ready_for_official_reporting ? (
              <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-turquoise" />
            ) : (
              <AlertCircle size={16} className="mt-0.5 shrink-0 text-amber" />
            )}
            <p className="text-xs text-muted">
              {readiness.ready_for_official_reporting
                ? 'Equivalencia oficial habilitada y baremo completo.'
                : 'La salida oficial está bloqueada. Puedes generar un documento provisional claramente etiquetado.'}
            </p>
          </div>
        </>
      ) : null}
    </div>
  );
}
