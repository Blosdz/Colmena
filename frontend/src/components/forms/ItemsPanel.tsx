import { useState } from "react";
import { ChevronDown, FileSpreadsheet, Plus, SlidersHorizontal } from "lucide-react";
import { LikertScaleEditor } from "./LikertScaleEditor";

import type { ScaleDraft, VariableDraft } from "../../utils/projectDraftStore";
import type { ParsedQuestion } from "../../utils/bulkQuestionParser";
import { BulkQuestionImporter } from "./BulkQuestionImporter";
import { BulkQuestionTable, type CatalogScale } from "./BulkQuestionTable";

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
  const [editingScale, setEditingScale] = useState(false);
  const [importing, setImporting] = useState(false);
  return (
    <div className="question-workspace">
      <div className="question-workspace-heading">
        <div><h2>Preguntas</h2><p>Define qué quieres preguntar y cómo se responde.</p></div>
        <div className="question-actions">
          <button type="button" className="question-button" onClick={() => setImporting(!importing)} aria-expanded={importing}><FileSpreadsheet size={16} /> Importar Excel</button>
          <button type="button" className="question-button" onClick={onAddExogenousItem}><Plus size={16} /> Variable exógena</button>
          <button type="button" className="question-button question-button-primary" onClick={onAddManualItem}><Plus size={16} /> Agregar pregunta</button>
        </div>
      </div>
      <section className="question-scale-card">
        <button type="button" className="question-scale-summary" onClick={() => setEditingScale(!editingScale)} aria-expanded={editingScale}>
          <span className="question-symbol"><SlidersHorizontal size={20} /></span>
          <span className="question-scale-copy"><strong>Escala Likert compartida</strong><span>{variable.scale.name || "Define tu escala"}{/\b\d+ puntos\b/i.test(variable.scale.name) ? "" : ` · ${variable.scale.options.length} puntos`}</span></span>
          <span className="question-edit-label">{editingScale ? "Cerrar" : "Editar escala"}</span><ChevronDown size={16} className={editingScale ? "question-chevron-open" : ""} />
        </button>
        {!editingScale && variable.scale.options.length > 0 && <div className="question-scale-options">{variable.scale.options.map(o => <span key={o.id}><b>{o.value}</b>{o.label}</span>)}</div>}
        {editingScale && <LikertScaleEditor key={variable.id} scale={variable.scale} catalog={catalogScales} onCancel={() => setEditingScale(false)} onSave={scale => { onUpdateScale(scale); setEditingScale(false); }} />}
      </section>
      {importing && <div className="question-import"><p>Copia las filas de Excel y pégalas aquí. Puedes incluir código y pregunta en dos columnas.</p><BulkQuestionImporter onDataParsed={onAddItems} /></div>}
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
