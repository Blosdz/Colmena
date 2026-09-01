import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowDown, ArrowUp, LockKeyhole, Plus, Trash2 } from 'lucide-react';

import { createExogenousField, listExogenousFields } from '../../../api/variables.js';
import { getInstrumentTree } from '../../../api/instruments.js';
import { Button } from '../../ui/Button.jsx';
import { Card } from '../../ui/Card.jsx';
import { EmptyState } from '../../ui/EmptyState.jsx';
import { displayLabel } from '../../../utils/labels.js';

const LOCK_MESSAGES = {
  SYSTEM_INSTRUMENT_LOCKED: 'Este instrumento es de sistema y no admite campos exógenos nuevos en su estado actual.',
  STUDY_OPEN_STRUCTURAL_LOCK:
    'El estudio de este instrumento ya está abierto y recolectando respuestas, así que su estructura quedó congelada — incluidos los campos exógenos. Agrega los campos de segmentación antes de abrir el estudio, o clona una versión editable si necesitas seguir cambiándola.',
};

const MIN_OPTIONS = 2;

const initialForm = {
  code: '', name: '', questionText: '', dataType: 'CATEGORY', measurementLevel: 'NOMINAL', required: false,
  options: ['Femenino', 'Masculino', 'Prefiero no responder'],
};

function buildCategoryOptions(optionLabels, measurementLevel) {
  return optionLabels
    .map((label) => label.trim())
    .filter(Boolean)
    .map((label, index) => ({
      raw_code: String(index + 1),
      label,
      numeric_value: measurementLevel === 'ORDINAL' ? index + 1 : null,
      sort_order: index,
    }));
}

export default function ExogenousFieldsManager({ projectId, versionId }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(initialForm);
  const { data: fields = [] } = useQuery({
    queryKey: ['exogenousFields', projectId],
    queryFn: () => listExogenousFields(projectId),
    enabled: Boolean(projectId),
  });
  const { data: tree } = useQuery({
    queryKey: ['instrumentTree', versionId],
    queryFn: () => getInstrumentTree(versionId),
    enabled: Boolean(versionId),
  });
  const isLocked = tree ? !tree.editable : false;
  const categoryOptions = buildCategoryOptions(form.options, form.measurementLevel);
  const mutation = useMutation({
    mutationFn: () => createExogenousField(projectId, {
      instrument_version_id: versionId,
      code: form.code,
      name: form.name,
      question_text: form.questionText,
      data_type: form.dataType,
      measurement_level: form.measurementLevel,
      is_required: form.required,
      options: form.dataType === 'CATEGORY' ? categoryOptions : [],
    }),
    onSuccess: () => {
      setForm(initialForm);
      queryClient.invalidateQueries({ queryKey: ['exogenousFields', projectId] });
    },
  });

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  const updateOptionLabel = (index, value) => {
    setForm((current) => ({ ...current, options: current.options.map((label, i) => (i === index ? value : label)) }));
  };
  const addOption = () => {
    setForm((current) => ({ ...current, options: [...current.options, ''] }));
  };
  const removeOption = (index) => {
    setForm((current) => (
      current.options.length <= MIN_OPTIONS
        ? current
        : { ...current, options: current.options.filter((_, i) => i !== index) }
    ));
  };
  const moveOption = (index, direction) => {
    const target = index + direction;
    setForm((current) => {
      if (target < 0 || target >= current.options.length) return current;
      const next = [...current.options];
      [next[index], next[target]] = [next[target], next[index]];
      return { ...current, options: next };
    });
  };

  if (!versionId) return <EmptyState title="Primero inicializa la estructura." description="Los campos de perfil se agregan como una sección opcional del formulario." />;

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
      {isLocked ? (
        <div className="flex gap-3 rounded-2xl border border-amber/20 bg-yellowSoft p-4 xl:col-span-2">
          <LockKeyhole size={18} className="mt-0.5 shrink-0 text-yellowDark" />
          <div>
            <p className="text-sm font-semibold text-dark">La estructura de este instrumento está bloqueada.</p>
            <p className="mt-1 text-xs text-yellowDark">
              {LOCK_MESSAGES[tree?.lock_reason] || 'No se pueden agregar campos exógenos nuevos en el estado actual del instrumento.'}
            </p>
          </div>
        </div>
      ) : null}
      <Card padded={false}>
        <div className="border-b border-border px-4 py-4">
          <p className="text-sm font-semibold text-dark">Campos exógenos</p>
          <p className="text-xs text-muted">Sirven para perfilar y comparar grupos; nunca suman al puntaje de las variables.</p>
        </div>
        {fields.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-surfaceSoft text-xs uppercase text-muted"><tr><th className="px-4 py-3">Código</th><th className="px-4 py-3">Campo</th><th className="px-4 py-3">Tipo</th><th className="px-4 py-3">Nivel</th></tr></thead>
              <tbody>{fields.map(({ variable, question }) => <tr key={variable.id} className="border-t border-border"><td className="px-4 py-3 font-mono text-xs">{variable.code}</td><td className="px-4 py-3"><p className="font-medium text-dark">{variable.name}</p><p className="text-xs text-muted">{question.question_text}</p></td><td className="px-4 py-3">{displayLabel(variable.data_type)}</td><td className="px-4 py-3">{displayLabel(variable.measurement_level)}</td></tr>)}</tbody>
            </table>
          </div>
        ) : <div className="p-4"><EmptyState title="Sin campos de perfil" description="Edad, sexo, sede y otros datos son opcionales." /></div>}
      </Card>

      {isLocked ? null : (
      <Card>
        <div className="flex flex-col gap-4">
          <div><p className="text-sm font-semibold text-dark">Agregar campo</p><p className="mt-1 text-xs text-muted">Se crea la pregunta y su variable exógena en una sola transacción.</p></div>
          <input className="colmena-input h-10 px-4 text-sm" placeholder="Código: edad" value={form.code} onChange={(event) => update('code', event.target.value)} />
          <input className="colmena-input h-10 px-4 text-sm" placeholder="Nombre: Edad" value={form.name} onChange={(event) => update('name', event.target.value)} />
          <textarea rows={2} className="colmena-input px-4 py-3 text-sm" placeholder="Pregunta que verá el encuestado" value={form.questionText} onChange={(event) => update('questionText', event.target.value)} />
          <div className="grid grid-cols-2 gap-3">
            <select className="colmena-input h-10 px-3 text-sm" value={form.dataType} onChange={(event) => update('dataType', event.target.value)}>
              <option value="CATEGORY">Categoría</option><option value="INTEGER">Entero</option><option value="DECIMAL">Decimal</option><option value="TEXT">Texto</option><option value="BOOLEAN">Sí/No</option><option value="DATE">Fecha</option>
            </select>
            <select className="colmena-input h-10 px-3 text-sm" value={form.measurementLevel} onChange={(event) => update('measurementLevel', event.target.value)}>
              <option value="NOMINAL">Nominal</option><option value="ORDINAL">Ordinal</option><option value="SCALE">Escala</option><option value="BINARY">Binaria</option><option value="TEXT">Texto</option>
            </select>
          </div>
          {form.dataType === 'CATEGORY' ? (
            <div className="flex flex-col gap-2">
              <span className="colmena-label">Opciones de respuesta</span>
              <p className="text-xs text-muted">
                Escribe cada opción en su propio campo{form.measurementLevel === 'ORDINAL' ? '; el orden define el valor numérico (1, 2, 3…), usa las flechas para reordenar' : ''}.
              </p>
              <div className="flex flex-col gap-2">
                {form.options.map((label, index) => (
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
                      <Button type="button" variant="ghost" size="sm" className="!px-2" onClick={() => moveOption(index, -1)} disabled={index === 0} aria-label="Mover opción hacia arriba">
                        <ArrowUp size={14} />
                      </Button>
                      <Button type="button" variant="ghost" size="sm" className="!px-2" onClick={() => moveOption(index, 1)} disabled={index === form.options.length - 1} aria-label="Mover opción hacia abajo">
                        <ArrowDown size={14} />
                      </Button>
                      <Button type="button" variant="ghost" size="sm" className="!px-2 text-danger hover:bg-danger/10" onClick={() => removeOption(index)} disabled={form.options.length <= MIN_OPTIONS} aria-label="Eliminar opción">
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              <Button type="button" variant="secondary" size="sm" className="w-fit" onClick={addOption}>
                <Plus size={14} className="mr-1" /> Añadir opción
              </Button>
            </div>
          ) : null}
          <label className="flex items-center gap-2 text-sm text-dark"><input type="checkbox" checked={form.required} onChange={(event) => update('required', event.target.checked)} /> Obligatorio</label>
          {mutation.isError ? <p className="text-sm text-danger">{mutation.error?.message || 'No se pudo crear.'}</p> : null}
          <Button variant="primary" size="sm" onClick={() => mutation.mutate()} loading={mutation.isPending} disabled={!form.code || !form.name || !form.questionText || (form.dataType === 'CATEGORY' && categoryOptions.length < MIN_OPTIONS)}>Agregar campo</Button>
        </div>
      </Card>
      )}
    </div>
  );
}
