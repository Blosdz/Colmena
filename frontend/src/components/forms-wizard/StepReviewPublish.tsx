import type {
  WizardBaremDraft,
  WizardDimensionDraft,
  WizardFormContext,
  WizardInstrumentDraft,
  WizardItemDraft,
  WizardScaleOptionDraft,
  WizardVariableDraft,
} from "./FormWizard";
import { WizardStepHeader } from "./WizardStepHeader";
import { SoftPanel } from "../ui/SoftPanel";

export function StepReviewPublish({
  value,
  projectTitle,
}: {
  value: WizardFormContext & {
    variables: WizardVariableDraft[];
    instrument: WizardInstrumentDraft;
    dimensions: WizardDimensionDraft[];
    items: WizardItemDraft[];
    responseScale: WizardScaleOptionDraft[];
    scoringMethod: string;
    barems: WizardBaremDraft[];
    missingPolicy: string;
    minCompletionPercent: string;
    minAnsweredItems: string;
    lieScale: {
      enabled: boolean;
      name: string;
      linkedItemCodes: string;
      flagLevel: string;
    };
  };
  projectTitle?: string;
}) {
  const reverseCount = value.items.filter((item) => item.reversed).length;

  return (
    <div className="space-y-6">
      <WizardStepHeader
        step="Paso 8"
        title="Revision y publicacion"
        description="Antes de guardar, revisa que la estructura del instrumento tenga sentido para quien respondera y para quien analizara resultados."
      />

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <SoftPanel className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Proyecto</p>
              <p className="mt-2 text-base font-semibold text-dark">{projectTitle || "Proyecto actual"}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Formulario</p>
              <p className="mt-2 text-base font-semibold text-dark">{value.title || "Sin titulo"}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Instrumento</p>
              <p className="mt-2 text-base font-semibold text-dark">{value.instrument.name || "Sin nombre"}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Metodo de scoring</p>
              <p className="mt-2 text-base font-semibold text-dark">{value.scoringMethod}</p>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl border border-border bg-white px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Variables</p>
              <p className="mt-2 text-3xl font-semibold text-dark">{value.variables.filter((item) => item.name.trim()).length}</p>
            </div>
            <div className="rounded-2xl border border-border bg-white px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Dimensiones</p>
              <p className="mt-2 text-3xl font-semibold text-dark">{value.dimensions.filter((item) => item.name.trim()).length}</p>
            </div>
            <div className="rounded-2xl border border-border bg-white px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Items</p>
              <p className="mt-2 text-3xl font-semibold text-dark">{value.items.filter((item) => item.text.trim()).length}</p>
            </div>
          </div>
        </SoftPanel>

        <SoftPanel className="space-y-4">
          <h3 className="text-lg font-semibold text-dark">Checklist de salida</h3>
          <ul className="space-y-3 text-sm leading-6 text-muted">
            <li>La escala base aplicara {value.responseScale.filter((item) => item.label.trim()).length} opciones sobre los items Likert.</li>
            <li>{reverseCount > 0 ? `${reverseCount} items invertidos` : "Aun no marcaste items invertidos"} se guardaran como parte del scoring real.</li>
            <li>{value.barems.filter((item) => item.label.trim()).length} rangos interpretativos se guardaran como baremos reales del instrumento.</li>
            <li>
              Politica de completitud: {value.missingPolicy}. Umbral minimo: {value.minAnsweredItems || "sin minimo fijo"} items y {value.minCompletionPercent || "sin porcentaje"}%.
            </li>
            <li>
              {value.lieScale.enabled
                ? `La escala de control ${value.lieScale.name || "activa"} quedara registrada con accion ${value.lieScale.flagLevel}.`
                : "La escala de control esta desactivada por ahora."}
            </li>
            <li>Al publicar, Colmena activara el link publico y podras copiarlo de inmediato.</li>
          </ul>
        </SoftPanel>
      </div>
    </div>
  );
}
