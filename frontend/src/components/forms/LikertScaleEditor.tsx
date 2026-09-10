import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { ScaleDraft } from "../../utils/projectDraftStore";
import type { CatalogScale } from "./BulkQuestionTable";

export function LikertScaleEditor({ scale, catalog, onSave, onCancel }: {
  scale: ScaleDraft;
  catalog: CatalogScale[];
  onSave: (scale: ScaleDraft) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<ScaleDraft>(() => ({ ...scale, options: scale.options.map(o => ({ ...o })) }));
  const valid = draft.name.trim() && draft.options.length >= 2 && draft.options.every(o => o.label.trim() && Number.isFinite(o.value)) && new Set(draft.options.map(o => o.value)).size === draft.options.length;
  const change = (patch: Partial<ScaleDraft>) => setDraft(current => ({ ...current, ...patch, catalogScaleId: null }));
  return <div className="question-scale-editor">
    <p className="question-helper">Se aplica a las preguntas que usan la escala compartida. Puedes partir de una plantilla y ajustar sus etiquetas.</p>
    <div className="question-field-grid">
      <label>Plantilla<select value={draft.catalogScaleId ?? ""} onChange={e => {
        const preset = catalog.find(s => s.id === e.target.value);
        if (preset) setDraft({ name: preset.name, catalogScaleId: preset.id, options: preset.options.map(o => ({ ...o, id: crypto.randomUUID() })) });
        else change({});
      }}><option value="">Personalizada</option>{catalog.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
      <label>Nombre de la escala<input value={draft.name} onChange={e => change({ name: e.target.value })} placeholder="Ej. Acuerdo · 5 puntos" /></label>
    </div>
    <div className="question-option-head"><span>Valor</span><span>Etiqueta de respuesta</span></div>
    {draft.options.map((o, i) => <div className="question-option-row" key={o.id}>
      <input type="number" aria-label={`Valor del punto ${i + 1}`} value={Number.isNaN(o.value) ? "" : o.value} onChange={e => change({ options: draft.options.map(x => x.id === o.id ? { ...x, value: e.target.valueAsNumber } : x) })} />
      <input aria-label={`Etiqueta del punto ${i + 1}`} value={o.label} placeholder={`Respuesta ${i + 1}`} onChange={e => change({ options: draft.options.map(x => x.id === o.id ? { ...x, label: e.target.value } : x) })} />
      <button type="button" className="question-icon-button" aria-label={`Eliminar punto ${i + 1}`} disabled={draft.options.length <= 2} onClick={() => change({ options: draft.options.filter(x => x.id !== o.id) })}><Trash2 size={16} /></button>
    </div>)}
    <button type="button" className="question-button" onClick={() => change({ options: [...draft.options, { id: crypto.randomUUID(), value: Math.max(0, ...draft.options.map(o => Number.isFinite(o.value) ? o.value : 0)) + 1, label: "" }] })}><Plus size={15} /> Agregar punto</button>
    {!valid && <p className="question-helper" role="status">Completa el nombre y al menos dos etiquetas con valores numéricos distintos.</p>}
    <div className="question-editor-footer"><button type="button" className="question-button" onClick={onCancel}>Cancelar</button><button type="button" disabled={!valid} className="question-button question-button-primary" onClick={() => onSave({ ...draft, name: draft.name.trim(), options: [...draft.options].sort((a, b) => a.value - b.value).map(o => ({ ...o, label: o.label.trim() })) })}>Guardar escala</button></div>
  </div>;
}
