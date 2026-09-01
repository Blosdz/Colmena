/**
 * Formato numérico centralizado (D-08, D-23): un solo lugar que decide
 * cuántos decimales se muestran y cómo se lee un p-valor — evita que cada
 * panel de resultados reimplemente su propio `.toFixed()` con distinto
 * número de decimales.
 */

const numberFormatter = new Intl.NumberFormat('es-PE', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 1,
});

const percentFormatter = new Intl.NumberFormat('es-PE', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 1,
});

export function formatNumber(value, { decimals = 1, fallback = '—' } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return fallback;
  if (decimals === 1) return numberFormatter.format(value);
  return new Intl.NumberFormat('es-PE', { maximumFractionDigits: decimals }).format(value);
}

export function formatPercent(value, { decimals = 0, fallback = '—' } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return fallback;
  const formatter =
    decimals === 1 ? percentFormatter : new Intl.NumberFormat('es-PE', { maximumFractionDigits: decimals });
  // Clampa a [0, 100] para evitar residuos de coma flotante como 100.0001%.
  const clamped = Math.min(100, Math.max(0, value));
  return `${formatter.format(clamped)}%`;
}

/** p-valores nunca se muestran como 0.0000 — bajo el umbral de precisión
 * visible se reporta como "< 0,001" en vez de un cero engañoso. */
export function formatPValue(value, { fallback = '—' } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return fallback;
  if (value < 0.001) return 'p < 0,001';
  return `p = ${formatNumber(value, { decimals: 3 })}`;
}
