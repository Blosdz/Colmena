"""Corrección Benjamini-Hochberg (harness §25). Función pura, sin scipy."""

from __future__ import annotations


def adjust_pvalues_bh(values: list[float]) -> list[float]:
    """Devuelve p-valores ajustados (FDR) en el mismo orden que `values`."""
    m = len(values)
    if m == 0:
        return []

    indexed = sorted(enumerate(values), key=lambda item: item[1])
    adjusted = [0.0] * m

    prev_min = 1.0
    for rank in range(m, 0, -1):
        original_index, p_value = indexed[rank - 1]
        candidate = min(p_value * m / rank, 1.0)
        prev_min = min(prev_min, candidate)
        adjusted[original_index] = prev_min

    return adjusted
