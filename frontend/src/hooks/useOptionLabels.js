import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { listLikertScales } from '../api/instruments.js';

/**
 * Diccionario de etiquetas centralizado (D-13): resuelve `raw_code -> label`
 * usando el catálogo de opciones del instrumento, en vez de que cada panel
 * de resultados muestre el código crudo ("1", "2"...) tal como llega del
 * backend. Un solo lugar carga y cachea los `option_set` de la versión.
 */
export function useOptionLabels(instrumentVersionId) {
  const { data: scales = [], isLoading } = useQuery({
    queryKey: ['likertScales', instrumentVersionId],
    queryFn: () => listLikertScales(instrumentVersionId),
    enabled: Boolean(instrumentVersionId),
  });

  const byOptionSetId = useMemo(() => {
    const map = new Map();
    for (const scale of scales) {
      const options = new Map();
      for (const option of scale.options || []) {
        options.set(String(option.raw_code), option.label);
      }
      map.set(scale.id, options);
    }
    return map;
  }, [scales]);

  function resolveLabel(optionSetId, rawCode) {
    if (optionSetId == null || rawCode == null) return rawCode;
    return byOptionSetId.get(optionSetId)?.get(String(rawCode)) ?? rawCode;
  }

  return { resolveLabel, isLoading };
}

export default useOptionLabels;
