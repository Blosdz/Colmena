from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import f_oneway, kruskal, levene, mannwhitneyu, ttest_ind

from app.statistics.descriptive_engine import numeric_descriptive
from app.statistics.normality_engine import detect_outliers_iqr


def _round(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    if np.isnan(value):
        return None
    return round(float(value), decimals)


def classify_significance(p_value: float | None, alpha: float) -> str:
    if p_value is None:
        return "not_applicable"
    return "statistically_significant" if p_value < alpha else "not_statistically_significant"


def classify_effect_size(name: str, value: float | None) -> str:
    if value is None:
        return "not_applicable"
    absolute = abs(float(value))
    if name == "cohens_d":
        if absolute < 0.20:
            return "negligible"
        if absolute < 0.50:
            return "small"
        if absolute < 0.80:
            return "medium"
        return "large"
    if name == "eta_squared":
        if absolute < 0.01:
            return "negligible"
        if absolute < 0.06:
            return "small"
        if absolute < 0.14:
            return "medium"
        return "large"
    if name == "epsilon_squared":
        if absolute < 0.01:
            return "negligible"
        if absolute < 0.06:
            return "small"
        if absolute < 0.14:
            return "medium"
        return "large"
    if name == "rank_biserial":
        if absolute < 0.10:
            return "negligible"
        if absolute < 0.30:
            return "small"
        if absolute < 0.50:
            return "medium"
        return "large"
    return "not_applicable"


def clean_groups(outcome_series: pd.Series, group_series: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "outcome": pd.to_numeric(outcome_series, errors="coerce"),
            "group": group_series,
        }
    )
    frame["group"] = frame["group"].where(frame["group"].notna(), None)
    return frame


def build_group_descriptives(
    groups: dict[str, pd.Series],
    *,
    group_labels: dict[str, str] | None = None,
    total_counts: dict[str, int] | None = None,
    decimals: int = 3,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for group_value, series in groups.items():
        descriptive = numeric_descriptive(series, decimals=decimals)
        total_count = total_counts[group_value] if total_counts is not None and group_value in total_counts else descriptive.valid_n
        items.append(
            {
                "group_label": group_labels[group_value] if group_labels is not None and group_value in group_labels else str(group_value),
                "group_value": group_value,
                "n": descriptive.valid_n,
                "missing_n": max(total_count - descriptive.valid_n, 0),
                "mean": descriptive.mean,
                "median": descriptive.median,
                "standard_deviation": descriptive.standard_deviation,
                "variance": descriptive.variance,
                "minimum": descriptive.minimum,
                "maximum": descriptive.maximum,
                "range": descriptive.range,
                "percentile_25": descriptive.percentile_25,
                "percentile_75": descriptive.percentile_75,
            }
        )
    return items


def detect_outliers_by_group(groups: dict[str, pd.Series]) -> bool:
    return any(detect_outliers_iqr(series) for series in groups.values())


def cohen_d(group_a: pd.Series, group_b: pd.Series, *, decimals: int = 3) -> float | None:
    a = pd.to_numeric(group_a, errors="coerce").dropna()
    b = pd.to_numeric(group_b, errors="coerce").dropna()
    if a.size < 2 or b.size < 2:
        return None
    pooled_df = a.size + b.size - 2
    if pooled_df <= 0:
        return None
    pooled_var = (((a.size - 1) * a.var(ddof=1)) + ((b.size - 1) * b.var(ddof=1))) / pooled_df
    if pooled_var <= 0:
        return None
    value = (a.mean() - b.mean()) / np.sqrt(pooled_var)
    return _round(value, decimals)


def independent_t_test(
    group_a: pd.Series,
    group_b: pd.Series,
    *,
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    a = pd.to_numeric(group_a, errors="coerce").dropna()
    b = pd.to_numeric(group_b, errors="coerce").dropna()
    statistic, p_value = ttest_ind(a.to_numpy(), b.to_numpy(), equal_var=True)
    return {
        "method_used": "t_student_independent",
        "statistic": _round(statistic, decimals),
        "p_value": _round(p_value, decimals),
        "degrees_of_freedom": str(int(a.size + b.size - 2)),
        "classification": classify_significance(_round(p_value, decimals), alpha),
        "effect_size_name": "cohens_d",
        "effect_size_value": cohen_d(a, b, decimals=decimals),
    }


def welch_t_test(
    group_a: pd.Series,
    group_b: pd.Series,
    *,
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    a = pd.to_numeric(group_a, errors="coerce").dropna()
    b = pd.to_numeric(group_b, errors="coerce").dropna()
    statistic, p_value = ttest_ind(a.to_numpy(), b.to_numpy(), equal_var=False)
    var_a = a.var(ddof=1) / a.size if a.size > 1 else 0.0
    var_b = b.var(ddof=1) / b.size if b.size > 1 else 0.0
    denominator = ((var_a**2) / (a.size - 1) if a.size > 1 else 0.0) + ((var_b**2) / (b.size - 1) if b.size > 1 else 0.0)
    if denominator > 0:
        welch_df = ((var_a + var_b) ** 2) / denominator
    else:
        welch_df = None
    return {
        "method_used": "welch_t",
        "statistic": _round(statistic, decimals),
        "p_value": _round(p_value, decimals),
        "degrees_of_freedom": str(_round(welch_df, decimals)) if welch_df is not None else None,
        "classification": classify_significance(_round(p_value, decimals), alpha),
        "effect_size_name": "cohens_d",
        "effect_size_value": cohen_d(a, b, decimals=decimals),
    }


def mann_whitney_u_test(
    group_a: pd.Series,
    group_b: pd.Series,
    *,
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    a = pd.to_numeric(group_a, errors="coerce").dropna()
    b = pd.to_numeric(group_b, errors="coerce").dropna()
    statistic, p_value = mannwhitneyu(a.to_numpy(), b.to_numpy(), alternative="two-sided", method="asymptotic")
    denominator = a.size * b.size
    rank_biserial = None if denominator == 0 else _round(1 - (2 * float(statistic) / denominator), decimals)
    return {
        "method_used": "mann_whitney_u",
        "statistic": _round(statistic, decimals),
        "p_value": _round(p_value, decimals),
        "degrees_of_freedom": None,
        "classification": classify_significance(_round(p_value, decimals), alpha),
        "effect_size_name": "rank_biserial",
        "effect_size_value": rank_biserial,
    }


def eta_squared_anova(groups: dict[str, pd.Series], *, decimals: int = 3) -> float | None:
    cleaned_groups = [pd.to_numeric(series, errors="coerce").dropna() for series in groups.values()]
    valid_groups = [series for series in cleaned_groups if not series.empty]
    if len(valid_groups) < 2:
        return None
    combined = pd.concat(valid_groups, ignore_index=True)
    if combined.empty:
        return None
    grand_mean = combined.mean()
    ss_between = sum(series.size * ((series.mean() - grand_mean) ** 2) for series in valid_groups)
    ss_total = float(((combined - grand_mean) ** 2).sum())
    if ss_total <= 0:
        return None
    return _round(ss_between / ss_total, decimals)


def one_way_anova(
    groups: dict[str, pd.Series],
    *,
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    cleaned_groups = [pd.to_numeric(series, errors="coerce").dropna() for series in groups.values()]
    statistic, p_value = f_oneway(*[series.to_numpy() for series in cleaned_groups])
    total_n = sum(series.size for series in cleaned_groups)
    k = len(cleaned_groups)
    return {
        "method_used": "anova_one_way",
        "statistic": _round(statistic, decimals),
        "p_value": _round(p_value, decimals),
        "degrees_of_freedom": f"{k - 1}, {total_n - k}",
        "classification": classify_significance(_round(p_value, decimals), alpha),
        "effect_size_name": "eta_squared",
        "effect_size_value": eta_squared_anova(groups, decimals=decimals),
    }


def epsilon_squared_kruskal(statistic: float, n: int, k: int, *, decimals: int = 3) -> float | None:
    if n <= k:
        return None
    value = (float(statistic) - k + 1) / (n - k)
    return _round(max(value, 0.0), decimals)


def kruskal_wallis_test(
    groups: dict[str, pd.Series],
    *,
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    cleaned_groups = [pd.to_numeric(series, errors="coerce").dropna() for series in groups.values()]
    statistic, p_value = kruskal(*[series.to_numpy() for series in cleaned_groups])
    total_n = sum(series.size for series in cleaned_groups)
    k = len(cleaned_groups)
    return {
        "method_used": "kruskal_wallis",
        "statistic": _round(statistic, decimals),
        "p_value": _round(p_value, decimals),
        "degrees_of_freedom": str(k - 1),
        "classification": classify_significance(_round(p_value, decimals), alpha),
        "effect_size_name": "epsilon_squared",
        "effect_size_value": epsilon_squared_kruskal(float(statistic), total_n, k, decimals=decimals),
    }


def levene_variance_test(
    groups: dict[str, pd.Series],
    *,
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    cleaned_groups = [pd.to_numeric(series, errors="coerce").dropna() for series in groups.values()]
    if len(cleaned_groups) < 2 or any(series.size < 2 for series in cleaned_groups):
        return {
            "method": "levene",
            "statistic": None,
            "p_value": None,
            "alpha": alpha,
            "classification": "not_applicable",
            "warnings": ["insufficient_n"],
        }
    statistic, p_value = levene(*[series.to_numpy() for series in cleaned_groups], center="median")
    rounded_p = _round(p_value, decimals)
    classification = "homogeneous" if rounded_p is not None and rounded_p >= alpha else "non_homogeneous"
    return {
        "method": "levene",
        "statistic": _round(statistic, decimals),
        "p_value": rounded_p,
        "alpha": alpha,
        "classification": classification,
        "warnings": [],
    }
