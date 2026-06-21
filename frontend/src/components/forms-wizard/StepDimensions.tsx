import { Plus, Trash2 } from "lucide-react";

import type { WizardDimensionDraft, WizardFormContext } from "./FormWizard";
import { WizardStepHeader } from "./WizardStepHeader";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { SoftPanel } from "../ui/SoftPanel";

function createDimension(sortOrder: number): WizardDimensionDraft {
  return {
    id: `dim-${crypto.randomUUID()}`,
    name: `Dimension ${sortOrder + 1}`,
    code: `D${sortOrder + 1}`,
    description: "",
    sortOrder,
  };
}

export function StepDimensions({
  value,
  onChange,
}: {
  value: WizardFormContext & { dimensions: WizardDimensionDraft[] };
  onChange: (next: WizardFormContext & { dimensions: WizardDimensionDraft[] }) => void;
}) {
  const updateDimension = (dimensionId: string, patch: Partial<WizardDimensionDraft>) => {
    onChange({
      ...value,
      dimensions: value.dimensions.map((item) => (item.id === dimensionId ? { ...item, ...patch } : item)),
    });
  };

  const removeDimension = (dimensionId: string) => {
    const nextDimensions = value.dimensions.filter((item) => item.id !== dimensionId);
    onChange({
      ...value,
      dimensions: nextDimensions.length > 0 ? nextDimensions : [createDimension(0)],
    });
  };

  return (
    <div className="space-y-6">
      <WizardStepHeader
        step="Paso 4"
        title="Dimensiones"
        description="Organiza los items en dimensiones para que el sistema pueda calcular subtotales, graficos y tablas con mayor claridad."
      />

      <div className="grid gap-4">
        {value.dimensions.map((dimension, index) => (
          <SoftPanel className="space-y-4" key={dimension.id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-dark">Dimension {index + 1}</p>
                <p className="text-xs text-muted">Puedes enlazar los items del instrumento a cada bloque.</p>
              </div>
              <Button onClick={() => removeDimension(dimension.id)} size="sm" variant="ghost">
                <Trash2 className="mr-2 h-4 w-4" />
                Quitar
              </Button>
            </div>

            <div className="grid gap-4 xl:grid-cols-3">
              <label className="space-y-2 text-sm text-dark">
                <span className="font-medium">Nombre</span>
                <Input
                  value={dimension.name}
                  onChange={(event) => updateDimension(dimension.id, { name: event.target.value })}
                />
              </label>
              <label className="space-y-2 text-sm text-dark">
                <span className="font-medium">Codigo</span>
                <Input
                  value={dimension.code}
                  onChange={(event) => updateDimension(dimension.id, { code: event.target.value })}
                />
              </label>
              <label className="space-y-2 text-sm text-dark">
                <span className="font-medium">Orden</span>
                <Input
                  type="number"
                  value={dimension.sortOrder}
                  onChange={(event) => updateDimension(dimension.id, { sortOrder: Number(event.target.value) || 0 })}
                />
              </label>
            </div>

            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Descripcion</span>
              <textarea
                className="min-h-[96px] w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20"
                value={dimension.description}
                onChange={(event) => updateDimension(dimension.id, { description: event.target.value })}
              />
            </label>
          </SoftPanel>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button
          onClick={() =>
            onChange({
              ...value,
              dimensions: [...value.dimensions, createDimension(value.dimensions.length)],
            })
          }
          variant="secondary"
        >
          <Plus className="mr-2 h-4 w-4" />
          Agregar dimension
        </Button>
      </div>
    </div>
  );
}
