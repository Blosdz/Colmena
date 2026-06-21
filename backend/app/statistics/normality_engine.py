from typing import Any

import pandas as pd
from scipy.stats import normaltest, shapiro
from statsmodels.stats.diagnostic import lilliefors

from app.statistics.descriptive_engine import numeric_descriptive


def round_nullable(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    return round(float(value), decimals)


def detect_outliers_iqr(series: pd.Series) -> bool:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.size < 4:
        return False
    q1 = cleaned.quantile(0.25)
    q3 = cleaned.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return False
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return bool(((cleaned < lower) | (cleaned > upper)).any())


def build_normality_interpretation(classification: str, p_value: float | None, alpha: float) -> str:
    if classification == "normal":
        return (
            "La prueba aplicada no evidenció una desviación estadísticamente significativa respecto de la normalidad, "
            f"dado que el valor p ({p_value}) fue mayor o igual al nivel de significancia establecido ({alpha}). "
            "Por ello, la distribución puede tratarse como compatible con normalidad para decisiones analíticas iniciales."
        )
    if classification == "non_normal":
        return (
            "La prueba aplicada evidenció una desviación estadísticamente significativa respecto de la normalidad, "
            f"dado que el valor p ({p_value}) fue menor al nivel de significancia establecido ({alpha}). "
            "En consecuencia, se recomienda considerar procedimientos no paramétricos o revisar la distribución antes de aplicar pruebas paramétricas."
        )
    if classification == "not_applicable":
        return (
            "No se aplicó una prueba de normalidad porque la variable no cuenta con datos numéricos suficientes o no corresponde a una escala donde la normalidad sea pertinente."
        )
    return (
        "No fue posible establecer una clasificación confiable de normalidad con los datos disponibles. "
        "Se recomienda revisar el tamaño muestral, valores constantes, datos faltantes o el tipo de variable."
    )


def evaluate_numeric_normality(
    series: pd.Series,
    *,
    total_n: int,
    method: str = "auto",
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    valid_n = int(valid.size)
    missing_n = int(total_n - valid_n)
    missing_percent = round((missing_n / total_n) * 100, decimals) if total_n else 0.0
    descriptive = numeric_descriptive(numeric, decimals=decimals)
    warnings: list[str] = []

    if valid_n == 0:
        warnings.extend(["all_values_missing", "non_numeric"])
        classification = "not_applicable"
        return {
            "method": "not_applicable",
            "statistic": None,
            "p_value": None,
            "alpha": alpha,
            "valid_n": valid_n,
            "missing_n": missing_n,
            "missing_percent": missing_percent,
            "classification": classification,
            "warnings": warnings,
            "descriptive_context": descriptive,
            "interpretation": build_normality_interpretation(classification, None, alpha),
        }

    if valid_n < 3:
        warnings.append("insufficient_n")
        classification = "not_applicable"
        return {
            "method": "not_applicable",
            "statistic": None,
            "p_value": None,
            "alpha": alpha,
            "valid_n": valid_n,
            "missing_n": missing_n,
            "missing_percent": missing_percent,
            "classification": classification,
            "warnings": warnings,
            "descriptive_context": descriptive,
            "interpretation": build_normality_interpretation(classification, None, alpha),
        }

    if valid.nunique(dropna=True) <= 1:
        warnings.append("constant_values")
        classification = "not_applicable"
        return {
            "method": "not_applicable",
            "statistic": None,
            "p_value": None,
            "alpha": alpha,
            "valid_n": valid_n,
            "missing_n": missing_n,
            "missing_percent": missing_percent,
            "classification": classification,
            "warnings": warnings,
            "descriptive_context": descriptive,
            "interpretation": build_normality_interpretation(classification, None, alpha),
        }

    if missing_percent >= 20:
        warnings.append("high_missingness")
    if valid_n < 30:
        warnings.append("small_sample_low_power")
    if valid_n > 300:
        warnings.append("large_sample_sensitive")
    if descriptive.skewness is not None and abs(descriptive.skewness) >= 1:
        warnings.append("skewness_high")
    if descriptive.kurtosis is not None and abs(descriptive.kurtosis) >= 1:
        warnings.append("kurtosis_high")
    if detect_outliers_iqr(valid):
        warnings.append("outliers_possible")

    requested_method = method.lower()
    chosen_method = requested_method
    statistic: float | None = None
    p_value: float | None = None

    def _choose_auto() -> str:
        if valid_n < 3:
            return "not_applicable"
        if valid_n <= 5000:
            return "shapiro"
        return "lilliefors"

    if requested_method == "auto":
        chosen_method = _choose_auto()

    try:
        if chosen_method == "shapiro":
            if valid_n > 5000:
                warnings.append("method_fallback")
                chosen_method = "lilliefors" if requested_method == "auto" or requested_method == "shapiro" else chosen_method
            if chosen_method == "shapiro":
                statistic, p_value = shapiro(valid.to_numpy())
        if chosen_method == "lilliefors":
            statistic, p_value = lilliefors(valid.to_numpy())
        if chosen_method == "dagostino":
            if valid_n < 8:
                warnings.append("method_fallback")
                if requested_method == "auto":
                    chosen_method = "shapiro"
                    statistic, p_value = shapiro(valid.to_numpy())
                else:
                    chosen_method = "inconclusive"
            else:
                statistic, p_value = normaltest(valid.to_numpy())
        if chosen_method == "inconclusive":
            raise ValueError("No applicable method")
    except Exception:
        if chosen_method != "dagostino" and valid_n >= 8:
            try:
                statistic, p_value = normaltest(valid.to_numpy())
                chosen_method = "dagostino"
                warnings.append("method_fallback")
            except Exception:
                statistic = None
                p_value = None
        else:
            statistic = None
            p_value = None

    if statistic is None or p_value is None:
        classification = "inconclusive"
    else:
        classification = "normal" if p_value >= alpha else "non_normal"

    return {
        "method": chosen_method,
        "statistic": round_nullable(statistic, decimals),
        "p_value": round_nullable(p_value, decimals),
        "alpha": alpha,
        "valid_n": valid_n,
        "missing_n": missing_n,
        "missing_percent": missing_percent,
        "classification": classification,
        "warnings": list(dict.fromkeys(warnings)),
        "descriptive_context": descriptive,
        "interpretation": build_normality_interpretation(classification, round_nullable(p_value, decimals), alpha),
    }
