from __future__ import annotations

from typing import Any


def validate_bands_no_overlap(bands: list[Any]) -> list[str]:
    warnings: list[str] = []
    ordered = sorted(
        [band for band in bands if getattr(band, "deleted_at", None) is None],
        key=lambda item: (float(item.min_value), float(item.max_value), int(getattr(item, "severity_order", 0))),
    )
    for current, next_band in zip(ordered, ordered[1:]):
        if float(current.max_value) >= float(next_band.min_value):
            warnings.append("overlapping_bands")
            break
    return warnings


def resolve_score_band(score: float | None, bands: list[Any]) -> Any | None:
    if score is None:
        return None
    active_bands = [band for band in bands if getattr(band, "deleted_at", None) is None]
    ordered = sorted(active_bands, key=lambda item: (int(getattr(item, "severity_order", 0)), float(item.min_value)))
    for band in ordered:
        if float(band.min_value) <= float(score) <= float(band.max_value):
            return band
    return None


def build_band_interpretation(score: float | None, band: Any | None) -> str | None:
    if band is None:
        return None
    interpretation = getattr(band, "interpretation", None)
    if interpretation:
        return str(interpretation)
    label = getattr(band, "label", None)
    if label is None or score is None:
        return None
    return f"El puntaje se ubica en el rango {label}."
