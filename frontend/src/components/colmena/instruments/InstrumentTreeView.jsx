import { useState } from 'react';
import { ChevronDown, ChevronRight, FileQuestion, Layers3, Plus } from 'lucide-react';

import { Button } from '../../ui/Button.jsx';
import { displayLabel } from '../../../utils/labels.js';

function QuestionRow({ item, construct, onEditItem, readOnly }) {
  if (readOnly) {
    return (
      <div className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-muted">
        <FileQuestion size={14} className="shrink-0 text-muted/60" />
        <span className="min-w-0 flex-1 truncate">{item.question_text}</span>
        {item.code ? <span className="text-xs text-muted/70">({item.code})</span> : null}
      </div>
    );
  }
  return (
    <button type="button" onClick={() => onEditItem(item, construct)}
      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-muted hover:bg-[#F5F6F8]">
      <FileQuestion size={14} className="shrink-0 text-muted/60" />
      <span className="min-w-0 flex-1 truncate">{item.question_text}</span>
      {item.code ? <span className="text-xs text-muted/70">({item.code})</span> : null}
    </button>
  );
}

function DimensionNode({ construct, depth, onAddSubdimension, onAddItem, onEditItem, readOnly }) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = construct.subdimensions.length > 0 || construct.items.length > 0;
  const isDimension = construct.construct_type === 'DIMENSION';

  return (
    <div className={depth > 0 ? 'ml-6 border-l border-border pl-4' : ''}>
      <div className="flex items-center justify-between gap-2 py-2">
        <button type="button" onClick={() => setExpanded((value) => !value)}
          className="flex min-w-0 items-center gap-2 text-left text-sm font-semibold text-dark">
          {hasChildren ? (expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />) : <span className="w-4" />}
          <Layers3 size={15} className="shrink-0 text-amber" />
          <span className="truncate">{construct.name}</span>
          <span className="colmena-badge bg-amber/10 text-amber">
            {isDimension ? 'DIMENSIÓN' : 'SUBDIMENSIÓN'}
          </span>
        </button>
        {readOnly ? null : (
          <div className="flex shrink-0 gap-2">
            {isDimension ? (
              <Button variant="secondary" size="sm" onClick={() => onAddSubdimension(construct)}>
                <Plus size={13} /> Subdimensión
              </Button>
            ) : null}
            <Button variant="secondary" size="sm" onClick={() => onAddItem(construct)}>
              <Plus size={13} /> Pregunta
            </Button>
          </div>
        )}
      </div>
      {expanded ? (
        <div className="space-y-1 pb-2 pl-6">
          {construct.items.map((item) => (
            <QuestionRow key={item.id} item={item} construct={construct} onEditItem={onEditItem} readOnly={readOnly} />
          ))}
          {construct.subdimensions.map((child) => (
            <DimensionNode key={child.id} construct={child} depth={depth + 1}
              onAddSubdimension={onAddSubdimension} onAddItem={onAddItem} onEditItem={onEditItem} readOnly={readOnly} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default function InstrumentTreeView({
  tree, selectedVariableId, onSelectVariable, onAddVariable, onAddDimension,
  onAddSubdimension, onAddItem, onEditItem, readOnly = false,
}) {
  const variables = tree.variables || [];
  const selected = variables.find((variable) => variable.id === selectedVariableId) || null;

  return (
    <div>
      <div className="flex flex-col gap-3 border-b border-border px-4 py-3 sm:flex-row sm:items-end sm:justify-between">
        <label className="flex min-w-0 flex-1 flex-col gap-1.5 sm:max-w-md">
          <span className="colmena-label">Variable</span>
          <select className="colmena-input w-full px-3 text-sm font-medium" value={selectedVariableId || ''}
            onChange={(event) => onSelectVariable(Number(event.target.value))}>
            {!variables.length ? <option value="">Sin variables</option> : null}
            {variables.map((variable) => (
              <option key={variable.id} value={variable.id}>{variable.name}</option>
            ))}
          </select>
        </label>
        {readOnly ? null : (
          <Button variant="secondary" size="md" onClick={onAddVariable}>
            <Plus size={14} /> Nueva variable
          </Button>
        )}
      </div>

      {!selected ? (
        <div className="flex min-h-56 flex-col items-center justify-center gap-3 px-4 py-10 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber/10 text-amber"><Layers3 size={19} /></div>
          <div><p className="text-sm font-semibold text-dark">Crea la primera variable</p>
            <p className="mt-1 text-xs text-muted">Después podrás agregar sus dimensiones y preguntas directas.</p></div>
          {readOnly ? null : (
            <Button variant="primary" size="sm" onClick={onAddVariable}><Plus size={13} /> Nueva variable</Button>
          )}
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surfaceSoft/60 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-dark">{selected.name}</p>
              <p className="mt-0.5 text-xs text-muted">{selected.code} · {displayLabel(selected.role)}</p>
            </div>
            {readOnly ? null : (
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => onAddDimension(selected)}>
                  <Plus size={13} /> Dimensión
                </Button>
                <Button variant="secondary" size="sm" onClick={() => onAddItem(selected)}>
                  <Plus size={13} /> Pregunta directa
                </Button>
              </div>
            )}
          </div>
          <div className="px-4 py-3">
            {selected.direct_items.length ? (
              <section className="mb-3 rounded-xl border border-border bg-white p-2">
                <p className="px-3 py-1 text-[11px] font-bold uppercase tracking-[0.06em] text-muted">Preguntas directas</p>
                {selected.direct_items.map((item) => (
                  <QuestionRow key={item.id} item={item} construct={selected} onEditItem={onEditItem} readOnly={readOnly} />
                ))}
              </section>
            ) : null}
            {selected.dimensions.length ? selected.dimensions.map((dimension) => (
              <DimensionNode key={dimension.id} construct={dimension} depth={0}
                onAddSubdimension={onAddSubdimension} onAddItem={onAddItem} onEditItem={onEditItem} readOnly={readOnly} />
            )) : !selected.direct_items.length ? (
              <p className="py-8 text-center text-sm text-muted">Agrega una dimensión o una pregunta directa.</p>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
