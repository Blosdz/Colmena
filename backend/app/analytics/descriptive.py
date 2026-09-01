"""Estadística descriptiva mínima (harness §22).

Funciones puras: no tocan la base de datos ni conocen de `Variable` o
`Response`. Reciben listas de valores numéricos ya extraídos y filtrados de
missing por el llamador (`AnalysisService`).
"""

from __future__ import annotations

import statistics


def compute_descriptive(values: list[float]) -> dict:
    n_valid = len(values)
    if n_valid == 0:
        return {
            "n_valid": 0,
            "mean": None,
            "median": None,
            "mode": None,
            "std": None,
            "variance": None,
            "min": None,
            "max": None,
            "quartiles": None,
        }

    mode = statistics.mode(values)
    quartiles = None
    if n_valid >= 2:
        q1, q2, q3 = statistics.quantiles(values, n=4, method="inclusive")
        quartiles = [q1, q2, q3]

    return {
        "n_valid": n_valid,
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "mode": mode,
        "std": statistics.stdev(values) if n_valid >= 2 else 0.0,
        "variance": statistics.variance(values) if n_valid >= 2 else 0.0,
        "min": min(values),
        "max": max(values),
        "quartiles": quartiles,
    }
