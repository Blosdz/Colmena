import { Plus, Trash2 } from "lucide-react";

import type { WizardFormContext, WizardVariableDraft } from "./FormWizard";
import { WizardStepHeader } from "./WizardStepHeader";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select, SelectOption } from "../ui/Select";
import { SoftPanel } from "../ui/SoftPanel";

function createVariable(): WizardVariableDraft {
  return {
    id: `var-${crypto.randomUUID()}`,
    name: "",
    code: "",
    role: "resultado",
    measurementLevel: "ordinal",
    dataType: "numeric",
    description: "",
    notes: "",
    requiredForAnalysis: true,
  };
}

export function StepVariables({
  value,
  onChange,
}: {
  value: WizardFormContext & { variables: WizardVariableDraft[]; instrument: { variableId: string } };
  onChange: (next: WizardFormContext & { variables: WizardVariableDraft[]; instrument: { variableId: string } }) => void;
}) {
  const updateVariable = (variableId: string, patch: Partial<WizardVariableDraft>) => {
    onChange({
      ...value,
      variables: value.variables.map((item) => (item.id === variableId ? { ...item, ...patch } : item)),
      instrument: value.instrument.variableId ? value.instrument : { ...value.instrument, variableId },
    });
  };

  const removeVariable = (variableId: string) => {
    const nextVariables = value.variables.filter((item) => item.id !== variableId);
    onChange({
      ...value,
      variables: nextVariables.length > 0 ? nextVariables : [createVariable()],
      instrument:
        value.instrument.variableId === variableId
          ? { ...value.instrument, variableId: nextVariables[0]?.id ?? "" }
          : value.instrument,
    });
  };

  return (
    <div className="space-y-6">
      <WizardStepHeader
        step="Paso 2"
        title="Variables del estudio"
        description="Define las variables base del proyecto para que luego puedas enlazar instrumentos, analisis y reportes de forma coherente."
      />

      <div className="grid gap-4">
        {value.variables.map((variable, index) => (
          <SoftPanel className="space-y-4" key={variable.id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-dark">Variable {index + 1}</p>
                <p className="text-xs text-muted">Ejemplo: ansiedad academica, sexo, semestre, rendimiento.</p>
              </div>
              <Button onClick={() => removeVariable(variable.id)} size="sm" variant="ghost">
                <Trash2 className="mr-2 h-4 w-4" />
                Quitar
              </Button>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <label className="space-y-2 text-sm text-dark">
                <span className="font-medium">Nombre</span>
                <Input
                  value={variable.name}
                  onChange={(event) => updateVariable(variable.id, { name: event.target.value })}
                />
              </label>
              <label className="space-y-2 text-sm text-dark">
                <span className="font-medium">Codigo</span>
                <Input
                  placeholder="VAR_01"
                  value={variable.code}
                  onChange={(event) => updateVariable(variable.id, { code: event.target.value })}
                />
              </label>
              <label className="space-y-2 text-sm text-dark">
                <span className="font-medium">Rol</span>
                <Select value={variable.role} onChange={(event) => updateVariable(variable.id, { role: event.target.value })}>
                  <SelectOption value="sociodemografica">Sociodemografica</SelectOption>
                  <SelectOption value="independiente">Independiente</SelectOption>
                  <SelectOption value="dependiente">Dependiente</SelectOption>
                  <SelectOption value="interviniente">Interviniente</SelectOption>
                  <SelectOption value="control">Control</SelectOption>
                  <SelectOption value="agrupacion">Agrupacion</SelectOption>
                  <SelectOption value="resultado">Resultado</SelectOption>
                </Select>
              </label>
              <label className="space-y-2 text-sm text-dark">
                <span className="font-medium">Nivel de medicion</span>
                <Select
                  value={variable.measurementLevel}
                  onChange={(event) => updateVariable(variable.id, { measurementLevel: event.target.value })}
                >
                  <SelectOption value="nominal">Nominal</SelectOption>
                  <SelectOption value="ordinal">Ordinal</SelectOption>
                  <SelectOption value="interval">Intervalo</SelectOption>
                  <SelectOption value="ratio">Razon</SelectOption>
                </Select>
              </label>
              <label className="space-y-2 text-sm text-dark">
                <span className="font-medium">Tipo de dato</span>
                <Select value={variable.dataType} onChange={(event) => updateVariable(variable.id, { dataType: event.target.value })}>
                  <SelectOption value="numeric">Numerico</SelectOption>
                  <SelectOption value="text">Texto</SelectOption>
                  <SelectOption value="categorical">Categorico</SelectOption>
                  <SelectOption value="boolean">Booleano</SelectOption>
                </Select>
              </label>
              <label className="flex items-center gap-3 rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark">
                <input
                  checked={variable.requiredForAnalysis}
                  type="checkbox"
                  onChange={(event) => updateVariable(variable.id, { requiredForAnalysis: event.target.checked })}
                />
                Marcar como variable clave para resultados
              </label>
            </div>

            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Descripcion</span>
              <textarea
                className="min-h-[92px] w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20"
                value={variable.description}
                onChange={(event) => updateVariable(variable.id, { description: event.target.value })}
              />
            </label>
          </SoftPanel>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={() => onChange({ ...value, variables: [...value.variables, createVariable()] })}
          variant="secondary"
        >
          <Plus className="mr-2 h-4 w-4" />
          Agregar variable
        </Button>
        <p className="text-sm text-muted">
          Usa variables de agrupacion para comparaciones y variables resultado para los puntajes principales.
        </p>
      </div>
    </div>
  );
}
