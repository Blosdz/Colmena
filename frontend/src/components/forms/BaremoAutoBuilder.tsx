import { Zap } from "lucide-react";
import { useState } from "react";
import { validateBaremoGaps, type BaremoLevel } from "../../utils/baremoCalculator";
import type { DimensionDraft } from "../../utils/projectDraftStore";
import type { ParsedQuestion } from "../../utils/bulkQuestionParser";

type Props = {
  items: ParsedQuestion[];
  scaleMin: number;
  scaleMax: number;
  dimensions: DimensionDraft[];
  baremos: BaremoLevel[];
  onChange: (baremos: BaremoLevel[]) => void;
  onAutoGenerate: (levels: number) => void;
  onDimensionBaremosChange: (dimId: string, baremos: BaremoLevel[]) => void;
};

export function BaremoAutoBuilder({ items, scaleMin, scaleMax, dimensions, baremos, onChange, onAutoGenerate, onDimensionBaremosChange }: Props) {
  const [levelsCount, setLevelsCount] = useState(5);

  const totalMin = items.length * scaleMin;
  const totalMax = items.length * scaleMax;

  const validation = validateBaremoGaps(baremos);

  return (
    <div className="space-y-4">
      {/* Auto-generate controls */}
      <div className="flex items-end gap-2 p-3 rounded-lg border border-colmena-border bg-white">
        <div className="flex-1">
          <label className="colmena-label">Niveles de calificación</label>
          <input type="number" className="colmena-input w-full" value={levelsCount} onChange={(e) => setLevelsCount(Number(e.target.value))} min={2} max={10} />
        </div>
        <div className="flex-1">
          <label className="colmena-label">Rango Variable</label>
          <div className="colmena-input w-full flex items-center text-[12px] text-muted bg-colmena-bg cursor-default">
            {items.length > 0 ? `${totalMin} – ${totalMax}` : "Sin ítems"} <span className="ml-1 text-[10px]">({items.length} ítems × {scaleMin}–{scaleMax})</span>
          </div>
        </div>
        <button
          className="colmena-button-sm-primary shrink-0 flex items-center gap-1.5"
          onClick={() => onAutoGenerate(levelsCount)}
          disabled={items.length === 0}
        >
          <Zap className="w-3.5 h-3.5" />
          Auto-calcular todo
        </button>
      </div>

      {/* Variable baremos */}
      {baremos.length > 0 && (
        <BaremoTable
          title={`Baremos de la Variable (${items.length} ítems)`}
          baremos={baremos}
          onChange={onChange}
          validation={validation}
        />
      )}

      {/* Dimension baremos */}
      {dimensions.map((dim) => {
        const dimItems = items.filter(i => i.dimensionName === dim.name);
        if (dim.baremos.length === 0) return null;
        const dimValidation = validateBaremoGaps(dim.baremos);

        return (
          <BaremoTable
            key={dim.id}
            title={`${dim.name} (${dimItems.length} ítems)`}
            baremos={dim.baremos}
            onChange={(b) => onDimensionBaremosChange(dim.id, b)}
            validation={dimValidation}
          />
        );
      })}

      {baremos.length === 0 && (
        <div className="rounded-lg border border-dashed border-colmena-border py-4 text-center text-[11px] text-muted">
          Presiona <strong>Auto-calcular todo</strong> para generar baremos de la variable y todas sus dimensiones.
        </div>
      )}
    </div>
  );
}

// ── Reusable baremo table ──────────────────────────────

function BaremoTable({ title, baremos, onChange, validation }: {
  title: string;
  baremos: BaremoLevel[];
  onChange: (b: BaremoLevel[]) => void;
  validation: { valid: boolean; issues: string[] };
}) {
  return (
    <div className="rounded-xl border border-colmena-border bg-white overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-colmena-bg border-b border-colmena-border">
        <span className="text-[11px] font-bold text-dark">{title}</span>
        <span className="text-[9px] text-muted">{baremos.length} niveles</span>
      </div>

      {!validation.valid && (
        <div className="px-3 py-1.5 bg-danger/5 text-danger text-[10px] border-b border-danger/10">
          {validation.issues.join(" · ")}
        </div>
      )}

      <div className="divide-y divide-colmena-border">
        {baremos.map((lvl, index) => (
          <div key={lvl.id} className="grid grid-cols-[20px_1fr_72px_20px_72px] gap-2 px-3 py-1.5 items-center hover:bg-colmena-bg/50 transition-colors">
            <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: lvl.color }} />
            <input
              className="bg-transparent text-[12px] font-semibold text-dark outline-none w-full"
              value={lvl.name}
              onChange={(e) => {
                const next = [...baremos];
                next[index] = { ...next[index], name: e.target.value };
                onChange(next);
              }}
            />
            <input
              type="number" step="0.1"
              className="bg-transparent text-[12px] text-dark outline-none text-center w-full"
              value={lvl.min}
              onChange={(e) => {
                const next = [...baremos];
                next[index] = { ...next[index], min: Number(e.target.value) };
                onChange(next);
              }}
            />
            <span className="text-[10px] text-muted text-center">–</span>
            <input
              type="number" step="0.1"
              className="bg-transparent text-[12px] text-dark outline-none text-center w-full"
              value={lvl.max}
              onChange={(e) => {
                const next = [...baremos];
                next[index] = { ...next[index], max: Number(e.target.value) };
                onChange(next);
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
