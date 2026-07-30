export type VariablePreset = {
  id: string;
  name: string;
  code: string;
  measurementLevel: string;
  dataType: string;
  fieldType: "number" | "select" | "text";
  optionsText: string;
  description: string;
};

export const VARIABLE_PRESETS: VariablePreset[] = [
  {
    id: "nombre",
    name: "Nombre",
    code: "nombre",
    measurementLevel: "nominal",
    dataType: "text",
    fieldType: "text",
    optionsText: "",
    description: "Nombre o iniciales del participante.",
  },
  {
    id: "edad",
    name: "Edad",
    code: "edad",
    measurementLevel: "ratio",
    dataType: "numeric",
    fieldType: "number",
    optionsText: "",
    description: "Edad del participante en años cumplidos.",
  },
  {
    id: "sexo",
    name: "Sexo",
    code: "sexo",
    measurementLevel: "nominal",
    dataType: "categorical",
    fieldType: "select",
    optionsText: "Femenino, Masculino, Prefiero no decirlo",
    description: "Sexo del participante.",
  },
  {
    id: "estado_civil",
    name: "Estado civil",
    code: "estado_civil",
    measurementLevel: "nominal",
    dataType: "categorical",
    fieldType: "select",
    optionsText: "Soltero/a, Casado/a, Union libre, Divorciado/a, Viudo/a",
    description: "Estado civil del participante.",
  },
  {
    id: "nivel_educativo",
    name: "Nivel educativo",
    code: "nivel_educativo",
    measurementLevel: "ordinal",
    dataType: "categorical",
    fieldType: "select",
    optionsText: "Primaria, Secundaria, Tecnico, Universitario, Posgrado",
    description: "Maximo nivel educativo alcanzado.",
  },
  {
    id: "ocupacion",
    name: "Ocupacion",
    code: "ocupacion",
    measurementLevel: "nominal",
    dataType: "text",
    fieldType: "text",
    optionsText: "",
    description: "Ocupacion actual del participante.",
  },
];

// Alias semántico: estos presets alimentan la sección fija "Datos del participante".
export const PARTICIPANT_PRESETS = VARIABLE_PRESETS;
