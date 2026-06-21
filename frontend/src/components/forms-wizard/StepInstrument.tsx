import type { WizardFormContext, WizardInstrumentDraft, WizardVariableDraft } from "./FormWizard";
import { WizardStepHeader } from "./WizardStepHeader";
import { Input } from "../ui/Input";
import { Select, SelectOption } from "../ui/Select";
import { SoftPanel } from "../ui/SoftPanel";

export function StepInstrument({
  value,
  onChange,
}: {
  value: WizardFormContext & { variables: WizardVariableDraft[]; instrument: WizardInstrumentDraft };
  onChange: (next: WizardFormContext & { variables: WizardVariableDraft[]; instrument: WizardInstrumentDraft }) => void;
}) {
  const instrument = value.instrument;

  const updateInstrument = (patch: Partial<WizardInstrumentDraft>) => {
    onChange({ ...value, instrument: { ...value.instrument, ...patch } });
  };

  return (
    <div className="space-y-6">
      <WizardStepHeader
        step="Paso 3"
        title="Instrumento y escala base"
        description="Conecta el formulario con la variable principal y define la forma general en la que sera puntuado."
      />

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <SoftPanel className="space-y-4">
          <div className="grid gap-4 xl:grid-cols-2">
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Nombre del instrumento</span>
              <Input value={instrument.name} onChange={(event) => updateInstrument({ name: event.target.value })} />
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Acronimo</span>
              <Input value={instrument.acronym} onChange={(event) => updateInstrument({ acronym: event.target.value })} />
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Autor</span>
              <Input value={instrument.author} onChange={(event) => updateInstrument({ author: event.target.value })} />
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Anio</span>
              <Input value={instrument.year} onChange={(event) => updateInstrument({ year: event.target.value })} />
            </label>
            <label className="space-y-2 text-sm text-dark xl:col-span-2">
              <span className="font-medium">Variable vinculada</span>
              <Select value={instrument.variableId} onChange={(event) => updateInstrument({ variableId: event.target.value })}>
                <SelectOption value="">Selecciona una variable</SelectOption>
                {value.variables
                  .filter((variable) => variable.name.trim())
                  .map((variable) => (
                    <SelectOption key={variable.id} value={variable.id}>
                      {variable.name}
                    </SelectOption>
                  ))}
              </Select>
            </label>
          </div>

          <label className="space-y-2 text-sm text-dark">
            <span className="font-medium">Descripcion</span>
            <textarea
              className="min-h-[120px] w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20"
              value={instrument.description}
              onChange={(event) => updateInstrument({ description: event.target.value })}
            />
          </label>
        </SoftPanel>

        <SoftPanel className="space-y-4">
          <label className="space-y-2 text-sm text-dark">
            <span className="font-medium">Escala de respuesta</span>
            <Input
              value={instrument.responseScaleName}
              onChange={(event) => updateInstrument({ responseScaleName: event.target.value })}
            />
          </label>
          <label className="space-y-2 text-sm text-dark">
            <span className="font-medium">Metodo de puntuacion</span>
            <Select value={instrument.scoringMethod} onChange={(event) => updateInstrument({ scoringMethod: event.target.value })}>
              <SelectOption value="suma">Suma</SelectOption>
              <SelectOption value="promedio">Promedio</SelectOption>
              <SelectOption value="dimension">Por dimension</SelectOption>
              <SelectOption value="total_general">Total general</SelectOption>
            </Select>
          </label>
          <label className="flex items-center gap-3 rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark">
            <input
              checked={instrument.reverseScoringEnabled}
              type="checkbox"
              onChange={(event) => updateInstrument({ reverseScoringEnabled: event.target.checked })}
            />
            Este instrumento admite puntuacion inversa
          </label>
          <div className="rounded-2xl border border-dashed border-border bg-white px-4 py-4 text-sm leading-6 text-muted">
            Aqui defines el contrato general del instrumento. Los baremos, reglas de control y puntajes finales se
            afinan en el paso de scoring.
          </div>
        </SoftPanel>
      </div>
    </div>
  );
}
