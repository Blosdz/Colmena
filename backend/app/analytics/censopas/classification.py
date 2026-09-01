"""Clasificación CENSOPAS por constructo y colectiva (harness §29-30). Funciones puras.

Nunca hardcodear estos umbrales en el router — la regla debe poder
versionarse/configurarse (§30). `DEFAULT_COLLECTIVE_RULES` es el valor
inicial descrito en el harness; se puede sobreescribir por parámetro.
"""

from __future__ import annotations

import statistics

# Códigos estables usados por BaremBand.classification_code — el motor de
# scoring (ScoringService) los busca en este idioma/forma exacta; nunca
# deben derivarse del texto de un `label` (que sí es libre/traducible).
BAND_CODE_FAVORABLE = "FAVORABLE"
BAND_CODE_INTERMEDIATE = "INTERMEDIATE"
BAND_CODE_UNFAVORABLE = "UNFAVORABLE"

DEFAULT_COLLECTIVE_RULES = {
    "version": "v1",
    "unfavorable_threshold_pct": 50.0,
    "favorable_threshold_pct": 50.0,
}


def classify_construct_score(
    score_0_100: float,
    cut_1: float,
    cut_2: float,
    direction: str | None,
    favorable_label: str = "FAVORABLE",
    intermediate_label: str = "INTERMEDIO",
    unfavorable_label: str = "DESFAVORABLE",
) -> str:
    """Clasifica un score 0-100 contra los cortes de un barem.

    `direction`:
        HIGHER_BETTER (default) -> score alto es favorable.
        LOWER_BETTER            -> score alto es desfavorable (riesgo).
    """
    lo, hi = sorted((cut_1, cut_2))
    if direction == "LOWER_BETTER":
        if score_0_100 <= lo:
            return favorable_label
        if score_0_100 <= hi:
            return intermediate_label
        return unfavorable_label

    if score_0_100 <= lo:
        return unfavorable_label
    if score_0_100 <= hi:
        return intermediate_label
    return favorable_label


def classify_collective_result(
    favorable_pct: float,
    intermediate_pct: float,
    unfavorable_pct: float,
    rules: dict | None = None,
) -> str:
    """Regla colectiva configurable (harness §30):

    rojo (desfavorable) >= 50%   -> riesgo alto
    verde (favorable) >= 50%     -> factor protector
    amarillo (intermedio) predominante -> riesgo medio
    otro                          -> revisión
    """
    active_rules = {**DEFAULT_COLLECTIVE_RULES, **(rules or {})}

    if unfavorable_pct >= active_rules["unfavorable_threshold_pct"]:
        return "RIESGO_ALTO"
    if favorable_pct >= active_rules["favorable_threshold_pct"]:
        return "FACTOR_PROTECTOR"
    if intermediate_pct > favorable_pct and intermediate_pct > unfavorable_pct:
        return "RIESGO_MEDIO"
    return "REVISION"


def cutoff_to_bands(
    cut_1: float,
    cut_2: float,
    direction: str | None,
    favorable_label: str,
    intermediate_label: str,
    unfavorable_label: str,
) -> list[dict]:
    """Deriva las 3 bandas ejecutables (`BaremBand`) desde un corte trichotomy
    (`BaremCutoff`). Es la única función que debe crear bandas a partir de un
    corte — `BaremCutoff` es la fuente autoral, `BaremBand` es el artefacto
    de ejecución que consume el motor de scoring.

    `classification_code` siempre queda en {FAVORABLE, INTERMEDIATE,
    UNFAVORABLE} sin importar el idioma de los `label` visibles, para que el
    motor de scoring nunca tenga que inferir semántica de un texto libre.
    """
    lo, hi = sorted((float(cut_1), float(cut_2)))
    if direction == "HIGHER_BETTER":
        ranges = [
            (BAND_CODE_UNFAVORABLE, unfavorable_label, 0.0, lo, "#ef4444"),
            (BAND_CODE_INTERMEDIATE, intermediate_label, lo, hi, "#f59e0b"),
            (BAND_CODE_FAVORABLE, favorable_label, hi, 100.0, "#22c55e"),
        ]
    else:
        ranges = [
            (BAND_CODE_FAVORABLE, favorable_label, 0.0, lo, "#22c55e"),
            (BAND_CODE_INTERMEDIATE, intermediate_label, lo, hi, "#f59e0b"),
            (BAND_CODE_UNFAVORABLE, unfavorable_label, hi, 100.0, "#ef4444"),
        ]
    return [
        {
            "code": code,
            "label": label,
            "min_value": minimum,
            "max_value": maximum,
            "severity_order": order,
            "classification_code": code,
            "color_hint": color,
        }
        for order, (code, label, minimum, maximum, color) in enumerate(ranges, start=1)
    ]


def summarize_trichotomy(values: list[tuple[float, str | None]]) -> dict:
    """Resume pares `(score_0_100, classification_code)` ya orientados en el
    trichotomy favorable/intermedio/desfavorable + clasificación colectiva
    (harness §29-30). Única función que debe construir este resumen — la usan
    tanto el resultado a nivel de estudio como el resultado por unidad, para
    no duplicar el cálculo entre ambos.
    """
    n_valid = len(values)
    if n_valid == 0:
        return {
            "n_valid": 0,
            "favorable_n": 0,
            "intermediate_n": 0,
            "unfavorable_n": 0,
            "favorable_pct": None,
            "intermediate_pct": None,
            "unfavorable_pct": None,
            "construct_score": None,
            "classification": None,
        }
    categories = [category for _, category in values]
    favorable_n = categories.count(BAND_CODE_FAVORABLE)
    intermediate_n = categories.count(BAND_CODE_INTERMEDIATE)
    unfavorable_n = categories.count(BAND_CODE_UNFAVORABLE)
    favorable_pct = round((favorable_n / n_valid) * 100, 4)
    intermediate_pct = round((intermediate_n / n_valid) * 100, 4)
    unfavorable_pct = round((unfavorable_n / n_valid) * 100, 4)
    classification = (
        classify_collective_result(favorable_pct, intermediate_pct, unfavorable_pct)
        if favorable_n or intermediate_n or unfavorable_n
        else None
    )
    return {
        "n_valid": n_valid,
        "favorable_n": favorable_n,
        "intermediate_n": intermediate_n,
        "unfavorable_n": unfavorable_n,
        "favorable_pct": favorable_pct,
        "intermediate_pct": intermediate_pct,
        "unfavorable_pct": unfavorable_pct,
        "construct_score": statistics.fmean(score for score, _ in values),
        "classification": classification,
    }
