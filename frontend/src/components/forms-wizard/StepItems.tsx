import { Plus, Trash2 } from "lucide-react";

import type { WizardDimensionDraft, WizardFormContext, WizardItemDraft } from "./FormWizard";
import { WizardStepHeader } from "./WizardStepHeader";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select, SelectOption } from "../ui/Select";
import { SoftPanel } from "../ui/SoftPanel";

function createItem(sortOrder: number): WizardItemDraft {
  return {
    id: `item-${crypto.randomUUID()}`,
    code: `item_${String(sortOrder + 1).padStart(2, "0")}`,
    text: "",
    dimensionId: "",
    questionType: "likert",
    required: true,
    scored: true,
    reversed: false,
    sortOrder,
  };
}

export function StepItems({
  value,
  onChange,
}: {
  value: WizardFormContext & { dimensions: WizardDimensionDraft[]; items: WizardItemDraft[] };
  onChange: (next: WizardFormContext & { dimensions: WizardDimensionDraft[]; items: WizardItemDraft[] }) => void;
}) {
  const updateItem = (itemId: string, patch: Partial<WizardItemDraft>) => {
    onChange({
      ...value,
      items: value.items.map((item) => (item.id === itemId ? { ...item, ...patch } : item)),
    });
  };

  const removeItem = (itemId: string) => {
    const nextItems = value.items.filter((item) => item.id !== itemId);
    onChange({
      ...value,
      items: nextItems.length > 0 ? nextItems : [createItem(0)],
    });
  };

  return (
    <div className="space-y-6">
      <WizardStepHeader
        step="Paso 5"
        title="Items del instrumento"
        description="Carga los items en una tabla rapida, marca si son puntuables y define si alguno debe leerse en sentido inverso."
      />

      <SoftPanel className="space-y-4 overflow-x-auto">
        <div className="min-w-[920px] space-y-3">
          <div className="grid grid-cols-[120px_minmax(260px,1fr)_180px_120px_90px_110px_110px_90px] gap-3 px-2 text-xs font-semibold uppercase tracking-[0.12em] text-muted">
            <span>Codigo</span>
            <span>Item</span>
            <span>Dimension</span>
            <span>Tipo</span>
            <span>Req.</span>
            <span>Puntuable</span>
            <span>Invertido</span>
            <span />
          </div>

          {value.items.map((item, index) => (
            <div
              className="grid grid-cols-[120px_minmax(260px,1fr)_180px_120px_90px_110px_110px_90px] gap-3 rounded-2xl border border-border bg-white p-3"
              key={item.id}
            >
              <Input value={item.code} onChange={(event) => updateItem(item.id, { code: event.target.value })} />
              <textarea
                className="min-h-[84px] w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20"
                placeholder={`Item ${index + 1}`}
                value={item.text}
                onChange={(event) => updateItem(item.id, { text: event.target.value })}
              />
              <Select value={item.dimensionId} onChange={(event) => updateItem(item.id, { dimensionId: event.target.value })}>
                <SelectOption value="">Sin dimension</SelectOption>
                {value.dimensions.map((dimension) => (
                  <SelectOption key={dimension.id} value={dimension.id}>
                    {dimension.name}
                  </SelectOption>
                ))}
              </Select>
              <Select value={item.questionType} onChange={(event) => updateItem(item.id, { questionType: event.target.value })}>
                <SelectOption value="likert">Likert</SelectOption>
                <SelectOption value="single_choice">Opcion unica</SelectOption>
                <SelectOption value="numeric">Numerica</SelectOption>
              </Select>
              <label className="flex items-center justify-center rounded-2xl border border-border bg-[#fffdf8]">
                <input
                  checked={item.required}
                  type="checkbox"
                  onChange={(event) => updateItem(item.id, { required: event.target.checked })}
                />
              </label>
              <label className="flex items-center justify-center rounded-2xl border border-border bg-[#fffdf8]">
                <input
                  checked={item.scored}
                  type="checkbox"
                  onChange={(event) => updateItem(item.id, { scored: event.target.checked })}
                />
              </label>
              <label className="flex items-center justify-center rounded-2xl border border-border bg-[#fffdf8]">
                <input
                  checked={item.reversed}
                  type="checkbox"
                  onChange={(event) => updateItem(item.id, { reversed: event.target.checked })}
                />
              </label>
              <Button onClick={() => removeItem(item.id)} size="sm" variant="ghost">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </SoftPanel>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={() => onChange({ ...value, items: [...value.items, createItem(value.items.length)] })}
          variant="secondary"
        >
          <Plus className="mr-2 h-4 w-4" />
          Agregar item
        </Button>
        <p className="text-sm text-muted">
          Marca aqui los items invertidos para que Colmena los use luego en el scoring real del instrumento.
        </p>
      </div>
    </div>
  );
}
