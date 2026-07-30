import { Users, Hash, List, Type } from "lucide-react";

import { PARTICIPANT_PRESETS } from "../forms-wizard/scalePresets";
import { cn } from "../../utils/cn";

type Props = {
  selected: string[];
  onToggle: (presetId: string) => void;
};

const FIELD_TYPE_META: Record<string, { icon: React.ElementType; label: string }> = {
  number: { icon: Hash, label: "Número" },
  select: { icon: List, label: "Opciones" },
  text: { icon: Type, label: "Texto" },
};

/**
 * Panel a nivel de proyecto: qué datos del participante pedirá el formulario.
 * Cada dato marcado se convierte en una pregunta no puntuada de la sección
 * "Datos del participante" (question_role = "sociodemographic"), no en una variable.
 */
export function ParticipantDataPanel({ selected, onToggle }: Props) {
  return (
    <div className="max-w-[850px] mx-auto px-8 py-10" data-purpose="participant-data-form">
      <div className="flex items-start gap-4 mb-8">
        <div className="mt-1 text-colmena-orange">
          <Users className="w-7 h-7" strokeWidth={2} />
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-800">Datos del participante</h1>
          <p className="text-sm text-gray-400">
            Marca qué datos pedirá el formulario al inicio. No son variables de estudio: se
            guardan como una sección aparte y sirven para describir y segmentar la muestra.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {PARTICIPANT_PRESETS.map((preset) => {
          const active = selected.includes(preset.id);
          const meta = FIELD_TYPE_META[preset.fieldType] ?? FIELD_TYPE_META.text;
          const MetaIcon = meta.icon;
          return (
            <label
              key={preset.id}
              className={cn(
                "flex items-start gap-4 rounded-xl border p-4 cursor-pointer transition-all",
                active
                  ? "border-colmena-orange bg-colmena-orange/5 ring-1 ring-colmena-orange/30"
                  : "border-gray-200 bg-gray-50/30 hover:border-colmena-orange/40"
              )}
            >
              <input
                type="checkbox"
                className="mt-1 w-5 h-5 rounded text-colmena-orange focus:ring-colmena-orange border-gray-300 accent-colmena-orange"
                checked={active}
                onChange={() => onToggle(preset.id)}
              />
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-bold text-gray-800">{preset.name}</p>
                  <span className="inline-flex items-center gap-1 rounded-full bg-white border border-gray-200 px-2 py-0.5 text-[10px] font-semibold text-gray-500">
                    <MetaIcon className="w-3 h-3" />
                    {meta.label}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">{preset.description}</p>
                {preset.fieldType === "select" && (
                  <p className="text-[11px] text-gray-400 mt-1.5 italic truncate">
                    {preset.optionsText}
                  </p>
                )}
              </div>
            </label>
          );
        })}
      </div>

      <div className="pt-6">
        <p className="text-xs text-gray-400">
          Estas preguntas aparecerán primero en el formulario, en la sección{" "}
          <span className="font-bold text-gray-600">"Datos del participante"</span>, y no se
          incluyen en los puntajes de las escalas.
        </p>
      </div>
    </div>
  );
}
