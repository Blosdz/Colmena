// Colores aleatorios para las barras de los gráficos de reportes.
//
// La paleta que se usa normalmente la sortea el backend (`useBarPalette`), para
// que el color en pantalla sea el mismo que acaba en el PNG del reporte Word.
// Esto de aquí es la copia del algoritmo en el navegador, que solo entra si esa
// petición falla: mantener los dos lados en paridad es intencional
// (ver `backend/app/charts/palette.py`).
//
// Para que "aleatorio" no signifique "ilegible", los tonos se reparten sobre la
// rueda de color y luego se barajan: dos barras nunca comparten color y las
// vecinas no quedan en degradado. La saturación y la luminosidad se mantienen
// acotadas para que las barras contrasten sobre el fondo blanco de las tarjetas.

/** Convierte HSL (h en grados, s/l en %) a `#RRGGBB`. */
function hslToHex(h: number, s: number, l: number): string {
  const saturation = s / 100;
  const lightness = l / 100;
  const a = saturation * Math.min(lightness, 1 - lightness);
  const channel = (n: number) => {
    const k = (n + h / 30) % 12;
    const value = lightness - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    return Math.round(255 * value)
      .toString(16)
      .padStart(2, "0");
  };
  return `#${channel(0)}${channel(8)}${channel(4)}`;
}

/** `count` colores aleatorios distintos entre sí, legibles sobre fondo blanco. */
export function randomBarColors(count: number): string[] {
  if (count <= 0) return [];

  const offset = Math.random() * 360;
  const step = 360 / count;
  const hues = Array.from({ length: count }, (_, index) => (offset + index * step) % 360);

  // Fisher-Yates: sin barajar, las barras saldrían ordenadas en degradado de tono.
  for (let i = hues.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [hues[i], hues[j]] = [hues[j], hues[i]];
  }

  return hues.map((hue) =>
    hslToHex(hue, 58 + Math.random() * 20, 42 + Math.random() * 12),
  );
}

/** Añade el canal alfa a un `#RRGGBB` (formato `#RRGGBBAA`, entendido por Chart.js). */
export function withAlpha(hex: string, alpha: number): string {
  const clamped = Math.max(0, Math.min(1, alpha));
  const suffix = Math.round(clamped * 255)
    .toString(16)
    .padStart(2, "0");
  return `${hex}${suffix}`;
}
