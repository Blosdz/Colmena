import { apiClient } from "./client";

export interface PaletteRead {
  colors: string[];
}

/** Paleta aleatoria de barras. La sortea el backend para que pantalla y reporte Word coincidan. */
export function getBarPalette(count: number, seed?: string) {
  return apiClient.get<PaletteRead>("/api/v1/charts/palette", { count, seed });
}
