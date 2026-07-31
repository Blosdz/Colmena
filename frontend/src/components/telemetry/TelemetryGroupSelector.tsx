import { useMemo } from "react";

import type { DimensionDescriptive, InstrumentDescriptive, ProjectVariableDescriptive } from "../../types/analysis";
import { Select, SelectOption } from "../ui/Select";

export const ALL_QUESTIONS_KEY = "all";

export function dimensionGroupKey(dimensionId: string) {
  return `dimension:${dimensionId}`;
}

export function variableGroupKey(variableId: string) {
  return `variable:${variableId}`;
}

interface TelemetryGroupSelectorProps {
  dimensions: DimensionDescriptive[];
  instruments: InstrumentDescriptive[];
  projectVariables: ProjectVariableDescriptive[];
  value: string;
  onChange: (key: string) => void;
}

/** Combo para filtrar las gráficas de Telemetría por dimensión o variable de proyecto. */
export function TelemetryGroupSelector({
  dimensions,
  instruments,
  projectVariables,
  value,
  onChange,
}: TelemetryGroupSelectorProps) {
  const instrumentNameByDimensionId = useMemo(() => {
    const map = new Map<string, string>();
    for (const instrument of instruments) {
      for (const dimension of instrument.dimensions) {
        map.set(dimension.dimension_id, instrument.name);
      }
    }
    return map;
  }, [instruments]);

  if (dimensions.length === 0 && projectVariables.length === 0) {
    return null;
  }

  return (
    <Select
      aria-label="Filtrar por dimensión o variable"
      className="w-full sm:w-auto sm:min-w-[240px]"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      <SelectOption value={ALL_QUESTIONS_KEY}>Todas las preguntas</SelectOption>
      {dimensions.length > 0 ? (
        <optgroup label="Dimensiones">
          {dimensions.map((dimension) => {
            const instrumentName = instrumentNameByDimensionId.get(dimension.dimension_id);
            return (
              <SelectOption key={dimension.dimension_id} value={dimensionGroupKey(dimension.dimension_id)}>
                {instrumentName ? `${instrumentName} — ${dimension.name}` : dimension.name}
              </SelectOption>
            );
          })}
        </optgroup>
      ) : null}
      {projectVariables.length > 0 ? (
        <optgroup label="Variables">
          {projectVariables.map((variable) => (
            <SelectOption key={variable.variable_id} value={variableGroupKey(variable.variable_id)}>
              {variable.name}
            </SelectOption>
          ))}
        </optgroup>
      ) : null}
    </Select>
  );
}
