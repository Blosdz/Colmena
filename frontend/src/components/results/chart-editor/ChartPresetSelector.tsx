import type { ChartThemeName } from "../../../types/chartEditor";
import { getPresetLabel } from "../../../utils/chartFormatters";

const descriptions: Record<ChartThemeName, string> = {
  academic_light: "Fondo blanco y lectura sobria para tesis.",
  colmena_premium: "Paleta miel y acentos calidos de Colmena.",
  presentation_clean: "Mayor contraste para exposiciones.",
  monochrome_apa: "Escala de grises para Word o impresion.",
};

const order: ChartThemeName[] = [
  "academic_light",
  "colmena_premium",
  "presentation_clean",
  "monochrome_apa",
];

export function ChartPresetSelector({
  value,
  onChange,
}: {
  value: ChartThemeName;
  onChange: (value: ChartThemeName) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <h4 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Preset visual</h4>
        <p className="text-sm text-muted">Cambia la intencion del grafico sin tocar el resultado estadistico.</p>
      </div>
      <div className="grid gap-2">
        {order.map((theme) => (
          <button
            className={`rounded-2xl border px-4 py-3 text-left transition ${
              value === theme
                ? "border-amber bg-surfaceSoft shadow-card"
                : "border-border bg-white hover:border-amber/40 hover:bg-[#fcfbf7]"
            }`}
            key={theme}
            onClick={() => onChange(theme)}
            type="button"
          >
            <p className="text-sm font-semibold text-dark">{getPresetLabel(theme)}</p>
            <p className="mt-1 text-xs leading-5 text-muted">{descriptions[theme]}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
