/**
 * Skins visuales del formulario que ven los encuestados (PublicFormPage) y del
 * preview del diseñador (SurveyThemePicker). Se guarda en
 * `forms.metadata_json` como `{ theme: SurveyTheme, ... }`.
 *
 * La parte estructural de cada skin (radios, grosor de borde, tipografía,
 * mayúsculas en labels) vive en index.css bajo `.survey-shell` /
 * `[data-survey-skin="modernist"]`. Este módulo sólo describe lo que el
 * usuario puede elegir y editar.
 */

export type SurveySkinId = "colmena" | "modernist";
export type QuestionsPerScreen = "single" | "all";
export type SurveyAlign = "center" | "left";

export interface SurveyColors {
  accent: string;
  bg: string;
  text: string;
}

export interface SurveyLayout {
  questionsPerScreen: QuestionsPerScreen;
  align: SurveyAlign;
}

export interface SurveyTheme {
  skin: SurveySkinId;
  colors: SurveyColors;
  layout: SurveyLayout;
}

interface SkinDef {
  id: SurveySkinId;
  label: string;
  description: string;
  fontLabel: string;
  defaultColors: SurveyColors;
}

export const DEFAULT_SURVEY_SKIN: SurveySkinId = "colmena";

export const SURVEY_SKINS: Record<SurveySkinId, SkinDef> = {
  colmena: {
    id: "colmena",
    label: "Colmena",
    description: "Vidrio, ámbar y esquinas suaves — el estilo por defecto de la app.",
    fontLabel: "Inter",
    defaultColors: { accent: "#F5B21A", bg: "#FAFAF8", text: "#111111" },
  },
  modernist: {
    id: "modernist",
    label: "Modernista",
    description: "Editorial, esquinas rectas y tipografía Archivo. Alto contraste.",
    fontLabel: "Archivo",
    defaultColors: { accent: "#EC3013", bg: "#F3F2F2", text: "#201E1D" },
  },
};

export const EDITABLE_SURVEY_COLORS: { key: keyof SurveyColors; label: string }[] = [
  { key: "accent", label: "Color de acento" },
  { key: "bg", label: "Fondo" },
  { key: "text", label: "Texto" },
];

export const QUESTIONS_PER_SCREEN_OPTIONS: {
  id: QuestionsPerScreen;
  label: string;
  description: string;
}[] = [
  {
    id: "single",
    label: "Una sección a la vez",
    description: "Tarjeta centrada, avanza con Atrás / Continuar.",
  },
  {
    id: "all",
    label: "Todo en una pantalla",
    description: "Lista completa en una sola vista.",
  },
];

export const ALIGN_OPTIONS: { id: SurveyAlign; label: string }[] = [
  { id: "center", label: "Centrado" },
  { id: "left", label: "A la izquierda" },
];

export const DEFAULT_SURVEY_LAYOUT: SurveyLayout = {
  questionsPerScreen: "single",
  align: "center",
};

export function getSurveySkin(skinId: string | undefined): SkinDef {
  return SURVEY_SKINS[(skinId as SurveySkinId) ?? DEFAULT_SURVEY_SKIN] ?? SURVEY_SKINS[DEFAULT_SURVEY_SKIN];
}

/**
 * Normaliza cualquier cosa guardada (incluido el formato viejo
 * `{primaryColor, backgroundColor}`) a un `SurveyTheme` completo.
 */
export function resolveSurveyTheme(raw: unknown): SurveyTheme {
  const t = (raw ?? {}) as Record<string, unknown>;
  const skin = getSurveySkin(typeof t.skin === "string" ? t.skin : undefined);

  // Compatibilidad con el diseñador anterior.
  const legacyAccent = typeof t.primaryColor === "string" ? t.primaryColor : undefined;
  const legacyBg =
    typeof t.backgroundColor === "string" && t.backgroundColor !== "system"
      ? t.backgroundColor
      : undefined;

  const savedColors = (t.colors ?? {}) as Partial<SurveyColors>;
  const layout = (t.layout ?? {}) as Partial<SurveyLayout>;

  return {
    skin: skin.id,
    colors: {
      accent: savedColors.accent ?? legacyAccent ?? skin.defaultColors.accent,
      bg: savedColors.bg ?? legacyBg ?? skin.defaultColors.bg,
      text: savedColors.text ?? skin.defaultColors.text,
    },
    layout: {
      questionsPerScreen: layout.questionsPerScreen === "all" ? "all" : "single",
      align: layout.align === "left" ? "left" : "center",
    },
  };
}

/** CSS custom properties para inyectar inline sobre `.survey-shell`. */
export function buildSurveyThemeVars({ colors }: Pick<SurveyTheme, "colors">): React.CSSProperties {
  return {
    ["--survey-accent" as string]: colors.accent,
    ["--survey-bg" as string]: colors.bg,
    ["--survey-text" as string]: colors.text,
  };
}
