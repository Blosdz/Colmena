from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact


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


def build_contingency_table(row_series: pd.Series, column_series: pd.Series) -> pd.DataFrame:
    filtered = pd.DataFrame({"row": row_series, "column": column_series}).dropna(subset=["row", "column"], how="any")
    if filtered.empty:
        return pd.DataFrame()
    filtered["row"] = filtered["row"].astype(str)
    filtered["column"] = filtered["column"].astype(str)
    return pd.crosstab(filtered["row"], filtered["column"], dropna=False)


def clean_categorical_pair(row_series: pd.Series, column_series: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame({"row": row_series, "column": column_series})
    frame["row"] = frame["row"].where(frame["row"].notna(), None)
    frame["column"] = frame["column"].where(frame["column"].notna(), None)
    return frame


def table_percentages(contingency_table: pd.DataFrame, *, decimals: int = 3) -> list[dict[str, Any]]:
    total_n = int(contingency_table.to_numpy().sum())
    if total_n == 0:
        return []
    cells: list[dict[str, Any]] = []
    for row_label in contingency_table.index.tolist():
        row_total = int(contingency_table.loc[row_label].sum())
        for column_label in contingency_table.columns.tolist():
            column_total = int(contingency_table[column_label].sum())
            observed = int(contingency_table.loc[row_label, column_label])
            cells.append(
                {
                    "row_value": str(row_label),
                    "column_value": str(column_label),
                    "observed": observed,
                    "total_percent": _round((observed / total_n) * 100 if total_n else 0.0, decimals),
                    "row_percent": _round((observed / row_total) * 100 if row_total else 0.0, decimals),
                    "column_percent": _round((observed / column_total) * 100 if column_total else 0.0, decimals),
                }
            )
    return cells


def detect_sparse_table(contingency_table: pd.DataFrame) -> bool:
    if contingency_table.empty:
        return False
    zero_cells = int((contingency_table == 0).sum().sum())
    total_cells = int(contingency_table.shape[0] * contingency_table.shape[1])
    return total_cells > 0 and (zero_cells / total_cells) >= 0.5


def expected_count_warnings(expected_table: np.ndarray) -> list[str]:
    warnings: list[str] = []
    if expected_table.size == 0:
        return warnings
    low_mask = expected_table < 5
    if low_mask.any():
        warnings.append("expected_counts_low")
        if (low_mask.sum() / expected_table.size) > 0.20:
            warnings.append("chi_square_assumption_risk")
    return warnings


def phi_coefficient(chi2: float, n: int, *, decimals: int = 3) -> float | None:
    if n <= 0:
        return None
    return _round(np.sqrt(float(chi2) / n), decimals)


def cramers_v(chi2: float, n: int, rows: int, columns: int, *, decimals: int = 3) -> float | None:
    denominator = n * min(rows - 1, columns - 1)
    if denominator <= 0:
        return None
    return _round(np.sqrt(float(chi2) / denominator), decimals)


def classify_phi(value: float | None) -> str:
    if value is None:
        return "not_applicable"
    absolute = abs(float(value))
    if absolute < 0.10:
        return "negligible"
    if absolute < 0.30:
        return "small"
    if absolute < 0.50:
        return "medium"
    return "large"


def classify_cramers_v(value: float | None) -> str:
    if value is None:
        return "not_applicable"
    absolute = abs(float(value))
    if absolute < 0.10:
        return "negligible"
    if absolute < 0.30:
        return "weak"
    if absolute < 0.50:
        return "moderate"
    return "strong"


def chi_square_test(contingency_table: pd.DataFrame, *, alpha: float = 0.05, decimals: int = 3) -> dict[str, Any]:
    if contingency_table.empty:
        return {
            "method_used": "chi_square",
            "statistic": None,
            "p_value": None,
            "degrees_of_freedom": None,
            "expected": None,
            "classification": "not_applicable",
            "warnings": ["insufficient_n"],
        }
    statistic, p_value, dof, expected = chi2_contingency(contingency_table.to_numpy(), correction=False)
    warnings = expected_count_warnings(expected)
    return {
        "method_used": "chi_square",
        "statistic": _round(statistic, decimals),
        "p_value": _round(p_value, decimals),
        "degrees_of_freedom": int(dof),
        "expected": expected,
        "classification": classify_significance(_round(p_value, decimals), alpha),
        "warnings": warnings,
    }


def fisher_exact_test(contingency_table: pd.DataFrame, *, alpha: float = 0.05, decimals: int = 3) -> dict[str, Any]:
    if contingency_table.shape != (2, 2):
        return {
            "method_used": "fisher_exact",
            "odds_ratio": None,
            "p_value": None,
            "classification": "not_applicable",
            "warnings": ["fisher_only_for_2x2"],
        }
    odds_ratio, p_value = fisher_exact(contingency_table.to_numpy(), alternative="two-sided")
    return {
        "method_used": "fisher_exact",
        "odds_ratio": _round(odds_ratio, decimals),
        "p_value": _round(p_value, decimals),
        "classification": classify_significance(_round(p_value, decimals), alpha),
        "warnings": [],
    }
