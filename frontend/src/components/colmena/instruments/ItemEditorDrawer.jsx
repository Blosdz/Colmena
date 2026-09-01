import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import FormField from '../../ui/FormField.jsx';
import { Button } from '../../ui/Button.jsx';
import { Modal } from '../../ui/Modal.jsx';

const LIKERT_PRESETS = [
  {
    value: 'AGREEMENT_3',
    label: 'Acuerdo · 3 puntos',
    labels: ['En desacuerdo', 'Neutral', 'De acuerdo'],
  },
  {
    value: 'AGREEMENT_5',
    label: 'Acuerdo · 5 puntos',
    labels: [
      'Totalmente en desacuerdo',
      'En desacuerdo',
      'Ni de acuerdo ni en desacuerdo',
      'De acuerdo',
      'Totalmente de acuerdo',
    ],
  },
  {
    value: 'AGREEMENT_7',
    label: 'Acuerdo · 7 puntos',
    labels: [
      'Totalmente en desacuerdo',
      'Muy en desacuerdo',
      'En desacuerdo',
      'Ni de acuerdo ni en desacuerdo',
      'De acuerdo',
      'Muy de acuerdo',
      'Totalmente de acuerdo',
    ],
  },
  {
    value: 'SATISFACTION_5',
    label: 'Satisfacción · 5 puntos',
    labels: ['Muy insatisfecho', 'Insatisfecho', 'Neutral', 'Satisfecho', 'Muy satisfecho'],
  },
  {
    value: 'FREQUENCY_5',
    label: 'Frecuencia · 5 puntos',
    labels: ['Nunca', 'Rara vez', 'A veces', 'Frecuentemente', 'Siempre'],
  },
  {
    value: 'IMPORTANCE_5',
    label: 'Importancia · 5 puntos',
    labels: ['Nada importante', 'Poco importante', 'Moderadamente importante', 'Importante', 'Muy importante'],
  },
  {
    value: 'SCORE_10',
    label: 'Valoración · 1 a 10',
    labels: ['Mínimo', '2', '3', '4', '5', '6', '7', '8', '9', 'Máximo'],
  },
];

const DEFAULT_PRESET = LIKERT_PRESETS.find((preset) => preset.value === 'AGREEMENT_5');
const QUICK_COUNTS = [3, 5, 7, 10];

const schema = z.object({
  code: z.string().optional(),
  questionText: z.string().min(1, 'Ingresa el texto de la pregunta'),
  shortLabel: z.string().optional(),
  weight: z.coerce.number().min(0, 'El peso no puede ser negativo').default(1),
  scoringDirection: z.enum(['DIRECT', 'REVERSE']),
  isRequiredDefault: z.boolean(),
});

function createOptions(labels) {
  return labels.map((label, index) => ({
    raw_code: String(index + 1),
    label,
    numeric_value: index + 1,
    sort_order: index,
    is_active: true,
  }));
}

function normalizeOptions(options) {
  return [...(options || [])]
    .sort((left, right) => (left.sort_order ?? 0) - (right.sort_order ?? 0))
    .map((option, index) => ({
      raw_code: option.raw_code || String(index + 1),
      label: option.label || '',
      numeric_value: Number(option.numeric_value ?? index + 1),
      sort_order: index,
      is_active: option.is_active !== false,
    }));
}

function resizeOptions(current, count) {
  return Array.from({ length: count }, (_, index) => {
    const existing = current[index];
    return {
      raw_code: String(index + 1),
      label: existing?.label || `Opción ${index + 1}`,
      numeric_value: existing?.numeric_value ?? index + 1,
      sort_order: index,
      is_active: true,
    };
  });
}

function validateScale(name, options) {
  if (!name.trim()) return 'Asigna un nombre a la escala.';
  if (options.length < 2 || options.length > 10) return 'La escala debe tener entre 2 y 10 puntos.';
  if (options.some((option) => !option.label.trim())) return 'Todas las opciones necesitan un texto.';
  if (options.some((option) => !Number.isFinite(Number(option.numeric_value)))) {
    return 'Todos los puntos necesitan un valor numérico.';
  }
  const values = options.map((option) => Number(option.numeric_value));
  if (new Set(values).size !== values.length) return 'Los valores de puntuación deben ser únicos.';
  return '';
}

function Section({ title, description, children }) {
  return (
    <div className="grid grid-cols-1 gap-4 border-b border-border py-4 first:pt-0 last:border-0 last:pb-0 lg:grid-cols-[190px_minmax(0,1fr)] lg:gap-7">
      <div>
        <p className="text-sm font-semibold text-dark">{title}</p>
        {description ? <p className="mt-1 text-xs leading-5 text-muted">{description}</p> : null}
      </div>
      <div className="flex min-w-0 flex-col gap-4">{children}</div>
    </div>
  );
}

function ScalePreview({ options }) {
  return (
    <div className="rounded-xl border border-amber/25 bg-amber/5 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-yellowDark">Vista previa para el encuestado</p>
        <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-muted shadow-sm">
          Escala ordinal · {options.length} puntos
        </span>
      </div>
      <div className={`mt-4 grid gap-2 ${options.length > 5 ? 'grid-cols-2 md:grid-cols-5' : 'grid-cols-1 sm:grid-cols-5'}`}>
        {options.map((option, index) => (
          <div key={`${index}-${option.raw_code}`} className="flex min-w-0 flex-col items-center rounded-xl border border-border bg-white px-2 py-3 text-center">
            <span className="flex h-7 min-w-7 items-center justify-center rounded-full border-2 border-amber/60 px-1 text-xs font-bold text-yellowDark">
              {Number.isFinite(Number(option.numeric_value)) ? option.numeric_value : '—'}
            </span>
            <span className="mt-2 break-words text-[11px] leading-4 text-dark">{option.label || 'Sin texto'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ItemEditorDrawer({ item, scales = [], onClose, onSubmit, isSubmitting, submitError }) {
  const isEditing = Boolean(item);
  const initialScale = scales.find((scale) => Number(scale.id) === Number(item?.option_set_id));
  const [scaleChoice, setScaleChoice] = useState(initialScale ? String(initialScale.id) : 'custom');
  const [scaleAction, setScaleAction] = useState(initialScale ? 'USE' : 'CREATE');
  const [preset, setPreset] = useState(initialScale?.metadata?.preset || DEFAULT_PRESET.value);
  const [scaleName, setScaleName] = useState(initialScale?.name || 'Likert de acuerdo · 5 puntos');
  const [options, setOptions] = useState(
    initialScale ? normalizeOptions(initialScale.options) : createOptions(DEFAULT_PRESET.labels),
  );
  const [scaleError, setScaleError] = useState('');

  const selectedScale = useMemo(
    () => scales.find((scale) => String(scale.id) === scaleChoice),
    [scaleChoice, scales],
  );
  const previewOptions = scaleAction === 'USE' && selectedScale
    ? normalizeOptions(selectedScale.options)
    : options;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      code: item?.code || '',
      questionText: item?.question_text || '',
      shortLabel: item?.short_label || '',
      weight: item?.weight ?? 1,
      scoringDirection: item?.scoring_direction || 'DIRECT',
      isRequiredDefault: item?.is_required_default ?? true,
    },
  });

  const applyPreset = (presetId) => {
    const selectedPreset = LIKERT_PRESETS.find((entry) => entry.value === presetId);
    if (!selectedPreset) return;
    setPreset(presetId);
    setOptions(createOptions(selectedPreset.labels));
    setScaleName(selectedPreset.label.replace(' · ', ' — '));
    setScaleError('');
  };

  const changePointCount = (value) => {
    const count = Math.max(2, Math.min(10, Number(value) || 2));
    setPreset('CUSTOM');
    setOptions((current) => resizeOptions(current, count));
    setScaleError('');
  };

  const selectScale = (value) => {
    setScaleChoice(value);
    setScaleError('');
    if (value === 'custom') {
      setScaleAction('CREATE');
      applyPreset(DEFAULT_PRESET.value);
      return;
    }
    setScaleAction('USE');
  };

  const editSelectedScale = () => {
    if (!selectedScale) return;
    setScaleAction('UPDATE');
    setPreset(selectedScale.metadata?.preset || 'CUSTOM');
    setScaleName(selectedScale.name);
    setOptions(normalizeOptions(selectedScale.options));
  };

  const copySelectedScale = () => {
    if (!selectedScale) return;
    setScaleChoice('custom');
    setScaleAction('CREATE');
    setPreset('CUSTOM');
    setScaleName(`${selectedScale.name} — copia`);
    setOptions(normalizeOptions(selectedScale.options));
  };

  const updateOption = (index, field, value) => {
    setPreset('CUSTOM');
    setOptions((current) => current.map((option, optionIndex) => (
      optionIndex === index
        ? { ...option, [field]: field === 'numeric_value' ? Number(value) : value }
        : option
    )));
    setScaleError('');
  };

  const submit = (values) => {
    const effectiveOptions = scaleAction === 'USE' ? previewOptions : options;
    const validationMessage = validateScale(
      scaleAction === 'USE' ? selectedScale?.name || '' : scaleName,
      effectiveOptions,
    );
    if (validationMessage) {
      setScaleError(validationMessage);
      return;
    }

    const optionSet = scaleAction === 'USE' ? undefined : {
      name: scaleName.trim(),
      description: `Escala Likert editable de ${options.length} puntos, configurada desde el editor de ítems.`,
      metadata: {
        kind: 'LIKERT_USER',
        editable: true,
        points: options.length,
        preset,
        measurement_level: 'ORDINAL',
        created_from: 'ITEM_EDITOR',
      },
      options: options.map((option, index) => ({
        raw_code: String(index + 1),
        label: option.label.trim(),
        numeric_value: Number(option.numeric_value),
        sort_order: index,
        is_active: true,
      })),
    };

    onSubmit({
      code: values.code || null,
      question_text: values.questionText,
      short_label: values.shortLabel || null,
      question_type: 'LIKERT',
      is_scored: true,
      option_set_id: scaleChoice !== 'custom' ? Number(scaleChoice) : null,
      option_set: scaleAction === 'CREATE' && !isEditing ? optionSet : undefined,
      scale_config: optionSet,
      scale_action: scaleAction,
      is_required_default: values.isRequiredDefault,
      metadata: {
        measurement_scale: 'LIKERT',
        measurement_level: 'ORDINAL',
        likert_points: effectiveOptions.length,
      },
      weight: values.weight,
      scoring_direction: values.scoringDirection,
    });
  };

  const formId = 'item-editor-form';

  return (
    <Modal
      title={isEditing ? 'Editar pregunta Likert' : 'Agregar pregunta Likert'}
      subtitle="Configura el enunciado, la puntuación y exactamente cómo verá la escala el encuestado."
      onClose={onClose}
      size="xl"
      footer={
        <>
          <Button type="button" variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button type="submit" form={formId} variant="primary" loading={isSubmitting}>Guardar pregunta</Button>
        </>
      }
    >
      <form id={formId} onSubmit={handleSubmit(submit)} noValidate>
        <Section title="Pregunta" description="Las preguntas de variables y dimensiones son puntuables con Likert. Los datos de perfil se agregan en Datos exógenos.">
          <label className="flex flex-col gap-2">
            <span className="colmena-label">Texto de la pregunta</span>
            <textarea
              rows={3}
              className={`colmena-input px-4 py-3 text-sm text-dark ${errors.questionText ? 'has-error' : ''}`}
              placeholder="Ej.: Estoy satisfecho con el servicio recibido."
              {...register('questionText')}
            />
            {errors.questionText ? <span className="text-xs font-medium text-danger">{errors.questionText.message}</span> : null}
          </label>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Código (opcional)" placeholder="SAT_01" {...register('code')} />
            <FormField label="Etiqueta corta (opcional)" placeholder="Satisfacción general" {...register('shortLabel')} />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-border bg-surfaceSoft p-3">
              <p className="text-[11px] uppercase tracking-wide text-muted">Tipo</p>
              <p className="mt-1 text-sm font-semibold text-dark">Escala Likert</p>
            </div>
            <div className="rounded-xl border border-border bg-surfaceSoft p-3">
              <p className="text-[11px] uppercase tracking-wide text-muted">Medición</p>
              <p className="mt-1 text-sm font-semibold text-dark">Ordinal</p>
            </div>
            <div className="rounded-xl border border-border bg-surfaceSoft p-3">
              <p className="text-[11px] uppercase tracking-wide text-muted">Rango</p>
              <p className="mt-1 text-sm font-semibold text-dark">{previewOptions.length} puntos</p>
            </div>
          </div>
        </Section>

        <Section title="Escala de medición" description="Usa una escala guardada o crea una configuración propia de 2 a 10 puntos.">
          <label className="flex flex-col gap-2">
            <span className="colmena-label">Configuración</span>
            <select className="colmena-input h-10 px-4 text-sm text-dark" value={scaleChoice} onChange={(event) => selectScale(event.target.value)}>
              <option value="custom">Nueva escala editable para esta pregunta</option>
              {scales.map((scale) => (
                <option key={scale.id} value={scale.id}>{scale.name} ({scale.options.length} puntos)</option>
              ))}
            </select>
          </label>

          {selectedScale && scaleAction === 'USE' ? (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-surfaceSoft p-4">
              <div>
                <p className="text-sm font-semibold text-dark">{selectedScale.name}</p>
                <p className="mt-1 text-xs text-muted">Esta configuración ya está guardada y puede compartirse entre preguntas.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button type="button" size="sm" variant="secondary" onClick={editSelectedScale}>Editar esta escala</Button>
                <Button type="button" size="sm" variant="secondary" onClick={copySelectedScale}>Personalizar una copia</Button>
              </div>
            </div>
          ) : null}

          {scaleAction !== 'USE' ? (
            <div className="flex flex-col gap-4 rounded-xl border border-border p-4">
              {scaleAction === 'UPDATE' ? (
                <p className="rounded-lg bg-amber/10 px-3 py-2 text-xs text-yellowDark">
                  Estás editando una escala reutilizable. El cambio se reflejará en todas las preguntas que la utilizan.
                </p>
              ) : null}
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="flex flex-col gap-2">
                  <span className="colmena-label">Variación predefinida</span>
                  <select className="colmena-input h-10 px-4 text-sm text-dark" value={preset} onChange={(event) => applyPreset(event.target.value)}>
                    {preset === 'CUSTOM' ? <option value="CUSTOM">Personalizada</option> : null}
                    {LIKERT_PRESETS.map((entry) => <option key={entry.value} value={entry.value}>{entry.label}</option>)}
                  </select>
                </label>
                <label className="flex flex-col gap-2">
                  <span className="colmena-label">Nombre para reutilizar</span>
                  <input className="colmena-input h-10 px-4 text-sm text-dark" value={scaleName} onChange={(event) => setScaleName(event.target.value)} />
                </label>
              </div>

              <div>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="colmena-label">Cantidad de puntos</span>
                  <div className="flex flex-wrap gap-2">
                    {QUICK_COUNTS.map((count) => (
                      <button
                        key={count}
                        type="button"
                        onClick={() => changePointCount(count)}
                        className={`h-8 min-w-10 rounded-lg border px-2 text-xs font-semibold ${options.length === count ? 'border-amber bg-amber/10 text-yellowDark' : 'border-border bg-white text-muted'}`}
                      >
                        {count}
                      </button>
                    ))}
                    <input
                      type="number"
                      min="2"
                      max="10"
                      aria-label="Cantidad personalizada de puntos"
                      className="colmena-input h-8 w-20 px-2 text-center text-xs"
                      value={options.length}
                      onChange={(event) => changePointCount(event.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="overflow-hidden rounded-xl border border-border">
                <div className="grid grid-cols-[52px_76px_minmax(0,1fr)] gap-2 bg-surfaceSoft px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-muted">
                  <span>Punto</span><span>Valor</span><span>Texto editable</span>
                </div>
                <div className="divide-y divide-border">
                  {options.map((option, index) => (
                    <div key={index} className="grid grid-cols-[52px_76px_minmax(0,1fr)] items-center gap-2 px-3 py-2">
                      <span className="text-center text-xs font-semibold text-muted">{index + 1}</span>
                      <input
                        type="number"
                        step="any"
                        aria-label={`Valor de la opción ${index + 1}`}
                        className="colmena-input h-9 px-2 text-center text-sm"
                        value={option.numeric_value}
                        onChange={(event) => updateOption(index, 'numeric_value', event.target.value)}
                      />
                      <input
                        aria-label={`Texto de la opción ${index + 1}`}
                        className="colmena-input h-9 min-w-0 px-3 text-sm"
                        value={option.label}
                        onChange={(event) => updateOption(index, 'label', event.target.value)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}

          <ScalePreview options={previewOptions} />
          {scaleError ? <p className="text-sm font-medium text-danger">{scaleError}</p> : null}
          {submitError ? <p className="text-sm font-medium text-danger">{submitError.message || 'No se pudo guardar la pregunta.'}</p> : null}
        </Section>

        <Section title="Puntuación" description="Define el peso y si una respuesta alta suma o invierte el puntaje dentro de la dimensión.">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FormField label="Peso" type="number" step="0.1" min="0" error={errors.weight?.message} {...register('weight')} />
            <label className="flex flex-col gap-2">
              <span className="colmena-label">Dirección del puntaje</span>
              <select className="colmena-input h-10 px-4 text-sm text-dark" {...register('scoringDirection')}>
                <option value="DIRECT">Directa: mayor respuesta, mayor puntaje</option>
                <option value="REVERSE">Inversa: mayor respuesta, menor puntaje</option>
              </select>
            </label>
          </div>
          <label className="flex items-center gap-3 text-sm text-dark">
            <input type="checkbox" className="h-4 w-4" {...register('isRequiredDefault')} />
            Pregunta obligatoria por defecto
          </label>
        </Section>
      </form>
    </Modal>
  );
}
