import { Plus, Trash2 } from "lucide-react";

import type { WizardBaremDraft, WizardFormContext, WizardLieScaleDraft } from "./FormWizard";
import { WizardStepHeader } from "./WizardStepHeader";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select, SelectOption } from "../ui/Select";
import { SoftPanel } from "../ui/SoftPanel";

function createBarem(): WizardBaremDraft {
  return {
    id: `barem-${crypto.randomUUID()}`,
    min: "",
    max: "",
    label: "",
    interpretation: "",
  };
}

type StepScoringValue = WizardFormContext & {
  scoringMethod: string;
  missingPolicy: string;
  minAnsweredItems: string;
  minCompletionPercent: string;
  scoreByDimension: boolean;
  totalScoreLabel: string;
  barems: WizardBaremDraft[];
  lieScale: WizardLieScaleDraft;
};

export function StepScoringRules({
  value,
  onChange,
}: {
  value: StepScoringValue;
  onChange: (next: StepScoringValue) => void;
}) {
  const updateBarem = (baremId: string, patch: Partial<WizardBaremDraft>) => {
    onChange({
      ...value,
      barems: value.barems.map((item) => (item.id === baremId ? { ...item, ...patch } : item)),
    });
  };

  const removeBarem = (baremId: string) => {
    const nextBarems = value.barems.filter((item) => item.id !== baremId);
    onChange({
      ...value,
      barems: nextBarems.length > 0 ? nextBarems : [createBarem()],
    });
  };

  const updateControlScale = (patch: Partial<WizardLieScaleDraft>) => {
    onChange({
      ...value,
      lieScale: { ...value.lieScale, ...patch },
    });
  };

  return (
    <div className="space-y-6">
      <WizardStepHeader
        step="Paso 7"
        title="Scoring, baremos y escalas de control"
        description="Aqui defines como calcular puntajes, cuando advertir por respuestas incompletas y como clasificar los resultados por nivel."
      />

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <SoftPanel className="space-y-5">
          <div className="space-y-2">
            <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-muted">Calculo del instrumento</h3>
            <p className="text-sm leading-6 text-muted">
              Define el metodo principal, el criterio de completitud y si Colmena debe entregar resultados por dimension.
            </p>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Metodo de calculo</span>
              <Select value={value.scoringMethod} onChange={(event) => onChange({ ...value, scoringMethod: event.target.value })}>
                <SelectOption value="sum">Suma</SelectOption>
                <SelectOption value="mean">Promedio</SelectOption>
                <SelectOption value="weighted_mean">Promedio ponderado</SelectOption>
              </Select>
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Politica ante valores perdidos</span>
              <Select value={value.missingPolicy} onChange={(event) => onChange({ ...value, missingPolicy: event.target.value })}>
                <SelectOption value="strict_complete">Exigir respuestas completas</SelectOption>
                <SelectOption value="allow_partial">Permitir parciales</SelectOption>
                <SelectOption value="prorate_if_threshold_met">Prorratear si se cumple el umbral</SelectOption>
              </Select>
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Minimo de items respondidos</span>
              <Input
                inputMode="numeric"
                placeholder="Ej. 8"
                value={value.minAnsweredItems}
                onChange={(event) => onChange({ ...value, minAnsweredItems: event.target.value })}
              />
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Completitud minima (%)</span>
              <Input
                inputMode="decimal"
                placeholder="Ej. 70"
                value={value.minCompletionPercent}
                onChange={(event) => onChange({ ...value, minCompletionPercent: event.target.value })}
              />
            </label>
            <label className="space-y-2 text-sm text-dark xl:col-span-2">
              <span className="font-medium">Etiqueta del puntaje total</span>
              <Input
                value={value.totalScoreLabel}
                onChange={(event) => onChange({ ...value, totalScoreLabel: event.target.value })}
              />
            </label>
          </div>

          <label className="flex items-center gap-3 rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark">
            <input
              checked={value.scoreByDimension}
              type="checkbox"
              onChange={(event) => onChange({ ...value, scoreByDimension: event.target.checked })}
            />
            Calcular y reportar resultados por dimension cuando el instrumento las tenga definidas
          </label>

          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-muted">Baremos</h3>
                <p className="text-sm text-muted">Agrega rangos como Bajo, Medio y Alto con su interpretacion breve.</p>
              </div>
              <Button onClick={() => onChange({ ...value, barems: [...value.barems, createBarem()] })} size="sm" variant="secondary">
                <Plus className="mr-2 h-4 w-4" />
                Agregar rango
              </Button>
            </div>
            {value.barems.map((barem) => (
              <div className="grid gap-3 rounded-2xl border border-border bg-white p-3 xl:grid-cols-[110px_110px_160px_minmax(220px,1fr)_90px]" key={barem.id}>
                <Input placeholder="Min" value={barem.min} onChange={(event) => updateBarem(barem.id, { min: event.target.value })} />
                <Input placeholder="Max" value={barem.max} onChange={(event) => updateBarem(barem.id, { max: event.target.value })} />
                <Input placeholder="Bajo" value={barem.label} onChange={(event) => updateBarem(barem.id, { label: event.target.value })} />
                <Input
                  placeholder="Interpretacion del rango"
                  value={barem.interpretation}
                  onChange={(event) => updateBarem(barem.id, { interpretation: event.target.value })}
                />
                <Button onClick={() => removeBarem(barem.id)} size="sm" variant="ghost">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </SoftPanel>

        <SoftPanel className="space-y-5">
          <div className="space-y-2">
            <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-muted">Escala de control</h3>
            <p className="text-sm leading-6 text-muted">
              Usa esta regla para detectar respuestas sospechosas, poco consistentes o que ameriten advertencia metodologica.
            </p>
          </div>

          <label className="flex items-center gap-3 rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark">
            <input
              checked={value.lieScale.enabled}
              type="checkbox"
              onChange={(event) => updateControlScale({ enabled: event.target.checked })}
            />
            Activar escala de control
          </label>

          <div className="grid gap-4 xl:grid-cols-2">
            <label className="space-y-2 text-sm text-dark xl:col-span-2">
              <span className="font-medium">Nombre</span>
              <Input value={value.lieScale.name} onChange={(event) => updateControlScale({ name: event.target.value })} />
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Tipo</span>
              <Select value={value.lieScale.controlType} onChange={(event) => updateControlScale({ controlType: event.target.value })}>
                <SelectOption value="lie">Mentira</SelectOption>
                <SelectOption value="attention">Atencion</SelectOption>
                <SelectOption value="infrequency">Infrecuencia</SelectOption>
                <SelectOption value="consistency">Consistencia</SelectOption>
                <SelectOption value="custom">Personalizada</SelectOption>
              </Select>
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Regla</span>
              <Select value={value.lieScale.ruleType} onChange={(event) => updateControlScale({ ruleType: event.target.value })}>
                <SelectOption value="sum_threshold">Suma umbral</SelectOption>
                <SelectOption value="mean_threshold">Promedio umbral</SelectOption>
                <SelectOption value="count_failed">Conteo de fallos</SelectOption>
                <SelectOption value="any_failed">Cualquier fallo</SelectOption>
                <SelectOption value="paired_inconsistency">Inconsistencia emparejada</SelectOption>
              </Select>
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Comparacion</span>
              <Select value={value.lieScale.comparisonOperator} onChange={(event) => updateControlScale({ comparisonOperator: event.target.value })}>
                <SelectOption value="gte">Mayor o igual</SelectOption>
                <SelectOption value="gt">Mayor que</SelectOption>
                <SelectOption value="lte">Menor o igual</SelectOption>
                <SelectOption value="lt">Menor que</SelectOption>
                <SelectOption value="eq">Igual a</SelectOption>
              </Select>
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Accion</span>
              <Select value={value.lieScale.flagLevel} onChange={(event) => updateControlScale({ flagLevel: event.target.value })}>
                <SelectOption value="warning">Advertir</SelectOption>
                <SelectOption value="invalid">Invalidar</SelectOption>
              </Select>
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Umbral</span>
              <Input
                inputMode="decimal"
                placeholder="Ej. 4"
                value={value.lieScale.threshold}
                onChange={(event) => updateControlScale({ threshold: event.target.value })}
              />
            </label>
            <label className="space-y-2 text-sm text-dark">
              <span className="font-medium">Codigo interno</span>
              <Input value={value.lieScale.code} onChange={(event) => updateControlScale({ code: event.target.value })} />
            </label>
            <label className="space-y-2 text-sm text-dark xl:col-span-2">
              <span className="font-medium">Items asociados</span>
              <Input
                placeholder="item_02, item_07"
                value={value.lieScale.linkedItemCodes}
                onChange={(event) => updateControlScale({ linkedItemCodes: event.target.value })}
              />
            </label>
            <label className="space-y-2 text-sm text-dark xl:col-span-2">
              <span className="font-medium">Mensaje</span>
              <textarea
                className="min-h-[120px] w-full rounded-2xl border border-border bg-white px-4 py-3 text-sm text-dark outline-none transition focus:border-amber focus:ring-2 focus:ring-amber/20"
                value={value.lieScale.message}
                onChange={(event) => updateControlScale({ message: event.target.value })}
              />
            </label>
          </div>
        </SoftPanel>
      </div>
    </div>
  );
}
