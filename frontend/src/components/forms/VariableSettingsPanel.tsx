import { Check } from "lucide-react";

import type {
  VariableDraft,
  VariableMeta,
  VariableRole,
  VariableClassification,
} from "../../utils/projectDraftStore";
import { deriveMeasurementLevel } from "../../utils/projectDraftStore";
import { cn } from "../../utils/cn";

type Props = {
  variable: VariableDraft;
  onChange: (updates: Partial<VariableMeta>) => void;
};

// El formulario solo expone estos 3 tipos de variable metodológica.
// Internamente se siguen guardando como (variableRole, variableClassification)
// para no romper compatibilidad con el backend / proyectos existentes.
type VariableTypeOption = {
  value: "independent" | "dependent" | "intervening";
  label: string;
  role: VariableRole;
  classification: VariableClassification;
};

const VARIABLE_TYPES: VariableTypeOption[] = [
  { value: "independent", label: "Variable independiente", role: "main", classification: "independent" },
  { value: "dependent", label: "Variable dependiente", role: "main", classification: "dependent" },
  { value: "intervening", label: "Variable interviniente", role: "intervening", classification: null },
];

function resolveVariableType(role: VariableRole, classification: VariableClassification): VariableTypeOption["value"] {
  if (role === "intervening") return "intervening";
  if (classification === "dependent") return "dependent";
  return "independent";
}

const LEVEL_LABELS: Record<string, string> = {
  nominal: "Nominal",
  ordinal: "Ordinal",
  interval: "Intervalo",
  ratio: "Razón",
};

const LABEL_CLS = "block text-[10px] font-bold text-gray-500 uppercase mb-2 tracking-wide";
const FIELD_CLS =
  "w-full p-3 border border-gray-200 rounded-lg focus:ring-colmena-orange focus:border-colmena-orange bg-gray-50/30 outline-none transition";

export function VariableSettingsPanel({ variable, onChange }: Props) {
  const derivedLevel = deriveMeasurementLevel(variable.measurementMode, variable.dataType);

  return (
    <div className="max-w-[850px] mx-auto px-8 py-10" data-purpose="variable-definition-form">
      {/* Section Heading */}
      <div className="flex items-start gap-4 mb-8">
        <div className="mt-1 text-2xl text-colmena-orange">∑</div>
        <div>
          <h1 className="text-lg font-bold text-gray-800">Definición de la variable</h1>
          <p className="text-sm text-gray-400">
            Cuéntanos qué mides. El nivel estadístico lo deducimos por ti.
          </p>
        </div>
      </div>

      <div className="space-y-8">
        {/* Row 1: Names */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <label className={LABEL_CLS}>Nombre de la variable *</label>
            <input
              className={FIELD_CLS}
              type="text"
              placeholder="Ej. Autoestima"
              value={variable.name}
              onChange={(e) => onChange({ name: e.target.value })}
            />
          </div>
          <div className="col-span-4">
            <label className={LABEL_CLS}>Código</label>
            <input
              className={`${FIELD_CLS} uppercase`}
              type="text"
              placeholder="AUTOEST"
              value={variable.code}
              onChange={(e) => onChange({ code: e.target.value.toUpperCase() })}
            />
          </div>
        </div>

        {/* Row 2: Variable type */}
        <div>
          <label className={LABEL_CLS}>¿Qué tipo de variable es?</label>
          <div className="grid grid-cols-3 gap-3">
            {VARIABLE_TYPES.map((t) => (
              <RolePill
                key={t.value}
                label={t.label}
                active={resolveVariableType(variable.variableRole, variable.variableClassification) === t.value}
                onClick={() => onChange({ variableRole: t.role, variableClassification: t.classification })}
              />
            ))}
          </div>
        </div>

        {/* Row 3: Derived measurement level (read-only, educational) */}
        <div className="flex items-center gap-3 rounded-lg border border-dashed border-gray-200 bg-gray-50/40 px-4 py-3">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wide">Nivel de medición</span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-colmena-orange/10 px-3 py-1 text-[12px] font-bold text-colmena-orange">
            <Check className="w-3.5 h-3.5" />
            {LEVEL_LABELS[derivedLevel]}
          </span>
          <span className="text-[11px] text-gray-400">· detectado automáticamente</span>
        </div>

        {/* Row 6: Description */}
        <div>
          <label className={LABEL_CLS}>Descripción</label>
          <textarea
            className={`${FIELD_CLS} resize-none`}
            placeholder="Definición conceptual y operacional de la variable..."
            rows={3}
            value={variable.description}
            onChange={(e) => onChange({ description: e.target.value })}
          />
        </div>

        {/* Row 7: Checkbox Card */}
        <label className="p-4 border border-gray-200 rounded-lg bg-gray-50/30 flex items-start gap-4 cursor-pointer hover:border-colmena-orange/40 transition-colors">
          <input
            className="mt-1 w-5 h-5 rounded text-colmena-orange focus:ring-colmena-orange border-gray-300 accent-colmena-orange"
            type="checkbox"
            checked={variable.isRequiredForAnalysis}
            onChange={(e) => onChange({ isRequiredForAnalysis: e.target.checked })}
          />
          <div>
            <p className="text-sm font-bold text-gray-800">Obligatoria para el análisis</p>
            <p className="text-xs text-gray-400">
              Debe tener datos completos para incluirse en los cálculos estadísticos.
            </p>
          </div>
        </label>

        {/* Footer Help Text */}
        <div className="pt-2">
          <p className="text-xs text-gray-400">
            Siguiente paso → define las <span className="font-bold text-gray-600">dimensiones</span> y la{" "}
            <span className="font-bold text-gray-600">escala</span>, luego agrega las{" "}
            <span className="font-bold text-gray-600">preguntas (ítems)</span>.
          </p>
        </div>
      </div>
    </div>
  );
}

function RolePill({
  label,
  active,
  small,
  onClick,
}: {
  label: string;
  active: boolean;
  small?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-lg border font-semibold transition-all",
        small ? "px-2 py-1.5 text-[11px]" : "px-4 py-2.5 text-[13px]",
        active
          ? "border-colmena-orange bg-colmena-orange/5 text-colmena-orange ring-1 ring-colmena-orange/30"
          : "border-gray-200 bg-gray-50/30 text-gray-600 hover:border-colmena-orange/40"
      )}
    >
      {label}
    </button>
  );
}
