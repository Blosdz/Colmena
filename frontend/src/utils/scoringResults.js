import { semanticBand } from './chartColors.js';

// Filas con el contrato trichotomy de CENSOPAS (ConstructResultRead) traen
// favorable_pct/intermediate_pct/unfavorable_pct explícitos en vez de un
// arreglo `bands` — evita que este helper tenga que adivinar cuál banda es
// "desfavorable" leyendo el texto de un label.
const CENSOPAS_BANDS = [
  { code: 'FAVORABLE', label: 'Favorable', key: 'favorable_pct' },
  { code: 'INTERMEDIATE', label: 'Intermedio', key: 'intermediate_pct' },
  { code: 'UNFAVORABLE', label: 'Desfavorable', key: 'unfavorable_pct' },
];

function isCensopasTrichotomyResult(result) {
  return result != null && result.unfavorable_pct !== undefined && result.bands === undefined;
}

/** Banda dominante (mayor %) de un resultado de constructo. */
export function dominantBand(result) {
  if (isCensopasTrichotomyResult(result)) {
    const bands = CENSOPAS_BANDS.map((band) => ({ ...band, pct: result[band.key] || 0 }));
    return bands.reduce((best, band) => (band.pct > best.pct ? band : best), bands[0]);
  }
  if (!result?.bands?.length) return null;
  return result.bands.reduce((best, band) => ((band.pct || 0) > (best.pct || 0) ? band : best), result.bands[0]);
}

/** % de la banda semánticamente "desfavorable" (alto riesgo) de un resultado. */
export function unfavorablePct(result) {
  if (isCensopasTrichotomyResult(result)) return result.unfavorable_pct || 0;
  return (
    result.bands?.find((band) => (band.classification_code || band.code) === 'UNFAVORABLE')?.pct ??
    result.bands?.find((band) => semanticBand(band.label) === 'unfavorable')?.pct ??
    0
  );
}
