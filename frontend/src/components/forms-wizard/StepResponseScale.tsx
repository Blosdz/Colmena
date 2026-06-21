import { Plus, Trash2 } from "lucide-react";

import type { WizardFormContext, WizardScaleOptionDraft } from "./FormWizard";
import { WizardStepHeader } from "./WizardStepHeader";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { SoftPanel } from "../ui/SoftPanel";

function createScaleOption(sortOrder: number): WizardScaleOptionDraft {
  return {
    id: `scale-${crypto.randomUUID()}`,
    label: "",
    value: String(sortOrder + 1),
    score: sortOrder + 1,
    sortOrder,
  };
}

export function StepResponseScale({
  value,
  onChange,
}: {
  value: WizardFormContext & { responseScale: WizardScaleOptionDraft[] };
  onChange: (next: WizardFormContext & { responseScale: WizardScaleOptionDraft[] }) => void;
}) {
  const updateOption = (optionId: string, patch: Partial<WizardScaleOptionDraft>) => {
    onChange({
      ...value,
      responseScale: value.responseScale.map((item) => (item.id === optionId ? { ...item, ...patch } : item)),
    });
  };

  const removeOption = (optionId: string) => {
    const nextOptions = value.responseScale.filter((item) => item.id !== optionId);
    onChange({
      ...value,
      responseScale: nextOptions.length > 0 ? nextOptions : [createScaleOption(0), createScaleOption(1)],
    });
  };

  return (
    <div className="space-y-6">
      <WizardStepHeader
        step="Paso 6"
        title="Opciones de respuesta"
        description="Define la escala que se aplicara a todos los items del instrumento. Luego podras modificarla en futuras iteraciones si lo necesitas."
      />

      <SoftPanel className="space-y-4">
        {value.responseScale.map((option, index) => (
          <div className="grid gap-3 rounded-2xl border border-border bg-white p-3 xl:grid-cols-[1.2fr_140px_140px_90px]" key={option.id}>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Etiqueta {index + 1}</span>
              <Input
                placeholder="Nunca"
                value={option.label}
                onChange={(event) => updateOption(option.id, { label: event.target.value })}
              />
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Valor</span>
              <Input value={option.value} onChange={(event) => updateOption(option.id, { value: event.target.value })} />
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Puntaje</span>
              <Input
                type="number"
                value={option.score}
                onChange={(event) => updateOption(option.id, { score: Number(event.target.value) || 0 })}
              />
            </label>
            <div className="flex items-end">
              <Button className="w-full" onClick={() => removeOption(option.id)} size="sm" variant="ghost">
                <Trash2 className="mr-2 h-4 w-4" />
                Quitar
              </Button>
            </div>
          </div>
        ))}
      </SoftPanel>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={() =>
            onChange({
              ...value,
              responseScale: [...value.responseScale, createScaleOption(value.responseScale.length)],
            })
          }
          variant="secondary"
        >
          <Plus className="mr-2 h-4 w-4" />
          Agregar opcion
        </Button>
        <p className="text-sm text-muted">Esta escala se replicara sobre todos los items Likert creados en el wizard.</p>
      </div>
    </div>
  );
}
