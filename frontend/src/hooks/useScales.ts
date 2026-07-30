import { useQuery } from "@tanstack/react-query";

import { listScales } from "../api/scales";

/**
 * Fuente única de verdad de escalas: presets del sistema + del proyecto.
 * Reemplaza los presets hardcodeados del frontend.
 */
export function useScales(projectId?: string) {
  return useQuery({
    queryKey: ["scales", projectId ?? "system"],
    queryFn: () => listScales(projectId),
    staleTime: 5 * 60 * 1000, // los presets casi no cambian
  });
}
