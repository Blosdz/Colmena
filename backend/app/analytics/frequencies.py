"""Frecuencias y porcentajes (harness §22-23). Funciones puras."""

from __future__ import annotations

from collections import Counter


def compute_frequencies(values: list[str]) -> dict:
    n_valid = len(values)
    counts = Counter(values)
    categories = [
        {
            "value": value,
            "n": n,
            "pct": round((n / n_valid) * 100, 2) if n_valid else 0.0,
        }
        for value, n in sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))
    ]
    return {"n_valid": n_valid, "categories": categories}
