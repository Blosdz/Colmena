import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { getBarPalette } from "../api/charts";
import { randomBarColors } from "../utils/chartColors";

/**
 * Paleta de barras de un gráfico, sorteada por el backend.
 *
 * Se pide una sola vez por gráfico (`chartKey`) y se cachea para toda la
 * sesión: alternar 2D/3D o volver a montar la tarjeta no vuelve a sortear los
 * colores. Recargar la página sí los cambia, como antes.
 *
 * `chartKey` separa el sorteo de cada gráfico; sin él, dos gráficos con el
 * mismo número de barras compartirían la paleta cacheada.
 *
 * Si la petición falla se cae a `randomBarColors` en el navegador: un gráfico
 * con colores locales es mejor que un gráfico sin pintar, aunque en ese caso
 * los colores no coincidan con los del reporte.
 */
export function useBarPalette(count: number, chartKey: string) {
  const query = useQuery({
    queryKey: ["chart-palette", chartKey, count],
    queryFn: () => getBarPalette(count),
    enabled: count > 0,
    staleTime: Infinity,
    gcTime: Infinity,
  });

  const fallback = useMemo(() => randomBarColors(count), [count]);

  return {
    colors: query.isError ? fallback : query.data?.colors,
    /** Mientras es `true` no hay colores todavía: conviene no pintar aún. */
    isPending: count > 0 && !query.isError && query.data === undefined,
  };
}
