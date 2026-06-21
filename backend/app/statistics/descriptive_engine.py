import math

import pandas as pd
from scipy.stats import kurtosis, skew

from app.schemas.descriptive import NumericDescriptiveRead


def _round(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    if math.isnan(value):
        return None
    return round(float(value), decimals)


def safe_mode(series: pd.Series, decimals: int = 3) -> float | None:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.empty:
        return None
    modes = cleaned.mode(dropna=True)
    if modes.empty:
        return None
    return _round(float(modes.iloc[0]), decimals)


def safe_skewness(series: pd.Series, decimals: int = 3) -> float | None:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.size < 3 or cleaned.nunique(dropna=True) < 2:
        return None
    return _round(float(skew(cleaned, bias=False)), decimals)


def safe_kurtosis(series: pd.Series, decimals: int = 3) -> float | None:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.size < 4 or cleaned.nunique(dropna=True) < 2:
        return None
    return _round(float(kurtosis(cleaned, fisher=True, bias=False)), decimals)


def percentile_summary(series: pd.Series, decimals: int = 3) -> tuple[float | None, float | None, float | None]:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if cleaned.empty:
        return None, None, None
    return (
        _round(float(cleaned.quantile(0.25)), decimals),
        _round(float(cleaned.quantile(0.50)), decimals),
        _round(float(cleaned.quantile(0.75)), decimals),
    )


def numeric_descriptive(series: pd.Series, decimals: int = 3) -> NumericDescriptiveRead:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    valid_n = int(valid.size)
    missing_n = int(numeric.size - valid_n)

    if valid_n == 0:
        return NumericDescriptiveRead(
            valid_n=0,
            missing_n=missing_n,
            mean=None,
            median=None,
            mode=None,
            standard_deviation=None,
            variance=None,
            minimum=None,
            maximum=None,
            range=None,
            skewness=None,
            kurtosis=None,
            percentile_25=None,
            percentile_50=None,
            percentile_75=None,
        )

    minimum = float(valid.min())
    maximum = float(valid.max())
    percentile_25, percentile_50, percentile_75 = percentile_summary(valid, decimals)

    return NumericDescriptiveRead(
        valid_n=valid_n,
        missing_n=missing_n,
        mean=_round(float(valid.mean()), decimals),
        median=_round(float(valid.median()), decimals),
        mode=safe_mode(valid, decimals),
        standard_deviation=_round(float(valid.std(ddof=1)), decimals) if valid_n >= 2 else None,
        variance=_round(float(valid.var(ddof=1)), decimals) if valid_n >= 2 else None,
        minimum=_round(minimum, decimals),
        maximum=_round(maximum, decimals),
        range=_round(maximum - minimum, decimals),
        skewness=safe_skewness(valid, decimals),
        kurtosis=safe_kurtosis(valid, decimals),
        percentile_25=percentile_25,
        percentile_50=percentile_50,
        percentile_75=percentile_75,
    )
