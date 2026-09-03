import { useState } from "react";
import { ChevronDown, Pencil, SlidersHorizontal } from "lucide-react";

import type { VariableDraft, ScaleDraft } from "../../utils/projectDraftStore";
import type { ParsedQuestion } from "../../utils/bulkQuestionParser";
import { BulkQuestionImporter } from "./BulkQuestionImporter";
import { BulkQuestionTable, type CatalogScale } from "./BulkQuestionTable";
import { ScaleBuilder } from "./ScaleBuilder";

type Props = {
  variable: VariableDraft;
  catalogScales: CatalogScale[];
  defaultScale?: CatalogScale;
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onToggleAll: () => void;
  onClearSelection: () => void;
  onAddItems: (items: ParsedQuestion[]) => void;
  onUpdateItem: (id: string, updates: Partial<ParsedQuestion>) => void;
  onRemoveItem: (id: string) => void;
  onAddManualItem: () => void;
  onAddExogenousItem: () => void;
  onAddQuickDimension: () => void;
  onUpdateScale: (scale: ScaleDraft) => void;
};

export function ItemsPanel({
  variable,
  catalogScales,
  defaultScale,
  selectedIds,
  onToggleSelect,
  onToggleAll,
  onClearSelection,
  onAddItems,
  onUpdateItem,
  onRemoveItem,
  onAddManualItem,
  onAddExogenousItem,
  onUpdateScale,
}: Props) {
  const [showScaleEditor, setShowScaleEditor] = useState(false);

  return (
    <div className="flex-1 min-h-0 flex flex-col gap-3">
      {/* Escala de respuesta (fusionada aquí: los ítems la heredan) */}
      <div
        className={`rounded-xl border bg-white shrink-0 transition-colors ${
          showScaleEditor ? "border-amber/50 shadow-sm" : "border-colmena-border"
        }`}
      >
        <button
          type="button"
          onClick={() => setShowScaleEditor((s) => !s)}
          className="group w-full flex items-center gap-2 px-3 py-2 text-left"
        >
          <SlidersHorizontal className="w-4 h-4 text-amber shrink-0" />
          <span className="text-[12px] font-bold text-dark">Escala de respuesta</span>
          <span className="text-[11px] text-muted truncate">· {variable.scale.name}</span>
          <div className="hidden md:flex items-center gap-1 ml-1 overflow-hidden">
            {variable.scale.options.slice(0, 6).map((o) => (
              <span key={o.id} className="shrink-0 rounded-full bg-colmena-bg px-1.5 py-0.5 text-[9px] text-muted">
                {o.value} {o.label}
              </span>
            ))}
          </div>
          <span
            className={`ml-auto inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold shrink-0 transition-colors ${
              showScaleEditor
                ? "bg-amber/15 text-amber"
                : "bg-colmena-bg text-muted group-hover:bg-amber/10 group-hover:text-amber"
            }`}
          >
            <Pencil className="w-3.5 h-3.5" />
            {showScaleEditor ? "Listo" : "Editar"}
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showScaleEditor ? "rotate-180" : ""}`} />
          </span>
        </button>
        {showScaleEditor && (
          <div className="border-t border-colmena-border max-h-[55vh] overflow-y-auto">
            <ScaleBuilder
              embedded
              scale={variable.scale}
              presets={catalogScales}
              onChange={onUpdateScale}
              previewQuestion={variable.items[0]?.text}
            />
          </div>
        )}
      </div>

      {/* Importar desde Excel: sección propia, separada de las acciones rápidas */}
      <div className="rounded-xl border border-colmena-border bg-white p-3 shrink-0">
        <span className="text-[11px] font-bold text-dark block mb-2">Importar ítems desde Excel</span>
        <BulkQuestionImporter onDataParsed={onAddItems} />
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <button type="button" onClick={onAddManualItem} className="colmena-button-sm-primary">
          + Agregar ítem
        </button>
        <button
          type="button"
          onClick={onAddExogenousItem}
          className="rounded-lg border border-colmena-border bg-white px-2.5 py-1.5 text-[12px] font-semibold text-dark hover:border-amber hover:text-amber transition-colors"
          title="Dato de perfil del participante (Sexo, Edad…) — se guarda como variable comparable, no se puntúa"
        >
          + Variable exógena
        </button>
      </div>

      <BulkQuestionTable
        questions={variable.items}
        selectedIds={selectedIds}
        dimensions={variable.dimensions}
        scales={catalogScales}
        defaultScale={defaultScale}
        onToggleSelect={onToggleSelect}
        onToggleAll={onToggleAll}
        onUpdate={onUpdateItem}
        onRemove={onRemoveItem}
        onClearSelection={onClearSelection}
      />
    </div>
  );
}
