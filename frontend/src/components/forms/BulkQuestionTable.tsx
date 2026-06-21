import type { ParsedQuestion } from "../../utils/bulkQuestionParser";
import type { DimensionDraft } from "../../utils/projectDraftStore";
import { cn } from "../../utils/cn";

type Props = {
  questions: ParsedQuestion[];
  selectedIds: string[];
  dimensions: DimensionDraft[];
  defaultScaleName?: string;
  onToggleSelect: (id: string) => void;
  onToggleAll: () => void;
  onUpdate: (id: string, updates: Partial<ParsedQuestion>) => void;
};

export function BulkQuestionTable({
  questions,
  selectedIds,
  dimensions,
  defaultScaleName,
  onToggleSelect,
  onToggleAll,
  onUpdate
}: Props) {
  if (questions.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-colmena-border py-6 text-center text-[11px] text-muted">
        Sin ítems cargados. Pega desde Excel arriba o agrega manualmente.
      </div>
    );
  }

  const allSelected = selectedIds.length === questions.length;

  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-hidden rounded-xl border border-colmena-border bg-white shadow-sm">
      {/* Header */}
      <div className="grid grid-cols-[32px_64px_minmax(180px,2fr)_1.2fr_1.2fr_44px_44px_56px] gap-1 border-b border-colmena-border bg-colmena-bg px-2 py-1.5 text-[10px] font-bold uppercase tracking-[0.08em] text-muted">
        <div className="flex items-center justify-center">
          <input checked={allSelected} onChange={onToggleAll} type="checkbox" className="rounded" />
        </div>
        <span>Cód</span>
        <span>Ítem</span>
        <span>Dimensión</span>
        <span>Escala</span>
        <span className="text-center">Inv</span>
        <span className="text-center">Req</span>
        <span className="text-center">Est</span>
      </div>

      {/* Rows */}
      <div className="flex-1 divide-y divide-colmena-border overflow-y-auto">
        {questions.map((q) => {
          const isSelected = selectedIds.includes(q.id);
          const isReady = q.status === "ready";
          const hasCustomScale = !!q.scale;
          const displayScale = q.scale || defaultScaleName || "—";

          return (
            <div
              className={cn(
                "grid grid-cols-[32px_64px_minmax(180px,2fr)_1.2fr_1.2fr_44px_44px_56px] gap-1 px-2 py-1 text-[11px] hover:bg-amber/3 items-center transition-colors",
                isSelected && "bg-amber/3"
              )}
              key={q.id}
            >
              <div className="flex items-center justify-center">
                <input checked={isSelected} onChange={() => onToggleSelect(q.id)} type="checkbox" className="rounded" />
              </div>
              <input
                className="w-full bg-white outline-none font-medium text-dark border border-colmena-border hover:border-amber focus:border-amber rounded px-1.5 py-1 text-[11px] shadow-sm transition-all"
                value={q.code}
                onChange={(e) => onUpdate(q.id, { code: e.target.value })}
              />
              <input
                className="w-full bg-white outline-none text-dark border border-colmena-border hover:border-amber focus:border-amber rounded px-1.5 py-1 text-[11px] shadow-sm transition-all"
                value={q.text}
                onChange={(e) => onUpdate(q.id, { text: e.target.value })}
              />
              {/* Elegant Dimension Dropdown Selector */}
              <div className="px-1">
                <select
                  className="w-full bg-white outline-none text-dark font-medium cursor-pointer border border-colmena-border hover:border-amber focus:border-amber rounded px-1 py-1 text-[11px] shadow-sm transition-all"
                  value={q.dimensionName || ""}
                  onChange={(e) => onUpdate(q.id, { dimensionName: e.target.value })}
                >
                  <option value="">— Sin asignar —</option>
                  {dimensions.map((d) => (
                    <option key={d.id} value={d.name}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>
              {/* Inherited or Customized Scale Display */}
              <div className="px-1">
                <input
                  className={cn(
                    "w-full bg-white outline-none border border-colmena-border hover:border-amber focus:border-amber rounded px-1.5 py-1 text-[11px] shadow-sm transition-all",
                    hasCustomScale ? "text-dark font-medium" : "text-muted/70 italic"
                  )}
                  value={displayScale}
                  placeholder={defaultScaleName || "—"}
                  onChange={(e) => onUpdate(q.id, { scale: e.target.value })}
                />
              </div>
              <div className="flex justify-center">
                <input type="checkbox" checked={q.reversed} onChange={(e) => onUpdate(q.id, { reversed: e.target.checked })} />
              </div>
              <div className="flex justify-center">
                <input type="checkbox" checked={q.required} onChange={(e) => onUpdate(q.id, { required: e.target.checked })} />
              </div>
              <div className="flex justify-center">
                <span className={cn(
                  "inline-flex rounded px-1.5 py-0.5 text-[9px] font-bold leading-none",
                  isReady ? "bg-success/10 text-success" : "bg-warning/10 text-warning"
                )}>
                  {isReady ? "OK" : "Rev"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-3 py-1.5 border-t border-colmena-border bg-colmena-bg">
        <span className="text-[10px] font-semibold text-dark">{selectedIds.length}/{questions.length} sel</span>
        <span className="text-[10px] text-muted">{questions.filter(q => q.status === "ready").length} listos</span>
      </div>
    </div>
  );
}
