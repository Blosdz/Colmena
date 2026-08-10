import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../api/client";
import { deleteChartPalette, getChartPalette, saveChartPalette } from "../api/chartPalettes";

/**
 * Colores por barra de un gráfico, con la paleta personalizada que el usuario
 * haya guardado (persistida por formulario) por encima de la paleta por
 * defecto (`defaultColors`: la pastel semáforo del baremo, o la sorteada por
 * `useBarPalette` en los demás gráficos).
 *
 * Si la cantidad de colores guardados no coincide con `count` (p. ej. cambió
 * el número de barras porque cambiaron los datos), se ignora la paleta
 * guardada y se cae a `defaultColors` en vez de pintar colores de más o de
 * menos.
 */
export function useChartColors(
  formId: string,
  chartKey: string,
  count: number,
  defaultColors: string[],
) {
  const queryClient = useQueryClient();
  const queryKey = ["chart-palette-custom", formId, chartKey];

  const query = useQuery({
    queryKey,
    queryFn: async () => {
      try {
        return await getChartPalette(formId, chartKey);
      } catch (error) {
        // 404 = todavía no hay paleta guardada para este gráfico, no es un error.
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    enabled: Boolean(formId && chartKey) && count > 0,
  });

  const saved = query.data?.colors;
  const isCustom = Boolean(saved && saved.length === count);
  const colors = useMemo(() => (isCustom ? (saved as string[]) : defaultColors), [isCustom, saved, defaultColors]);

  const saveMutation = useMutation({
    mutationFn: (next: string[]) => saveChartPalette(formId, chartKey, next),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  });

  const resetMutation = useMutation({
    mutationFn: () => deleteChartPalette(formId, chartKey),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  });

  return {
    colors,
    isCustom,
    save: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    reset: resetMutation.mutate,
    isResetting: resetMutation.isPending,
  };
}
