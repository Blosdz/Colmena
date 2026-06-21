import { brandTokens } from "./brandTokens";

export const colmenaTheme = {
  name: "colmena",
  sidebar: {
    background: "rgba(255,255,255,0.82)",
    border: brandTokens.colors.border,
  },
  cards: {
    glass: "rgba(255,255,255,0.72)",
    soft: brandTokens.colors.white,
  },
  status: {
    active: brandTokens.colors.turquoise,
    draft: brandTokens.colors.yellow,
    alert: brandTokens.colors.orange,
  },
  flow: ["Disena", "Publica", "Recolecta", "Analiza", "Presenta"],
} as const;
