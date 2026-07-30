from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm


def _round(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    return round(float(value), decimals)


def _base_not_applicable(reason: str) -> dict[str, Any]:
    return {
        "valid_n": 0,
        "r_squared": None,
        "adjusted_r_squared": None,
        "f_statistic": None,
        "f_p_value": None,
        "intercept": None,
        "coefficients": [],
        "warnings": [reason],
    }


def linear_regression(
    dependent: pd.Series,
    independents: dict[str, pd.Series],
    *,
    alpha: float = 0.05,
    decimals: int = 3,
) -> dict[str, Any]:
    """Regresion lineal (simple si hay un predictor, multiple si hay varios).

    Recibe series ya construidas por el llamador (puntajes por dimension o
    variable, no respuestas crudas) y nunca vuelve a consultar la base de
    datos: sigue el mismo patron que correlation_engine.run_correlation.
    """
    if not independents:
        return _base_not_applicable("no_independent_variables")

    frame = pd.DataFrame({"__dependent__": pd.to_numeric(dependent, errors="coerce")})
    for name, series in independents.items():
        frame[name] = pd.to_numeric(series, errors="coerce")
    frame = frame.dropna()

    predictor_names = list(independents.keys())
    valid_n = int(len(frame))
    min_required = len(predictor_names) + 2
    if valid_n < min_required:
        return _base_not_applicable("insufficient_n")
    if frame["__dependent__"].nunique(dropna=True) <= 1:
        return _base_not_applicable("constant_dependent")
    for name in predictor_names:
        if frame[name].nunique(dropna=True) <= 1:
            return _base_not_applicable(f"constant_independent:{name}")

    y = frame["__dependent__"]
    x = sm.add_constant(frame[predictor_names], has_constant="add")
    model = sm.OLS(y, x).fit()

    conf_int = model.conf_int(alpha=alpha)
    coefficients: list[dict[str, Any]] = []
    for name in predictor_names:
        coefficients.append(
            {
                "name": name,
                "coefficient": _round(model.params.get(name), decimals),
                "standard_error": _round(model.bse.get(name), decimals),
                "t_value": _round(model.tvalues.get(name), decimals),
                "p_value": _round(model.pvalues.get(name), decimals),
                "significant": bool(model.pvalues.get(name) is not None and model.pvalues.get(name) < alpha),
                "ci_lower": _round(conf_int.loc[name, 0], decimals) if name in conf_int.index else None,
                "ci_upper": _round(conf_int.loc[name, 1], decimals) if name in conf_int.index else None,
            }
        )

    return {
        "valid_n": valid_n,
        "r_squared": _round(model.rsquared, decimals),
        "adjusted_r_squared": _round(model.rsquared_adj, decimals),
        "f_statistic": _round(model.fvalue, decimals),
        "f_p_value": _round(model.f_pvalue, decimals),
        "intercept": _round(model.params.get("const"), decimals),
        "coefficients": coefficients,
        "warnings": [],
    }
