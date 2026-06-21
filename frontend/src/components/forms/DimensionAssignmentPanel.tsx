import { Plus, Trash2, GripVertical } from "lucide-react";
import { useState } from "react";
import type { DimensionDraft } from "../../utils/projectDraftStore";
import type { ParsedQuestion } from "../../utils/bulkQuestionParser";

type Props = {
  dimensions: DimensionDraft[];
  items: ParsedQuestion[];
  onAdd: (name: string) => void;
  onRemove: (id: string) => void;
  onUpdate: (id: string, updates: Partial<DimensionDraft>) => void;
};

export function DimensionAssignmentPanel({ dimensions, items, onAdd, onRemove, onUpdate }: Props) {
  const [newName, setNewName] = useState("");

  const handleAdd = () => {
    const name = newName.trim();
    if (!name) return;
    onAdd(name);
    setNewName("");
  };

  // Count items per dimension
  const itemsByDim = dimensions.map(dim => ({
    ...dim,
    count: items.filter(i => i.dimensionName === dim.name).length,
  }));

  const unassigned = items.filter(i => !dimensions.some(d => d.name === i.dimensionName)).length;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <input
          className="colmena-input flex-1"
          placeholder="Nombre de la nueva dimensión..."
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleAdd(); }}
        />
        <button className="colmena-button-sm-primary" onClick={handleAdd} disabled={!newName.trim()}>
          <Plus className="w-3.5 h-3.5 mr-1" />
          Agregar
        </button>
      </div>

      {dimensions.length === 0 && (
        <div className="rounded-lg border border-dashed border-colmena-border py-4 text-center text-[11px] text-muted">
          Aún no hay dimensiones. Agrega al menos una para organizar tus ítems.
        </div>
      )}

      {dimensions.length > 0 && (
        <div className="rounded-xl border border-colmena-border bg-white overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-[24px_1fr_1.5fr_64px_32px] gap-2 px-3 py-2 bg-colmena-bg border-b border-colmena-border">
            <span />
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-muted">Nombre</span>
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-muted">Descripción</span>
            <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-muted text-center">Ítems</span>
            <span />
          </div>
          {/* Rows */}
          <div className="divide-y divide-colmena-border">
            {itemsByDim.map((dim) => (
              <div key={dim.id} className="grid grid-cols-[24px_1fr_1.5fr_64px_32px] gap-2 px-3 py-1.5 items-center hover:bg-colmena-bg/50 transition-colors group">
                <GripVertical className="w-3 h-3 text-muted/30 cursor-grab" />
                <input
                  className="bg-transparent text-[12px] font-semibold text-dark outline-none w-full"
                  value={dim.name}
                  onChange={(e) => onUpdate(dim.id, { name: e.target.value })}
                />
                <input
                  className="bg-transparent text-[12px] text-muted outline-none w-full"
                  placeholder="Descripción opcional..."
                  value={dim.description}
                  onChange={(e) => onUpdate(dim.id, { description: e.target.value })}
                />
                <span className={`text-center text-[11px] font-bold ${dim.count > 0 ? "text-success" : "text-muted"}`}>
                  {dim.count}
                </span>
                <button
                  className="p-1 opacity-0 group-hover:opacity-100 transition-opacity text-muted hover:text-danger"
                  onClick={() => onRemove(dim.id)}
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
          {/* Footer */}
          <div className="flex items-center justify-between px-3 py-2 bg-colmena-bg border-t border-colmena-border">
            <span className="text-[10px] font-semibold text-muted">{dimensions.length} dimensión{dimensions.length !== 1 ? "es" : ""}</span>
            {unassigned > 0 && (
              <span className="text-[10px] font-bold text-warning">{unassigned} ítem{unassigned !== 1 ? "s" : ""} sin asignar</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
