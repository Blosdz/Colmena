import { Zap, Plus, Trash2, RefreshCw, Save } from "lucide-react";
import { useEffect, useState } from "react";
import {
  calculateEqualRangeBaremos,
  validateBaremoGaps,
  type BaremoLevel,
} from "../../utils/baremoCalculator";
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

const PALETTE = ["#DC2626", "#F5B21A", "#11B7B2", "#059669", "#2563EB", "#7C3AED"];

export function BaremoAutoBuilder({
  items,
  scaleMin,
  scaleMax,
  dimensions,
  baremos,
  onChange,
  onDimensionBaremosChange,
}: Props) {
  const [levelsCount, setLevelsCount] = useState(baremos.length >= 2 ? baremos.length : 5);
  // Checklist de alcance: solo se muestran/calculan los baremos activados.
  const [byVariable, setByVariable] = useState(baremos.length > 0);
  const [byDimension, setByDimension] = useState(dimensions.some((d) => d.baremos.length > 0));

  // Los puntajes se normalizan a 0-100 (estilo COLMENA 2.0): los baremos van
  // siempre sobre 0-100, sin importar el nº de ítems ni la escala Likert.
  const totalMin = 0;
  const totalMax = 100;
  const dimCount = (dim: DimensionDraft) => items.filter((i) => i.dimensionName === dim.name).length;

  const genVariable = (n = levelsCount) =>
    onChange(calculateEqualRangeBaremos(0, 100, n, "mean"));
  const genDimension = (dim: DimensionDraft, n = levelsCount) => {
    const c = dimCount(dim);
    if (c > 0) onDimensionBaremosChange(dim.id, calculateEqualRangeBaremos(0, 100, n, "mean"));
  };

  const toggleVariable = (checked: boolean) => {
    setByVariable(checked);
    if (checked) {
      if (baremos.length === 0 && items.length > 0) genVariable();
    } else {
      onChange([]); // desactivar → no se guarda ni se muestra
    }
  };

  const toggleDimension = (checked: boolean) => {
    setByDimension(checked);
    dimensions.forEach((d) => {
      if (checked) {
        if (d.baremos.length === 0) genDimension(d);
      } else {
        onDimensionBaremosChange(d.id, []);
      }
    });
  };

  const changeLevels = (n: number) => {
    const safe = Math.max(2, Math.min(10, n || 2));
    setLevelsCount(safe);
    if (byVariable && items.length > 0) genVariable(safe);
    if (byDimension) dimensions.forEach((d) => genDimension(d, safe));
  };

  const recalcAll = () => {
    if (byVariable && items.length > 0) genVariable();
    if (byDimension) dimensions.forEach((d) => genDimension(d));
  };

  const nothingActive = !byVariable && !byDimension;

  return (
    <div className="space-y-4">
      {/* ── Controles: niveles + checklist de alcance + rango en vivo ── */}
      <div className="rounded-xl border border-colmena-border bg-white p-3 space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-32">
            <label className="colmena-label">Niveles</label>
            <input
              type="number"
              className="colmena-input w-full"
              value={levelsCount}
              onChange={(e) => changeLevels(Number(e.target.value))}
              min={2}
              max={10}
            />
          </div>

          <div className="flex-1 min-w-[180px]">
            <label className="colmena-label">Rango de la variable (en vivo)</label>
            <div className="colmena-input w-full flex items-center gap-2 bg-colmena-bg cursor-default text-[12px]">
              {items.length > 0 ? (
                <>
                  <span className="font-bold text-dark">
                    mín {totalMin} · máx {totalMax}
                  </span>
                  <span className="text-[10px] text-muted">
                    (puntaje normalizado 0–100 · {items.length} ítems, escala {scaleMin}–{scaleMax})
                  </span>
                </>
              ) : (
                <span className="text-muted">Sin ítems aún</span>
              )}
            </div>
          </div>

          <button
            className="colmena-button-sm-primary shrink-0 flex items-center gap-1.5 disabled:opacity-40"
            onClick={recalcAll}
            disabled={items.length === 0 || nothingActive}
            title="Recalcular con el rango actual"
          >
            <Zap className="w-3.5 h-3.5" />
            Recalcular
          </button>
        </div>

        {/* Checklist de alcance */}
        <div className="flex flex-wrap items-center gap-4 pt-1 border-t border-colmena-border">
          <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-muted">Calcular baremos por:</span>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              className="accent-amber w-4 h-4"
              checked={byVariable}
              onChange={(e) => toggleVariable(e.target.checked)}
            />
            <span className="text-[12px] font-medium text-dark">Variable</span>
          </label>
          <label className={`flex items-center gap-2 ${dimensions.length === 0 ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}`}>
            <input
              type="checkbox"
              className="accent-amber w-4 h-4"
              checked={byDimension}
              disabled={dimensions.length === 0}
              onChange={(e) => toggleDimension(e.target.checked)}
            />
            <span className="text-[12px] font-medium text-dark">
              Dimensión {dimensions.length > 0 ? `(${dimensions.length})` : "(sin dimensiones)"}
            </span>
          </label>
        </div>
      </div>

      {/* ── Tabla: baremos de la Variable ── */}
      {byVariable && (
        <BaremoTable
          title="Baremos de la Variable"
          subtitle={`${items.length} ítems`}
          rangeMin={totalMin}
          rangeMax={totalMax}
          baremos={baremos}
          onChange={onChange}
          onRecalculate={() => genVariable()}
        />
      )}

      {/* ── Tablas: baremos por Dimensión ── */}
      {byDimension &&
        dimensions.map((dim) => {
          const c = dimCount(dim);
          return (
            <BaremoTable
              key={dim.id}
              title={dim.name}
              subtitle={`${c} ítems`}
              rangeMin={0}
              rangeMax={100}
              baremos={dim.baremos}
              onChange={(b) => onDimensionBaremosChange(dim.id, b)}
              onRecalculate={() => genDimension(dim)}
            />
          );
        })}

      {nothingActive && (
        <div className="rounded-lg border border-dashed border-colmena-border py-4 text-center text-[11px] text-muted">
          Marca <strong>Variable</strong> o <strong>Dimensión</strong> arriba para generar y editar sus baremos.
        </div>
      )}
    </div>
  );
}

// ── Tabla de baremos reutilizable (editable + agregar/quitar niveles) ──

function BaremoTable({
  title,
  subtitle,
  rangeMin,
  rangeMax,
  baremos,
  onChange,
  onRecalculate,
}: {
  title: string;
  subtitle: string;
  rangeMin: number;
  rangeMax: number;
  baremos: BaremoLevel[];
  onChange: (b: BaremoLevel[]) => void;
  onRecalculate: () => void;
}) {
  // Borrador local: las ediciones se confirman con "Guardar", no en cada tecla.
  const [draft, setDraft] = useState<BaremoLevel[]>(baremos);
  useEffect(() => {
    setDraft(baremos);
  }, [baremos]);

  const dirty = JSON.stringify(draft) !== JSON.stringify(baremos);
  const validation = validateBaremoGaps(draft);

  // "Stale": el baremo guardado no cubre el rango actual (cambiaron ítems/escala).
  const coveredMin = baremos.length ? Math.min(...baremos.map((b) => b.min)) : null;
  const coveredMax = baremos.length ? Math.max(...baremos.map((b) => b.max)) : null;
  const isStale = baremos.length > 0 && (coveredMin !== rangeMin || coveredMax !== rangeMax);

  const patch = (index: number, updates: Partial<BaremoLevel>) => {
    setDraft((prev) => prev.map((b, i) => (i === index ? { ...b, ...updates } : b)));
  };

  const addLevel = () => {
    const lastMax = draft.length ? Math.max(...draft.map((b) => b.max)) : rangeMin - 0.1;
    const newMin = Math.round((lastMax + 0.1) * 10) / 10;
    setDraft((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        name: `Nivel ${prev.length + 1}`,
        min: newMin,
        max: Math.max(newMin, rangeMax),
        description: "",
        color: PALETTE[prev.length % PALETTE.length],
      },
    ]);
  };

  const removeLevel = (id: string) => setDraft((prev) => prev.filter((b) => b.id !== id));

  return (
    <div className="rounded-xl border border-colmena-border bg-white overflow-hidden">
      <div className="flex items-center justify-between gap-2 px-3 py-2 bg-colmena-bg border-b border-colmena-border">
        <div className="flex items-baseline gap-2 min-w-0">
          <span className="text-[11px] font-bold text-dark truncate">{title}</span>
          <span className="text-[10px] text-muted shrink-0">{subtitle}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] font-semibold text-muted">
            rango {rangeMin}–{rangeMax}
          </span>
          {dirty && (
            <button
              onClick={() => onChange(draft)}
              title="Guardar los cambios de este baremo"
              className="inline-flex items-center gap-1 rounded-md bg-amber px-2 py-1 text-[10px] font-bold text-white hover:bg-amber/90 transition-colors"
            >
              <Save className="w-3 h-3" />
              Guardar
            </button>
          )}
          <button
            onClick={onRecalculate}
            title="Recalcular niveles con el rango actual"
            className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-semibold transition-colors ${
              isStale ? "bg-warning/15 text-warning" : "bg-white text-muted hover:text-amber border border-colmena-border"
            }`}
          >
            <RefreshCw className="w-3 h-3" />
            {isStale ? "Rango cambió · Recalcular" : "Recalcular"}
          </button>
        </div>
      </div>

      {dirty && (
        <div className="px-3 py-1 bg-amber/5 text-amber text-[10px] border-b border-amber/10">
          Tienes cambios sin guardar en este baremo.
        </div>
      )}

      {!validation.valid && (
        <div className="px-3 py-1.5 bg-danger/5 text-danger text-[10px] border-b border-danger/10">
          {validation.issues.join(" · ")}
        </div>
      )}

      <div className="divide-y divide-colmena-border">
        {draft.map((lvl, index) => (
          <div
            key={lvl.id}
            className="grid grid-cols-[16px_1fr_70px_14px_70px_28px] gap-2 px-3 py-1.5 items-center hover:bg-colmena-bg/50 transition-colors"
          >
            <input
              type="color"
              className="w-4 h-4 rounded-full border-0 bg-transparent cursor-pointer p-0 shrink-0"
              value={lvl.color}
              onChange={(e) => patch(index, { color: e.target.value })}
              title="Color"
            />
            <input
              className="bg-transparent text-[12px] font-semibold text-dark outline-none w-full"
              value={lvl.name}
              onChange={(e) => patch(index, { name: e.target.value })}
            />
            <input
              type="number"
              step="0.1"
              className="bg-transparent text-[12px] text-dark outline-none text-center w-full"
              value={lvl.min}
              onChange={(e) => patch(index, { min: Number(e.target.value) })}
            />
            <span className="text-[10px] text-muted text-center">–</span>
            <input
              type="number"
              step="0.1"
              className="bg-transparent text-[12px] text-dark outline-none text-center w-full"
              value={lvl.max}
              onChange={(e) => patch(index, { max: Number(e.target.value) })}
            />
            <button
              onClick={() => removeLevel(lvl.id)}
              title="Quitar nivel"
              className="shrink-0 p-1 text-muted hover:text-danger transition-colors flex justify-center disabled:opacity-30"
              disabled={draft.length <= 2}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      <div className="px-3 py-2 border-t border-colmena-border">
        <button
          onClick={addLevel}
          className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-amber hover:text-amber/80"
        >
          <Plus className="w-3 h-3" /> Agregar nivel
        </button>
      </div>
    </div>
  );
}
