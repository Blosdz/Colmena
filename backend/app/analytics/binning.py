"""Agregación de pares (x, y) en bins (E-09). Función pura.

Ninguna coordenada individual exacta debe salir del backend cuando se
solicitan puntos de un scatter (Manual §6.3): en vez de devolver los pares
crudos, se agregan en una grilla rectangular y sólo se expone el conteo por
celda. Grilla N×N simple en vez de hexbin real, para no añadir dependencias
geométricas — suficiente para dibujar un scatter agregado en el frontend.
"""

from __future__ import annotations


def bin_points(points: list[tuple[float, float]], bin_count: int = 10) -> list[dict]:
    if not points:
        return []

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_max == x_min:
        x_max = x_min + 1.0
    if y_max == y_min:
        y_max = y_min + 1.0
    x_width = (x_max - x_min) / bin_count
    y_width = (y_max - y_min) / bin_count

    counts: dict[tuple[int, int], int] = {}
    for x, y in points:
        ix = min(int((x - x_min) / x_width), bin_count - 1)
        iy = min(int((y - y_min) / y_width), bin_count - 1)
        counts[(ix, iy)] = counts.get((ix, iy), 0) + 1

    return [
        {
            "x_bin_center": round(x_min + (ix + 0.5) * x_width, 4),
            "y_bin_center": round(y_min + (iy + 0.5) * y_width, 4),
            "n": n,
        }
        for (ix, iy), n in sorted(counts.items())
    ]
