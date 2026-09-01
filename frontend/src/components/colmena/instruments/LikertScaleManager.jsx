import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowDown, ArrowUp, Plus, Save, Trash2 } from 'lucide-react';

import { createLikertScale, listLikertScales, updateLikertScale } from '../../../api/instruments.js';
import { Button } from '../../ui/Button.jsx';
import { Card } from '../../ui/Card.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';

const DEFAULT_OPTION_LABELS = [
  'Totalmente en desacuerdo',
  'En desacuerdo',
  'Ni de acuerdo ni en desacuerdo',
  'De acuerdo',
  'Totalmente de acuerdo',
];
const MIN_OPTIONS = 2;
const MAX_OPTIONS = 10;

function buildOptions(optionLabels) {
  return optionLabels
    .map((label) => label.trim())
    .filter(Boolean)
    .map((label, index) => ({
      raw_code: String(index + 1),
      label,
      numeric_value: index + 1,
      sort_order: index,
      is_active: true,
    }));
}

export default function LikertScaleManager({ versionId }) {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState('');
  const [name, setName] = useState('Likert de 5 puntos');
  const [optionLabels, setOptionLabels] = useState(DEFAULT_OPTION_LABELS);
  const [message, setMessage] = useState('');

  const { data: scales = [], isLoading } = useQuery({
    queryKey: ['likertScales', versionId],
    queryFn: () => listLikertScales(versionId),
    enabled: Boolean(versionId),
  });
  const selected = scales.find((scale) => String(scale.id) === String(selectedId));

  useEffect(() => {
    if (!selected) return;
    setName(selected.name);
    setOptionLabels(selected.options.map((option) => option.label));
  }, [selected]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['likertScales', versionId] });
  const saveMutation = useMutation({
    mutationFn: () => {
      const options = buildOptions(optionLabels);
      const payload = {
        name,
        metadata: {
          kind: 'LIKERT_USER',
          editable: true,
          points: options.length,
          preset: 'CUSTOM',
          measurement_level: 'ORDINAL',
          created_from: 'SCALE_MANAGER',
        },
        options,
      };
      return selected ? updateLikertScale(selected.id, payload) : createLikertScale(versionId, payload);
    },
    onSuccess: (scale) => {
      setSelectedId(String(scale.id));
      setMessage('Escala guardada. Ya puede reutilizarse en cualquier ítem puntuable.');
      invalidate();
    },
  });

  const newScale = () => {
    setSelectedId('');
    setName('Likert de 5 puntos');
    setOptionLabels(DEFAULT_OPTION_LABELS);
    setMessage('');
  };

  const updateOptionLabel = (index, value) => {
    setOptionLabels((prev) => prev.map((label, i) => (i === index ? value : label)));
  };

  const addOption = () => {
    setOptionLabels((prev) => (prev.length >= MAX_OPTIONS ? prev : [...prev, '']));
  };

  const removeOption = (index) => {
    setOptionLabels((prev) => (prev.length <= MIN_OPTIONS ? prev : prev.filter((_, i) => i !== index)));
  };

  const moveOption = (index, direction) => {
    const target = index + direction;
    setOptionLabels((prev) => {
      if (target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const previewOptions = buildOptions(optionLabels);

  if (!versionId) {
    return <EmptyState title="Primero inicializa la estructura." description="Las escalas se reutilizan en las preguntas del proyecto." />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[300px_minmax(0,1fr)]">
      <Card padded={false}>
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <p className="text-sm font-semibold text-dark">Escalas reutilizables</p>
            <p className="text-xs text-muted">{scales.length} configurada(s)</p>
          </div>
          <Button variant="secondary" size="sm" onClick={newScale}><Plus size={14} /></Button>
        </div>
        <div className="flex flex-col gap-2 p-3">
          {isLoading ? <p className="p-3 text-sm text-muted">Cargando…</p> : null}
          {scales.map((scale) => (
            <button
              key={scale.id}
              type="button"
              onClick={() => setSelectedId(String(scale.id))}
              className={`rounded-xl border px-4 py-3 text-left ${selected?.id === scale.id ? 'border-amber bg-amber/10' : 'border-border bg-white'}`}
            >
              <p className="text-sm font-semibold text-dark">{scale.name}</p>
              <p className="mt-1 text-xs text-muted">{scale.options.length} puntos · {scale.options.map((option) => option.numeric_value).join(', ')}</p>
            </button>
          ))}
        </div>
      </Card>

      <Card>
        <div className="flex flex-col gap-4">
          <div>
            <p className="text-sm font-semibold text-dark">{selected ? 'Editar escala' : 'Nueva escala Likert'}</p>
            <p className="mt-1 text-xs text-muted">El orden asigna valores 1…n. Puedes configurar de 2 a 10 puntos y reutilizarlos en varias preguntas.</p>
          </div>
          <label className="flex flex-col gap-2">
            <span className="colmena-label">Nombre</span>
            <input className="colmena-input h-10 px-4 text-sm" value={name} onChange={(event) => setName(event.target.value)} />
          </label>

          <div className="flex flex-col gap-2">
            <span className="colmena-label">Opciones de respuesta</span>
            <p className="text-xs text-muted">
              Escribe cada opción en su propio campo, de menor a mayor acuerdo. El orden define el valor numérico
              (1, 2, 3…) que se usará para puntuar; usa las flechas para reordenar.
            </p>
            <div className="flex flex-col gap-2">
              {optionLabels.map((label, index) => (
                <div key={index} className="flex items-center gap-2">
                  <span className="colmena-badge flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber/10 text-xs font-semibold text-yellowDark">
                    {index + 1}
                  </span>
                  <input
                    className="colmena-input h-10 flex-1 px-4 text-sm"
                    value={label}
                    placeholder={`Opción ${index + 1}`}
                    onChange={(event) => updateOptionLabel(index, event.target.value)}
                  />
                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="!px-2"
                      onClick={() => moveOption(index, -1)}
                      disabled={index === 0}
                      aria-label="Mover opción hacia arriba"
                    >
                      <ArrowUp size={14} />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="!px-2"
                      onClick={() => moveOption(index, 1)}
                      disabled={index === optionLabels.length - 1}
                      aria-label="Mover opción hacia abajo"
                    >
                      <ArrowDown size={14} />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="!px-2 text-danger hover:bg-danger/10"
                      onClick={() => removeOption(index)}
                      disabled={optionLabels.length <= MIN_OPTIONS}
                      aria-label="Eliminar opción"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="w-fit"
              onClick={addOption}
              disabled={optionLabels.length >= MAX_OPTIONS}
            >
              <Plus size={14} className="mr-1" /> Añadir opción
            </Button>
            {optionLabels.length >= MAX_OPTIONS ? (
              <p className="text-xs text-muted">Una escala Likert admite como máximo {MAX_OPTIONS} puntos.</p>
            ) : null}
          </div>

          <div className="rounded-xl bg-surfaceSoft p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Así la verá quien responda</p>
            {previewOptions.length ? (
              <div
                className="mt-3 grid gap-2"
                style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))' }}
              >
                {previewOptions.map((option) => (
                  <div
                    key={option.raw_code}
                    className="flex flex-col items-center gap-1.5 rounded-xl border border-border bg-white px-3 py-3 text-center"
                  >
                    <span className="h-2.5 w-2.5 rounded-full border-2 border-amber" aria-hidden="true" />
                    <span className="text-xs font-medium text-dark">{option.label}</span>
                    <span className="text-[10px] text-muted">Valor {option.numeric_value}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-xs text-muted">Añade al menos {MIN_OPTIONS} opciones para ver la vista previa.</p>
            )}
          </div>

          {message ? <p className="text-sm text-turquoise">{message}</p> : null}
          {saveMutation.isError ? <p className="text-sm text-danger">{saveMutation.error?.message || 'No se pudo guardar.'}</p> : null}
          <Button
            variant="primary"
            size="sm"
            className="w-44"
            onClick={() => saveMutation.mutate()}
            loading={saveMutation.isPending}
            disabled={!name.trim() || previewOptions.length < MIN_OPTIONS || previewOptions.length > MAX_OPTIONS}
          >
            <Save size={15} className="mr-1" /> Guardar escala
          </Button>
        </div>
      </Card>
    </div>
  );
}
