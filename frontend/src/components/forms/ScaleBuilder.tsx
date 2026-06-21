
import { Plus, Trash2 } from "lucide-react";
import type { ScaleDraft } from "../../utils/projectDraftStore";

type Props = {
  scale: ScaleDraft;
  onChange: (scale: ScaleDraft) => void;
};

export function ScaleBuilder({ scale, onChange }: Props) {
  const updateName = (name: string) => onChange({ ...scale, name });

  const addOption = () => {
    onChange({
      ...scale,
      options: [...scale.options, { id: crypto.randomUUID(), value: scale.options.length + 1, label: "" }],
    });
  };

  const updateOption = (id: string, updates: Partial<{ value: number; label: string }>) => {
    onChange({
      ...scale,
      options: scale.options.map(o => o.id === id ? { ...o, ...updates } : o),
    });
  };

  const removeOption = (id: string) => {
    onChange({ ...scale, options: scale.options.filter(o => o.id !== id) });
  };

  return (
    <div className="space-y-3">
      <div>
        <label className="colmena-label">Nombre de la escala</label>
        <input
          className="colmena-input w-full max-w-xs"
          value={scale.name}
          onChange={(e) => updateName(e.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <label className="colmena-label">Opciones de respuesta</label>

        <div className="rounded-xl border border-colmena-border bg-white overflow-hidden">
          <div className="grid grid-cols-[56px_1fr_32px] gap-2 px-3 py-2 bg-colmena-bg border-b border-colmena-border">
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-muted text-center">Valor</span>
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-muted">Etiqueta</span>
            <span />
          </div>
          <div className="divide-y divide-colmena-border">
            {scale.options.map((opt) => (
              <div key={opt.id} className="grid grid-cols-[56px_1fr_32px] gap-2 px-3 py-1.5 items-center group hover:bg-colmena-bg/50 transition-colors">
                <input
                  type="number"
                  className="bg-transparent text-[12px] font-bold text-dark outline-none text-center w-full"
                  value={opt.value}
                  onChange={(e) => updateOption(opt.id, { value: Number(e.target.value) })}
                />
                <input
                  className="bg-transparent text-[12px] text-dark outline-none w-full"
                  placeholder="Etiqueta..."
                  value={opt.label}
                  onChange={(e) => updateOption(opt.id, { label: e.target.value })}
                />
                <button
                  className="p-1 opacity-0 group-hover:opacity-100 transition-opacity text-muted hover:text-danger"
                  onClick={() => removeOption(opt.id)}
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
          <div className="px-3 py-2 bg-colmena-bg border-t border-colmena-border">
            <button
              className="flex items-center gap-1.5 text-[11px] font-semibold text-amber hover:text-amber/80"
              onClick={addOption}
            >
              <Plus className="w-3 h-3" /> Agregar opción
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
