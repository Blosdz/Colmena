"""Normalidad complementaria para puntuaciones agregadas de constructos."""

from __future__ import annotations

import math
import statistics

import numpy as np
from scipy import stats


def compute_normality(values: list[float], histogram_bins: int = 10) -> dict:
    n = len(values)
    warnings: list[str] = []
    base = {
        "n": n,
        "mean": statistics.fmean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "standard_deviation": statistics.stdev(values) if n >= 2 else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
        "test": None,
        "statistic": None,
        "p_value": None,
        "status": "INCONCLUSO",
        "warnings": warnings,
        "histogram": [],
    }
    if values:
        counts, edges = np.histogram(values, bins=min(histogram_bins, max(1, n)))
        base["histogram"] = [
            {
                "min_value": float(edges[index]),
                "max_value": float(edges[index + 1]),
                "n": int(count),
            }
            for index, count in enumerate(counts)
        ]
    if n < 3:
        warnings.append("Se requieren al menos 3 observaciones para evaluar normalidad.")
        return base
    if len(set(values)) < 2:
        warnings.append("Todos los valores son iguales; la prueba de normalidad no es interpretable.")
        return base

    result = stats.shapiro(values) if n <= 5000 else stats.normaltest(values)
    statistic = float(result.statistic)
    p_value = float(result.pvalue)
    if math.isnan(statistic) or math.isnan(p_value):
        warnings.append("La prueba no produjo un resultado numérico interpretable.")
        return base
    base.update(
        test="SHAPIRO_WILK" if n <= 5000 else "DAGOSTINO_PEARSON",
        statistic=statistic,
        p_value=p_value,
        status="COMPATIBLE_CON_NORMALIDAD" if p_value >= 0.05 else "NO_NORMAL",
    )
    if n > 5000:
        warnings.append(
            "Para muestras mayores a 5000 se usa D'Agostino-Pearson; complemente con el histograma."
        )
    return base
