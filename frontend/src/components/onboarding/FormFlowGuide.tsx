import { SoftPanel } from "../ui/SoftPanel";

const steps = [
  "Variables y roles",
  "Instrumento y dimensiones",
  "Items y escala de respuesta",
  "Scoring, baremos y control",
  "Revision, publicacion y link",
];

export function FormFlowGuide() {
  return (
    <SoftPanel className="space-y-3">
      <h3 className="text-sm font-semibold text-dark">Camino del formulario</h3>
      <div className="space-y-2.5">
        {steps.map((step, index) => (
          <div className="flex items-center gap-3 text-sm text-dark" key={step}>
            <span className="flex h-7 w-7 items-center justify-center rounded-full border border-turquoise/20 bg-turquoiseSoft text-xs font-semibold text-turquoiseDark">
              {index + 1}
            </span>
            {step}
          </div>
        ))}
      </div>
    </SoftPanel>
  );
}
