"""Inferencia básica (harness §24-25, §47). Funciones puras sobre scipy.stats.

Cada función valida sus propios supuestos mínimos y devuelve `warnings`
estructurados en lugar de fallar silenciosamente (§47) — la decisión de
convertir un warning en error de dominio la toma `AnalysisService`.
"""

from __future__ import annotations

import math

from scipy import stats


def _effect_label(value: float, thresholds: tuple[float, float, float] = (0.1, 0.3, 0.5)) -> str:
    small, medium, _large = thresholds
    magnitude = abs(value)
    if magnitude < small:
        return "NEGLIGIBLE"
    if magnitude < medium:
        return "SMALL"
    if magnitude < thresholds[2]:
        return "MEDIUM"
    return "LARGE"


def compute_chi_square(table: list[list[int]]) -> dict:
    warnings: list[str] = []
    result = stats.chi2_contingency(table)
    statistic, p_value, dof, expected = result.statistic, result.pvalue, result.dof, result.expected_freq

    if (expected < 5).any():
        warnings.append(
            "Al menos una frecuencia esperada es menor a 5; el resultado del chi-cuadrado puede no ser confiable."
        )

    n = sum(sum(row) for row in table)
    min_dim = min(len(table), len(table[0])) - 1
    cramers_v = math.sqrt(statistic / (n * min_dim)) if n > 0 and min_dim > 0 else None

    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "degrees_freedom": int(dof),
        "n": n,
        "effect_size": cramers_v,
        "effect_label": _effect_label(cramers_v) if cramers_v is not None else None,
        "warnings": warnings,
    }


def compute_mann_whitney(group_a: list[float], group_b: list[float]) -> dict:
    result = stats.mannwhitneyu(group_a, group_b, alternative="two-sided")
    n1, n2 = len(group_a), len(group_b)
    rank_biserial = 1 - (2 * result.statistic) / (n1 * n2) if n1 and n2 else None

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "n1": n1,
        "n2": n2,
        "effect_size": rank_biserial,
        "effect_label": _effect_label(rank_biserial) if rank_biserial is not None else None,
        "warnings": [],
    }


def compute_kruskal_wallis(groups: list[list[float]]) -> dict:
    result = stats.kruskal(*groups)
    n_total = sum(len(g) for g in groups)
    k = len(groups)
    epsilon_squared = (result.statistic - k + 1) / (n_total - k) if n_total > k else None

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "degrees_freedom": k - 1,
        "n": n_total,
        "effect_size": epsilon_squared,
        "effect_label": _effect_label(epsilon_squared) if epsilon_squared is not None else None,
        "warnings": [],
    }


def compute_spearman(x: list[float], y: list[float]) -> dict:
    result = stats.spearmanr(x, y)
    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "n": len(x),
        "effect_size": float(result.statistic),
        "effect_label": _effect_label(float(result.statistic)),
        "warnings": [],
    }
