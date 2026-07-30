import type { CatalogScale } from "../components/forms/BulkQuestionTable";

/** Escala por defecto para una variable nueva: preferimos "Acuerdo · 5 puntos"
 *  (el Likert clásico de tesis), si no existe usamos la primera escala de sistema disponible. */
export function resolveDefaultCatalogScale(catalogScales: CatalogScale[]): CatalogScale | undefined {
  const systemScales = catalogScales.filter((s) => s.project_id == null);
  return (
    systemScales.find((s) => s.scale_kind === "acuerdo" && s.points === 5) ??
    systemScales[0] ??
    catalogScales[0]
  );
}
