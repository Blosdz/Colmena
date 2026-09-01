import { useEffect, useId, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ChevronRight, GitBranch, Info, Plus } from 'lucide-react';

import { Button } from '../../ui/Button.jsx';
import FormField from '../../ui/FormField.jsx';
import { Modal } from '../../ui/Modal.jsx';

const NODE_CONFIG = {
  variable: {
    title: 'Nueva variable',
    subtitle: 'Crea un grupo independiente de dimensiones y preguntas directas.',
    label: 'Nombre de la variable',
    placeholder: 'Ej. Satisfacción académica',
    submitLabel: 'Crear variable',
  },
  dimension: {
    title: 'Nueva dimensión',
    subtitle: 'Agrupa preguntas dentro de la variable seleccionada.',
    label: 'Nombre de la dimensión',
    placeholder: 'Ej. Calidad de enseñanza',
    submitLabel: 'Crear dimensión',
  },
  subdimension: {
    title: 'Nueva subdimensión',
    subtitle: 'Añade un nivel específico dentro de la dimensión.',
    label: 'Nombre de la subdimensión',
    placeholder: 'Ej. Claridad del docente',
    submitLabel: 'Crear subdimensión',
  },
};

const schema = z.object({
  name: z.string().trim().min(1, 'Ingresa un nombre').max(255, 'Usa 255 caracteres como máximo'),
  code: z.string().trim().min(1, 'Ingresa un código').max(80, 'Usa 80 caracteres como máximo')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Usa sólo letras, números, guiones y guiones bajos'),
  role: z.enum(['INDEPENDENT', 'DEPENDENT', 'CONTROL', 'OUTCOME']).optional(),
});

function slugify(value) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

function availableCode(name, type, parent, usedCodes) {
  const localCode = slugify(name) || type;
  const prefix = type === 'variable' ? '' : `${slugify(parent?.code || 'variable').slice(0, 50)}_`;
  const base = `${prefix}${localCode.slice(0, Math.max(1, 80 - prefix.length))}`;
  const used = new Set(usedCodes.map((code) => String(code).toLowerCase()));
  let code = base;
  let suffix = 2;
  while (used.has(code.toLowerCase())) {
    const tail = `_${suffix++}`;
    code = `${base.slice(0, 80 - tail.length)}${tail}`;
  }
  return code;
}

export default function StructureNodeModal({
  type, parent = null, usedCodes = [], onClose, onSubmit, isSubmitting = false, submitError = null,
}) {
  const formId = useId();
  const config = NODE_CONFIG[type];
  const [codeEdited, setCodeEdited] = useState(false);
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { name: '', code: availableCode('', type, parent, usedCodes), role: 'INDEPENDENT' },
  });
  const name = watch('name');

  useEffect(() => {
    if (!codeEdited) setValue('code', availableCode(name, type, parent, usedCodes), { shouldValidate: false });
  }, [codeEdited, name, parent, setValue, type, usedCodes]);

  if (!config) return null;
  const hierarchy = type === 'variable'
    ? [name?.trim() || 'Variable nueva', 'Dimensión o pregunta directa']
    : [parent?.name, name?.trim() || config.title, 'Pregunta'];

  return (
    <Modal
      title={config.title}
      subtitle={config.subtitle}
      icon={GitBranch}
      onClose={onClose}
      size="md"
      preventClose={isSubmitting}
      footer={
        <>
          <Button type="button" variant="secondary" size="lg" onClick={onClose} disabled={isSubmitting}>Cancelar</Button>
          <Button type="submit" form={formId} size="lg" loading={isSubmitting}
            className="bg-gradient-to-r from-amber to-honey px-6 text-white shadow-soft hover:opacity-95">
            <Plus size={16} /> {config.submitLabel}
          </Button>
        </>
      }
    >
      <form id={formId} className="space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
        {parent ? (
          <div className="flex items-center gap-2 rounded-xl border border-border bg-surfaceSoft px-3 py-2.5 text-xs">
            <span className="font-medium text-muted">Se agregará dentro de</span>
            <ChevronRight size={13} className="text-amber" />
            <span className="font-semibold text-dark">{parent.name}</span>
          </div>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.72fr)]">
          <FormField label={config.label} placeholder={config.placeholder} error={errors.name?.message}
            autoFocus autoComplete="off" {...register('name')} />
          <FormField label="Código" error={errors.code?.message} hint="Editable; se usa internamente."
            autoComplete="off" {...register('code', { onChange: () => setCodeEdited(true) })} />
        </div>

        {type === 'variable' ? (
          <label className="flex flex-col gap-2">
            <span className="colmena-label">Rol analítico</span>
            <select className="colmena-input px-3 text-sm" {...register('role')}>
              <option value="INDEPENDENT">Independiente</option>
              <option value="DEPENDENT">Dependiente</option>
              <option value="CONTROL">Control</option>
              <option value="OUTCOME">Resultado</option>
            </select>
          </label>
        ) : null}

        <div className="flex gap-2 rounded-xl border border-turquoise/20 bg-turquoiseSoft px-3 py-3 text-xs text-dark">
          <Info size={16} className="shrink-0 text-turquoiseDark" />
          <p>{hierarchy.filter(Boolean).join(' → ')}</p>
        </div>

        {submitError ? (
          <p role="alert" className="rounded-xl border border-danger/20 bg-danger/10 px-3 py-2.5 text-sm font-medium text-danger">
            {submitError.message || `No se pudo crear la ${type === 'variable' ? 'variable' : 'dimensión'}.`}
          </p>
        ) : null}
      </form>
    </Modal>
  );
}
