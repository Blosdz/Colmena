from __future__ import annotations

from typing import Any

import pandas as pd

DEFAULT_LEVEL_NAMES = ["Muy Bajo", "Bajo", "Medio", "Alto", "Muy Alto"]
THREE_LEVEL_NAMES = ["Bajo", "Medio", "Alto"]


def compute_equal_range_baremo(
    min_score: float,
    max_score: float,
    levels_count: int = 3,
    aggregation_method: str | None = None,
) -> list[dict[str, Any]]:
    """Baremo de rangos iguales.

    Para escalas de puntaje entero (suma de items, `aggregation_method == "sum"`
    con limites teoricos enteros) usa la formula documentada de la tesis:
    ancho = (max - min + 1) / niveles, con cortes enteros contiguos sin huecos
    ni solapamientos. Para escalas continuas (p.ej. promedio de items) mantiene
    la formula de paso continuo `step = (max - min) / niveles`.

    Mantiene la misma formula que frontend/src/utils/baremoCalculator.ts para que
    los baremos calculados en la resolucion coincidan con los del builder visual.
    """
    if levels_count <= 0 or min_score >= max_score:
        return []

    names = THREE_LEVEL_NAMES if levels_count == 3 else DEFAULT_LEVEL_NAMES
    is_integer_range = float(min_score).is_integer() and float(max_score).is_integer()
    levels: list[dict[str, Any]] = []

    if aggregation_method == "sum" and is_integer_range:
        min_i = int(min_score)
        max_i = int(max_score)
        width = (max_i - min_i + 1) / levels_count
        boundaries = [min_i + round(width * index) for index in range(levels_count)] + [max_i + 1]
        for index in range(levels_count):
            label = names[index] if index < len(names) else f"Nivel {index + 1}"
            levels.append(
                {
                    "label": label,
                    "min_value": float(boundaries[index]),
                    "max_value": float(boundaries[index + 1] - 1),
                    "severity_order": index,
                    "interpretation": None,
                    "source": "equal_range_formula",
                }
            )
        return levels

    step = (max_score - min_score) / levels_count
    for index in range(levels_count):
        current_min = min_score if index == 0 else round((min_score + step * index) * 10) / 10
        current_max = (
            max_score
            if index == levels_count - 1
            else round((min_score + step * (index + 1) - 0.1) * 10) / 10
        )
        label = names[index] if index < len(names) else f"Nivel {index + 1}"
        levels.append(
            {
                "label": label,
                "min_value": current_min,
                "max_value": current_max,
                "severity_order": index,
                "interpretation": None,
                "source": "equal_range_formula",
            }
        )
    return levels


def compute_percentile_baremo(
    scores: list[float],
    levels_count: int = 5,
) -> list[dict[str, Any]]:
    """Baremo por percentiles: los cortes de nivel son los percentiles
    observados de la muestra (P20/P40/P60/P80 para 5 niveles, P33/P66 para 3),
    en vez de repartir el rango teorico en partes iguales.
    """
    cleaned = sorted(float(value) for value in scores if value is not None)
    if len(cleaned) < 2 or levels_count <= 0:
        return []

    series = pd.Series(cleaned)
    names = THREE_LEVEL_NAMES if levels_count == 3 else DEFAULT_LEVEL_NAMES
    cut_points = [round(100 * (index + 1) / levels_count, 4) for index in range(levels_count - 1)]
    boundaries = [float(series.min())] + [
        float(series.quantile(cut / 100)) for cut in cut_points
    ] + [float(series.max())]

    levels: list[dict[str, Any]] = []
    for index in range(levels_count):
        current_min = boundaries[index] if index == 0 else round(boundaries[index] + 0.01, 3)
        current_max = boundaries[index + 1]
        label = names[index] if index < len(names) else f"Nivel {index + 1}"
        levels.append(
            {
                "label": label,
                "min_value": round(current_min, 3),
                "max_value": round(current_max, 3),
                "severity_order": index,
                "interpretation": None,
                "source": "percentile_formula",
            }
        )
    return levels


def compute_mean_sd_baremo(
    scores: list[float],
    levels_count: int = 5,
) -> list[dict[str, Any]]:
    """Baremo por media +/- desviacion estandar: los cortes se ubican en
    multiplos de 0.5 DE alrededor de la media (metodo normativo clasico de
    escalas psicometricas: M-1.5DE, M-0.5DE, M+0.5DE, M+1.5DE para 5 niveles).
    """
    cleaned = [float(value) for value in scores if value is not None]
    if len(cleaned) < 2 or levels_count <= 0:
        return []

    series = pd.Series(cleaned)
    mean = float(series.mean())
    sd = float(series.std(ddof=1))
    names = THREE_LEVEL_NAMES if levels_count == 3 else DEFAULT_LEVEL_NAMES

    if sd == 0:
        return []

    half_span = levels_count / 2
    cut_offsets = [-half_span + step for step in range(1, levels_count)]
    interior_cuts = [round(mean + offset * sd, 3) for offset in cut_offsets]
    boundaries = [float(series.min())] + interior_cuts + [float(series.max())]

    levels: list[dict[str, Any]] = []
    for index in range(levels_count):
        current_min = boundaries[index] if index == 0 else round(boundaries[index] + 0.01, 3)
        current_max = boundaries[index + 1]
        label = names[index] if index < len(names) else f"Nivel {index + 1}"
        levels.append(
            {
                "label": label,
                "min_value": round(current_min, 3),
                "max_value": round(current_max, 3),
                "severity_order": index,
                "interpretation": None,
                "source": "mean_sd_formula",
            }
        )
    return levels


def levels_from_score_bands(bands: list[Any]) -> list[dict[str, Any]]:
    active = sorted(
        (band for band in bands if getattr(band, "deleted_at", None) is None),
        key=lambda item: (int(getattr(item, "severity_order", 0)), float(item.min_value)),
    )
    return [
        {
            "label": band.label,
            "min_value": float(band.min_value),
            "max_value": float(band.max_value),
            "severity_order": int(getattr(band, "severity_order", 0)),
            "interpretation": getattr(band, "interpretation", None),
            "source": "configured_bands",
        }
        for band in active
    ]


def resolve_level_for_score(score: float | None, levels: list[dict[str, Any]]) -> dict[str, Any] | None:
    if score is None:
        return None
    for level in levels:
        if level["min_value"] <= score <= level["max_value"]:
            return level
    return None
