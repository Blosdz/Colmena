import type { ChangeEvent } from "react";

import type { WizardFormContext } from "./FormWizard";
import { WizardStepHeader } from "./WizardStepHeader";
import { Input } from "../ui/Input";
import { Select, SelectOption } from "../ui/Select";
import { SoftPanel } from "../ui/SoftPanel";

function update<K extends keyof WizardFormContext>(
  state: WizardFormContext,
  onChange: (next: WizardFormContext) => void,
  key: K,
  value: WizardFormContext[K],
) {
  onChange({ ...state, [key]: value });
}

export function StepProjectContext({
  value,
  onChange,
}: {
  value: WizardFormContext;
  onChange: (next: WizardFormContext) => void;
}) {
  return (
    <div className="space-y-6">
      <WizardStepHeader
        step="Paso 1"
        title="Contexto del formulario"
        description="Define el encabezado del formulario, las instrucciones para responder y las condiciones basicas de recoleccion."
      />

      <div className="grid gap-4 xl:grid-cols-2">
        <SoftPanel className="space-y-4">
          <label className="space-y-2 text-sm text-dark">
            <span className="font-medium">Titulo del formulario</span>
            <Input value={value.title} onChange={(event) => update(value, onChange, "title", event.target.value)} />
          </label>
          <label className="space-y-2 text-sm text-dark">
            <span className="font-medium">Descripcion breve</span>
            <textarea
              className="min-h-[110px] w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20"
              value={value.description}
              onChange={(event) => update(value, onChange, "description", event.target.value)}
            />
          </label>
          <label className="space-y-2 text-sm text-dark">
            <span className="font-medium">Instrucciones para responder</span>
            <textarea
              className="min-h-[130px] w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20"
              value={value.instructions}
              onChange={(event) => update(value, onChange, "instructions", event.target.value)}
            />
          </label>
        </SoftPanel>

        <SoftPanel className="space-y-4">
          <label className="space-y-2 text-sm text-dark">
            <span className="font-medium">Mensaje de agradecimiento</span>
            <textarea
              className="min-h-[110px] w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20"
              value={value.thankYouMessage}
              onChange={(event) => update(value, onChange, "thankYouMessage", event.target.value)}
            />
          </label>
          <label className="space-y-2 text-sm text-dark">
            <span className="font-medium">Estado inicial</span>
            <Select value={value.status} onChange={(event) => update(value, onChange, "status", event.target.value)}>
              <SelectOption value="draft">Borrador</SelectOption>
              <SelectOption value="published">Publicado</SelectOption>
            </Select>
          </label>
          <label className="flex items-center gap-3 rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark">
            <input
              checked={value.allowAnonymous}
              type="checkbox"
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                update(value, onChange, "allowAnonymous", event.target.checked)
              }
            />
            Permitir respuestas anonimas
          </label>
          <div className="rounded-2xl border border-dashed border-border bg-[#fffdf8] px-4 py-4 text-sm leading-6 text-muted">
            Publicar el formulario activara un link publico que luego podras copiar y compartir. Por ahora enfocate en que el contexto del instrumento sea claro y amable para quien responde.
          </div>
        </SoftPanel>
      </div>
    </div>
  );
}
