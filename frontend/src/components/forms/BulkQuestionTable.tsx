import { useState } from "react";
import { ChevronDown, Search, Trash2 } from "lucide-react";

import type { ParsedQuestion } from "../../utils/bulkQuestionParser";
import type { DimensionDraft } from "../../utils/projectDraftStore";
import { cn } from "../../utils/cn";
import { ResponseEditor } from "./ResponseEditor";

/** Escala proveniente del catálogo del backend (GET /api/v1/scales) */
export type CatalogScale = {
  id: string;
  name: string;
  /** frecuencia | intensidad | acuerdo | dificultad | satisfaccion | personalizada */
  scale_kind?: string;
  points?: number;
  /** null = preset de sistema; string = escala propia de un proyecto */
  project_id?: string | null;
  /** Cómo se ve para el encuestado: radio | slider_line | nps | stars | faces */
  render_style?: string;
  options: { value: number; label: string }[];
};

type Props = {
  questions: ParsedQuestion[];
  selectedIds: string[];
  dimensions: DimensionDraft[];
  /** Catálogo de escalas del backend (presets del sistema + del proyecto) */
  scales: CatalogScale[];
  /** Escala global del instrumento; la heredan los ítems sin escala propia */
  defaultScale?: CatalogScale;
  onToggleSelect: (id: string) => void;
  onToggleAll: () => void;
  onUpdate: (id: string, updates: Partial<ParsedQuestion>) => void;
  onRemove: (id: string) => void;
  onClearSelection: () => void;
};

/** Valida un ítem y devuelve los problemas pendientes (vacío = listo) */
function getItemIssues(q: ParsedQuestion): string[] {
  const issues: string[] = [];
  if (!q.text.trim()) issues.push("Falta el texto de la pregunta");
  // Las variables exógenas (Sexo, Edad…) no pertenecen a una dimensión del constructo.
  if (q.responseKind !== "exogenous" && !q.dimensionName) issues.push("Sin dimensión asignada");
  if (!q.code.trim()) issues.push("Falta el código");
  if (q.responseKind === "exogenous" && (q.exogenousType ?? "single_choice") === "single_choice") {
    const valid = (q.exogenousOptions ?? []).filter((o) => o.label.trim());
    if (valid.length < 2) issues.push("La variable exógena necesita al menos 2 opciones");
  }
  return issues;
}

export function BulkQuestionTable({
  questions,
  selectedIds,
  dimensions,
  scales,
  defaultScale,
  onToggleSelect,
  onToggleAll,
  onUpdate,
  onRemove,
  onClearSelection,
}: Props) {
  const [search, setSearch] = useState("");
  const [knownIds, setKnownIds] = useState(() => questions.map(q => q.id));
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => Object.fromEntries(questions.filter(q => !q.text.trim()).map(q => [q.id, true])));
  if (questions.length !== knownIds.length || questions.some((q, i) => q.id !== knownIds[i])) {
    setKnownIds(questions.map(q => q.id));
    setExpanded(previous => Object.fromEntries(questions.map(q => [q.id, previous[q.id] ?? !knownIds.includes(q.id)])));
    setSearch("");
  }
  if (questions.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-colmena-border py-6 text-center text-[11px] text-muted">
        Tu primera pregunta empieza aquí. Agrega una pregunta Likert o una variable exógena.
      </div>
    );
  }

  const allSelected = selectedIds.length === questions.length;

  /** Escala efectiva: la propia del ítem, o la global heredada */
  const getEffectiveScale = (q: ParsedQuestion): { scale?: CatalogScale; inherited: boolean } => {
    const own = q.scale ? scales.find((s) => s.name === q.scale) : undefined;
    if (own) return { scale: own, inherited: false };
    return { scale: defaultScale, inherited: true };
  };

  /** Aplica un cambio a todos los ítems seleccionados */
  const applyToSelected = (updates: Partial<ParsedQuestion>) => {
    selectedIds.forEach((id) => {
      const q = questions.find(item => item.id === id);
      if (q?.responseKind !== "exogenous") onUpdate(id, updates);
    });
  };

  return (
    <div className="question-list">
      <label className="question-search"><Search size={18} /><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por pregunta, código o dimensión…" aria-label="Buscar preguntas" /></label>
      {/* ── Barra de acciones masivas (aparece al seleccionar) ── */}
      {selectedIds.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-b border-amber/30 bg-amber/5 px-3 py-2 animate-colmena-fade-in">
          <span className="text-[11px] font-bold text-dark">
            {selectedIds.length} {selectedIds.length === 1 ? "ítem" : "ítems"}:
          </span>
          <select
            className="rounded border border-colmena-border bg-white px-1.5 py-1 text-[11px] outline-none hover:border-amber"
            defaultValue=""
            onChange={(e) => {
              if (e.target.value) applyToSelected({ dimensionName: e.target.value });
              e.target.value = "";
            }}
          >
            <option value="">Asignar dimensión…</option>
            {dimensions.map((d) => (
              <option key={d.id} value={d.name}>{d.name}</option>
            ))}
          </select>
          <select
            className="rounded border border-colmena-border bg-white px-1.5 py-1 text-[11px] outline-none hover:border-amber"
            defaultValue=""
            onChange={(e) => {
              if (e.target.value === "__global__") applyToSelected({ scale: "" });
              else if (e.target.value) applyToSelected({ scale: e.target.value });
              e.target.value = "";
            }}
          >
            <option value="">Asignar escala…</option>
            <option value="__global__">Heredar escala global</option>
            {scales.map((s) => (
              <option key={s.id} value={s.name}>{s.name}</option>
            ))}
          </select>
          <button
            type="button"
            className="rounded border border-colmena-border bg-white px-2 py-1 text-[11px] hover:border-amber"
            onClick={() => applyToSelected({ reversed: true })}
          >
            Marcar invertidos
          </button>
          <button
            type="button"
            className="rounded border border-colmena-border bg-white px-2 py-1 text-[11px] hover:border-amber"
            onClick={() => applyToSelected({ reversed: false })}
          >
            Quitar invertido
          </button>
          <button
            type="button"
            className="rounded border border-colmena-border bg-white px-2 py-1 text-[11px] hover:border-amber"
            onClick={() => applyToSelected({ isImportance: true })}
          >
            Marcar como importancia
          </button>
          <button
            type="button"
            className="rounded border border-colmena-border bg-white px-2 py-1 text-[11px] hover:border-amber"
            onClick={() => applyToSelected({ isImportance: false })}
          >
            Quitar importancia
          </button>
          <button
            type="button"
            className="flex items-center gap-1 rounded border border-red-200 bg-red-50 px-2 py-1 text-[11px] text-red-600 hover:bg-red-100"
            onClick={() => {
              if (window.confirm(`¿Eliminar ${selectedIds.length} ${selectedIds.length === 1 ? "ítem" : "ítems"}?`)) {
                selectedIds.forEach((id) => onRemove(id));
              }
            }}
          >
            <Trash2 className="w-3 h-3" />
            Eliminar
          </button>
          <button
            type="button"
            className="ml-auto text-[11px] text-muted underline hover:text-dark"
            onClick={onClearSelection}
          >
            Deseleccionar
          </button>
        </div>
      )}

      <div className="question-list-heading"><label><input checked={allSelected} onChange={onToggleAll} type="checkbox" /> Seleccionar todas</label><span>{questions.length} preguntas</span></div>
      <div className="question-rows">
        {questions.filter(q => `${q.code} ${q.text} ${q.dimensionName}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())).map(q => {
          const issues = getItemIssues(q);
          const { scale: effective, inherited } = getEffectiveScale(q);
          const exogenous = q.responseKind === "exogenous";
          const open = expanded[q.id] ?? false;
          const typeLabel = exogenous ? "Variable exógena" : `Likert · ${effective?.options.length ?? 0} puntos`;
          return <article key={q.id} className={cn("question-row", open && "is-open", selectedIds.includes(q.id) && "is-selected")}>
            <div className="question-row-summary">
              <input aria-label={`Seleccionar ${q.code}`} checked={selectedIds.includes(q.id)} onChange={() => onToggleSelect(q.id)} type="checkbox" />
              <button type="button" className="question-row-main" aria-expanded={open} aria-controls={`editor-${q.id}`} onClick={() => setExpanded(prev => ({ ...prev, [q.id]: !open }))}>
                <span className={cn("question-code", exogenous && "is-exogenous")}>{q.code || "?"}</span>
                <span className="question-row-copy"><strong>{q.text || "Escribe tu pregunta"}</strong><span>{exogenous ? "Dato del participante" : q.dimensionName || "Sin dimensión"}{q.required ? " · Obligatoria" : " · Opcional"}{issues.length > 0 ? " · Por completar" : ""}</span></span>
                <span className={cn("question-type-pill", exogenous && "is-exogenous")}>{typeLabel}<ChevronDown size={14} className={open ? "question-chevron-open" : ""} /></span>
              </button>
              <button type="button" aria-label={`Eliminar ${q.code}`} className="question-icon-button" onClick={() => { if (window.confirm("¿Eliminar esta pregunta?")) onRemove(q.id); }}><Trash2 size={16} /></button>
            </div>
            {open && <div id={`editor-${q.id}`} className="question-row-editor">
              <div className="question-field-grid question-text-fields"><label>Código<input value={q.code} onChange={e => onUpdate(q.id, { code: e.target.value })} /></label><label>Pregunta<textarea rows={2} placeholder="Escribe el texto de la pregunta…" value={q.text} onChange={e => onUpdate(q.id, { text: e.target.value })} /></label></div>
              <ResponseEditor question={q} effectiveScale={effective} inherited={inherited} scales={scales} defaultScale={defaultScale} onUpdate={updates => onUpdate(q.id, updates)} />
              <div className="question-secondary-controls">
                {!exogenous && <label>Dimensión<select aria-label="Dimensión" value={q.dimensionName || ""} onChange={e => onUpdate(q.id, { dimensionName: e.target.value })}><option value="">Seleccionar dimensión</option>{dimensions.map(d => <option key={d.id} value={d.name}>{d.name}</option>)}</select></label>}
                <label className="question-check"><input type="checkbox" checked={q.required} onChange={e => onUpdate(q.id, { required: e.target.checked })} /> Obligatoria</label>
                {!exogenous && <><label className="question-check"><input type="checkbox" checked={q.reversed} onChange={e => onUpdate(q.id, { reversed: e.target.checked })} /> Puntuación invertida</label><label className="question-check"><input type="checkbox" checked={q.isImportance} onChange={e => onUpdate(q.id, { isImportance: e.target.checked })} /> Importancia</label></>}
              </div>
              {issues.length > 0 && <p className="question-helper">Pendiente: {issues.join(" · ")}</p>}
              <div className="question-editor-footer"><button type="button" className="question-button" onClick={() => setExpanded(prev => ({ ...prev, [q.id]: false }))}>Listo</button></div>
            </div>}
          </article>;
        })}
        {search && !questions.some(q => `${q.code} ${q.text} ${q.dimensionName}`.toLocaleLowerCase().includes(search.toLocaleLowerCase())) && <p className="question-empty">No hay preguntas que coincidan con tu búsqueda.</p>}
      </div>

      {/* ── Footer ── */}
      <div className="flex items-center justify-between px-3 py-1.5 border-t border-colmena-border bg-colmena-bg">
        <span className="text-[10px] font-semibold text-dark">
          {selectedIds.length}/{questions.length} sel
        </span>
        <span className="text-[10px] text-muted">
          {questions.filter((q) => getItemIssues(q).length === 0).length}/{questions.length} listos para publicar
        </span>
      </div>
    </div>
  );
}

