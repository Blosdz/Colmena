from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, pearsonr, pointbiserialr, spearmanr

from app.statistics.normality_engine import detect_outliers_iqr


def pairwise_valid_series(x: pd.Series, y: pd.Series) -> tuple[pd.Series, pd.Series]:
    pair_frame = pd.DataFrame(
        {
            "x": pd.to_numeric(x, errors="coerce"),
            "y": pd.to_numeric(y, errors="coerce"),
        }
    ).dropna()
    return pair_frame["x"], pair_frame["y"]


def classify_correlation_magnitude(coefficient: float | None) -> str:
    if coefficient is None:
        return "not_applicable"
    absolute = abs(float(coefficient))
    if absolute < 0.20:
        return "very_weak"
    if absolute < 0.40:
        return "weak"
    if absolute < 0.60:
        return "moderate"
    if absolute < 0.80:
        return "strong"
    return "very_strong"


CORRELATION_MAGNITUDE_LABELS: dict[str, str] = {
    "very_weak": "muy débil",
    "weak": "débil",
    "moderate": "moderada",
    "strong": "fuerte",
    "very_strong": "muy fuerte",
    "not_applicable": "no aplicable",
}


def correlation_magnitude_label(key: str | None) -> str:
    if key is None:
        return CORRELATION_MAGNITUDE_LABELS["not_applicable"]
    return CORRELATION_MAGNITUDE_LABELS.get(key, key)


def is_dichotomous(series: pd.Series) -> bool:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.empty:
        return False
    return cleaned.nunique(dropna=True) == 2


def classify_correlation_direction(coefficient: float | None) -> str:
    if coefficient is None:
        return "none"
    if abs(float(coefficient)) < 1e-12:
        return "none"
    return "positive" if coefficient > 0 else "negative"


def classify_significance(p_value: float | None, alpha: float) -> str:
    if p_value is None:
        return "not_applicable"
    return "statistically_significant" if p_value < alpha else "not_statistically_significant"


def detect_many_ties(series: pd.Series) -> bool:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.empty:
        return False
    unique_ratio = cleaned.nunique(dropna=True) / cleaned.size
    return unique_ratio <= 0.5


def _round(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    if np.isnan(value):
        return None
    return round(float(value), decimals)


def _base_not_applicable(method: str, alpha: float, reason: str) -> dict[str, Any]:
    return {
        "method_used": method,
        "coefficient": None,
        "p_value": None,
        "direction": "none",
        "magnitude": "not_applicable",
        "significance": "not_applicable",
        "classification": "not_applicable",
        "warnings": [reason],
        "assumptions": [],
    }


def pearson_correlation(x: pd.Series, y: pd.Series, *, alpha: float = 0.05, decimals: int = 3) -> dict[str, Any]:
    x_valid, y_valid = pairwise_valid_series(x, y)
    if len(x_valid) < 3:
        return _base_not_applicable("pearson", alpha, "insufficient_n")
    if x_valid.nunique(dropna=True) <= 1 or y_valid.nunique(dropna=True) <= 1:
        return _base_not_applicable("pearson", alpha, "constant_values")
    coefficient, p_value = pearsonr(x_valid.to_numpy(), y_valid.to_numpy())
    coefficient = _round(coefficient, decimals)
    p_value = _round(p_value, decimals)
    significance = classify_significance(p_value, alpha)
    return {
        "method_used": "pearson",
        "coefficient": coefficient,
        "p_value": p_value,
        "direction": classify_correlation_direction(coefficient),
        "magnitude": classify_correlation_magnitude(coefficient),
        "significance": significance,
        "classification": significance,
        "warnings": [],
        "assumptions": ["numeric_targets", "pairwise_complete_cases", "non_constant_series"],
    }


def spearman_correlation(x: pd.Series, y: pd.Series, *, alpha: float = 0.05, decimals: int = 3) -> dict[str, Any]:
    x_valid, y_valid = pairwise_valid_series(x, y)
    if len(x_valid) < 3:
        return _base_not_applicable("spearman", alpha, "insufficient_n")
    if x_valid.nunique(dropna=True) <= 1 or y_valid.nunique(dropna=True) <= 1:
        return _base_not_applicable("spearman", alpha, "constant_values")
    coefficient, p_value = spearmanr(x_valid.to_numpy(), y_valid.to_numpy())
    coefficient = _round(coefficient, decimals)
    p_value = _round(p_value, decimals)
    significance = classify_significance(p_value, alpha)
    return {
        "method_used": "spearman",
        "coefficient": coefficient,
        "p_value": p_value,
        "direction": classify_correlation_direction(coefficient),
        "magnitude": classify_correlation_magnitude(coefficient),
        "significance": significance,
        "classification": significance,
        "warnings": [],
        "assumptions": ["rank_based_method", "pairwise_complete_cases", "non_constant_series"],
    }


def kendall_correlation(x: pd.Series, y: pd.Series, *, alpha: float = 0.05, decimals: int = 3) -> dict[str, Any]:
    x_valid, y_valid = pairwise_valid_series(x, y)
    if len(x_valid) < 3:
        return _base_not_applicable("kendall", alpha, "insufficient_n")
    if x_valid.nunique(dropna=True) <= 1 or y_valid.nunique(dropna=True) <= 1:
        return _base_not_applicable("kendall", alpha, "constant_values")
    coefficient, p_value = kendalltau(x_valid.to_numpy(), y_valid.to_numpy())
    coefficient = _round(coefficient, decimals)
    p_value = _round(p_value, decimals)
    significance = classify_significance(p_value, alpha)
    return {
        "method_used": "kendall",
        "coefficient": coefficient,
        "p_value": p_value,
        "direction": classify_correlation_direction(coefficient),
        "magnitude": classify_correlation_magnitude(coefficient),
        "significance": significance,
        "classification": significance,
        "warnings": [],
        "assumptions": ["rank_based_method", "pairwise_complete_cases", "non_constant_series"],
    }


def point_biserial_correlation(x: pd.Series, y: pd.Series, *, alpha: float = 0.05, decimals: int = 3) -> dict[str, Any]:
    x_valid, y_valid = pairwise_valid_series(x, y)
    if len(x_valid) < 3:
        return _base_not_applicable("point_biserial", alpha, "insufficient_n")
    # Identifica el lado dicotómico (exactamente 2 valores distintos) y el continuo.
    if is_dichotomous(x_valid):
        binary, continuous = x_valid, y_valid
    elif is_dichotomous(y_valid):
        binary, continuous = y_valid, x_valid
    else:
        return _base_not_applicable("point_biserial", alpha, "no_dichotomous_variable")
    if continuous.nunique(dropna=True) <= 1:
        return _base_not_applicable("point_biserial", alpha, "constant_values")
    # Codifica la dicotómica a 0/1 conservando el orden de sus dos categorías.
    categories = sorted(binary.unique())
    encoded = binary.map({categories[0]: 0, categories[1]: 1})
    coefficient, p_value = pointbiserialr(encoded.to_numpy(), continuous.to_numpy())
    coefficient = _round(coefficient, decimals)
    p_value = _round(p_value, decimals)
    significance = classify_significance(p_value, alpha)
    return {
        "method_used": "point_biserial",
        "coefficient": coefficient,
        "p_value": p_value,
        "direction": classify_correlation_direction(coefficient),
        "magnitude": classify_correlation_magnitude(coefficient),
        "significance": significance,
        "classification": significance,
        "warnings": [],
        "assumptions": ["dichotomous_continuous_pair", "pairwise_complete_cases", "non_constant_series"],
    }


def run_correlation(
    x: pd.Series,
    y: pd.Series,
    *,
    method: str,
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    selected = method.lower()
    if selected == "pearson":
        return pearson_correlation(x, y, alpha=alpha, decimals=decimals)
    if selected == "spearman":
        return spearman_correlation(x, y, alpha=alpha, decimals=decimals)
    if selected == "kendall":
        return kendall_correlation(x, y, alpha=alpha, decimals=decimals)
    if selected == "point_biserial":
        return point_biserial_correlation(x, y, alpha=alpha, decimals=decimals)
    raise ValueError("Unsupported correlation method")


def build_pair_diagnostics(x: pd.Series, y: pd.Series) -> dict[str, Any]:
    x_valid, y_valid = pairwise_valid_series(x, y)
    valid_n = int(len(x_valid))
    total_n = max(len(x), len(y))
    missing_n = int(total_n - valid_n)
    return {
        "valid_n": valid_n,
        "missing_n": missing_n,
        "pairwise_deletion_used": missing_n > 0,
        "many_ties": detect_many_ties(x_valid) or detect_many_ties(y_valid),
        "outliers_possible": detect_outliers_iqr(x_valid) or detect_outliers_iqr(y_valid),
    }
