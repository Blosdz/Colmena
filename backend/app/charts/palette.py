"""Paleta aleatoria de barras, generada en el backend.

Antes cada gráfico sorteaba sus colores en el navegador. Al moverlo aquí, el
color que se ve en pantalla es el mismo que acaba en el PNG del reporte Word:
el frontend pide la paleta, la usa tal cual en el gráfico 2D y la manda de
vuelta al construir el `option` del 3D.

El sorteo reparte los tonos sobre la rueda de color y luego los baraja, para
que "aleatorio" no signifique "ilegible": dos barras nunca comparten tono y las
vecinas no quedan en degradado. Saturación y luminosidad se mantienen acotadas
para que las barras contrasten sobre el fondo blanco de las tarjetas.
"""

from __future__ import annotations

import colorsys
import random

# Rangos que mantienen las barras legibles sobre blanco: ni lavadas ni tan
# oscuras que las etiquetas de valor encima dejen de leerse.
SATURATION_RANGE = (0.58, 0.78)
LIGHTNESS_RANGE = (0.42, 0.54)


def _hsl_to_hex(hue_degrees: float, saturation: float, lightness: float) -> str:
    # colorsys usa HLS (no HSL) y el tono normalizado a [0, 1).
    red, green, blue = colorsys.hls_to_rgb((hue_degrees % 360) / 360, lightness, saturation)
    return "#{:02X}{:02X}{:02X}".format(round(red * 255), round(green * 255), round(blue * 255))


def random_bar_colors(count: int, *, seed: str | None = None) -> list[str]:
    """`count` colores distintos entre sí, legibles sobre fondo blanco.

    Con `seed` el sorteo es reproducible (mismo seed → misma paleta), útil para
    que un gráfico conserve sus colores entre recargas. Sin `seed` cada llamada
    devuelve una paleta nueva.
    """
    if count <= 0:
        return []

    rng = random.Random(seed) if seed is not None else random.Random()

    offset = rng.random() * 360
    step = 360 / count
    hues = [(offset + index * step) % 360 for index in range(count)]
    # Sin barajar, las barras saldrían ordenadas en degradado de tono.
    rng.shuffle(hues)

    return [
        _hsl_to_hex(hue, rng.uniform(*SATURATION_RANGE), rng.uniform(*LIGHTNESS_RANGE))
        for hue in hues
    ]
