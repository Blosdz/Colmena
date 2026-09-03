import { Trash2 } from "lucide-react";

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
  if (questions.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-colmena-border py-6 text-center text-[11px] text-muted">
        Sin ítems cargados. Pega desde Excel arriba o agrega manualmente.
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
    selectedIds.forEach((id) => onUpdate(id, updates));
  };

  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-hidden rounded-xl border border-colmena-border bg-white shadow-sm">
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

      {/* ── Header ── */}
      <div className="flex items-center gap-2 border-b border-colmena-border bg-colmena-bg px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.08em] text-muted">
        <input checked={allSelected} onChange={onToggleAll} type="checkbox" className="rounded" />
        <span>Seleccionar todos</span>
      </div>

      {/* ── Tarjetas por ítem: pregunta arriba, escala completa debajo ── */}
      <div className="flex-1 divide-y divide-colmena-border overflow-y-auto">
        {questions.map((q, index) => {
          const isSelected = selectedIds.includes(q.id);
          const issues = getItemIssues(q);
          const isReady = issues.length === 0;
          const { scale: effective, inherited } = getEffectiveScale(q);

          return (
            <div key={q.id} className={cn("p-3 space-y-2.5 transition-colors", isSelected && "bg-amber/3")}>
              {/* Encabezado: selección, código, estado */}
              <div className="flex items-center gap-2">
                <input checked={isSelected} onChange={() => onToggleSelect(q.id)} type="checkbox" className="rounded shrink-0" />
                <input
                  className="w-16 shrink-0 bg-white outline-none font-medium text-dark border border-colmena-border hover:border-amber focus:border-amber rounded px-1.5 py-1 text-[11px] shadow-sm transition-all"
                  value={q.code}
                  onChange={(e) => onUpdate(q.id, { code: e.target.value })}
                />
                <span
                  className={cn(
                    "inline-flex shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold leading-none cursor-help",
                    isReady ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
                  )}
                  title={isReady ? "Ítem completo" : issues.join(" · ")}
                >
                  {isReady ? "OK" : "Rev"}
                </span>
                <span className="text-[10px] text-muted ml-auto shrink-0">Ítem {index + 1}</span>
                <button
                  type="button"
                  title="Eliminar ítem"
                  className="shrink-0 p-1 text-muted hover:text-danger transition-colors"
                  onClick={() => {
                    if (window.confirm("¿Eliminar este ítem?")) onRemove(q.id);
                  }}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Pregunta */}
              <input
                className="w-full bg-white outline-none text-dark border border-colmena-border hover:border-amber focus:border-amber rounded-lg px-3 py-2 text-[14px] font-semibold shadow-sm transition-all"
                placeholder="Escribe el texto de la pregunta…"
                value={q.text}
                onChange={(e) => onUpdate(q.id, { text: e.target.value })}
              />

              {/* Editor de respuesta modular: escala Likert o variable exógena */}
              <ResponseEditor
                question={q}
                effectiveScale={effective}
                inherited={inherited}
                scales={scales}
                defaultScale={defaultScale}
                onUpdate={(updates) => onUpdate(q.id, updates)}
              />
              {q.responseKind !== "exogenous" && q.reversed && effective && effective.options.length > 1 && (
                <p className="text-[10px] text-muted">
                  Invertido: "{effective.options[0].label}" puntúa {effective.options[effective.options.length - 1].value} y "
                  {effective.options[effective.options.length - 1].label}" puntúa {effective.options[0].value}.
                </p>
              )}

              {/* Controles secundarios: dimensión + flags */}
              <div className="flex flex-wrap items-center gap-2">
                {q.responseKind !== "exogenous" && (
                  <select
                    className={cn(
                      "bg-white outline-none font-medium cursor-pointer border rounded px-1.5 py-1 text-[11px] shadow-sm transition-all hover:border-amber focus:border-amber",
                      q.dimensionName ? "border-colmena-border text-dark" : "border-warning/50 text-warning"
                    )}
                    value={q.dimensionName || ""}
                    onChange={(e) => onUpdate(q.id, { dimensionName: e.target.value })}
                  >
                    <option value="">— Sin asignar —</option>
                    {dimensions.map((d) => (
                      <option key={d.id} value={d.name}>{d.name}</option>
                    ))}
                  </select>
                )}

                {q.responseKind !== "exogenous" && (
                  <label className="inline-flex items-center gap-1 text-[11px] text-muted" title="Ítem invertido: se recodifica al puntuar">
                    <input type="checkbox" checked={q.reversed} onChange={(e) => onUpdate(q.id, { reversed: e.target.checked })} />
                    Invertido
                  </label>
                )}
                <label className="inline-flex items-center gap-1 text-[11px] text-muted" title="Respuesta obligatoria">
                  <input type="checkbox" checked={q.required} onChange={(e) => onUpdate(q.id, { required: e.target.checked })} />
                  Requerido
                </label>
                {q.responseKind !== "exogenous" && (
                  <label className="inline-flex items-center gap-1 text-[11px] text-muted" title="Ítem de importancia (para el gráfico Stewart)">
                    <input type="checkbox" checked={q.isImportance} onChange={(e) => onUpdate(q.id, { isImportance: e.target.checked })} />
                    Importancia
                  </label>
                )}
              </div>
            </div>
          );
        })}
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

