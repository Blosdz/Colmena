import math

import numpy as np
import pandas as pd

from app.schemas.reliability import CronbachAlphaRead, ItemReliabilityRead


def _round(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return round(float(value), decimals)


def _classify_alpha(alpha: float | None) -> str:
    """Escala de George & Mallery, ampliamente citada en tesis."""
    if alpha is None:
        return "not_applicable"
    if alpha >= 0.9:
        return "excelente"
    if alpha >= 0.8:
        return "bueno"
    if alpha >= 0.7:
        return "aceptable"
    if alpha >= 0.6:
        return "cuestionable"
    if alpha >= 0.5:
        return "pobre"
    return "inaceptable"


def build_reliability_interpretation(classification: str, alpha: float | None, n_items: int) -> str:
    if classification == "not_applicable":
        return (
            "No fue posible calcular el coeficiente alfa de Cronbach con los datos disponibles. "
            "Se requieren al menos dos ítems y dos casos válidos con varianza no nula. "
            "Revise el número de ítems puntuables, los datos faltantes o los valores constantes."
        )
    prose = {
        "excelente": "indica una confiabilidad excelente",
        "bueno": "indica una buena confiabilidad",
        "aceptable": "indica una confiabilidad aceptable",
        "cuestionable": "indica una confiabilidad cuestionable",
        "pobre": "indica una confiabilidad pobre",
        "inaceptable": "indica una confiabilidad inaceptable",
    }[classification]
    detail = (
        f"El coeficiente alfa de Cronbach obtenido ({alpha}) sobre {n_items} ítems {prose} de la "
        "consistencia interna del instrumento."
    )
    if classification in {"cuestionable", "pobre", "inaceptable"}:
        detail += (
            " Se recomienda revisar los ítems con baja correlación ítem-total corregida, verificar la "
            "codificación inversa y considerar la depuración o reformulación de los reactivos."
        )
    return detail


def cronbach_alpha(
    dataframe: pd.DataFrame,
    item_columns: dict[str, str],
    *,
    item_labels: dict[str, str] | None = None,
    decimals: int = 3,
) -> CronbachAlphaRead:
    """Calcula el alfa de Cronbach para un conjunto de ítems.

    ``item_columns`` mapea ``item_id`` -> nombre de columna en ``dataframe`` (misma
    convención que ``build_score_matrix``). Aplica eliminación por lista (listwise):
    solo se usan los casos que respondieron todos los ítems, que es el criterio
    estándar para el cálculo del coeficiente.
    """
    item_labels = item_labels or {}
    warnings: list[str] = []

    ordered_ids = [item_id for item_id in item_columns if item_columns[item_id] in dataframe.columns]
    columns = [item_columns[item_id] for item_id in ordered_ids]

    def _empty(classification: str, extra_warnings: list[str]) -> CronbachAlphaRead:
        return CronbachAlphaRead(
            alpha=None,
            standardized_alpha=None,
            n_items=len(ordered_ids),
            n_valid_cases=0,
            n_excluded_cases=0,
            average_inter_item_correlation=None,
            sum_item_variances=None,
            total_variance=None,
            classification=classification,
            interpretation=build_reliability_interpretation(classification, None, len(ordered_ids)),
            items=[],
            warnings=list(dict.fromkeys(extra_warnings)),
        )

    if len(ordered_ids) < 2:
        return _empty("not_applicable", ["insufficient_items"])

    numeric = dataframe[columns].apply(pd.to_numeric, errors="coerce")
    numeric.columns = ordered_ids
    total_rows = int(numeric.shape[0])
    complete = numeric.dropna(axis=0, how="any")
    n_valid = int(complete.shape[0])
    n_excluded = total_rows - n_valid

    if n_valid < 2:
        return _empty("not_applicable", ["insufficient_cases"])

    item_variances = complete.var(ddof=1)
    total_scores = complete.sum(axis=1)
    total_variance = float(total_scores.var(ddof=1))
    sum_item_variances = float(item_variances.sum())

    constant_items = [item_id for item_id in ordered_ids if float(item_variances[item_id]) == 0.0]
    if constant_items:
        warnings.append("constant_item")

    k = len(ordered_ids)
    if total_variance == 0.0:
        return _empty("not_applicable", ["zero_total_variance"])

    alpha = (k / (k - 1)) * (1.0 - sum_item_variances / total_variance)

    correlation_matrix = complete.corr(method="pearson").to_numpy()
    off_diagonal_mask = ~np.eye(k, dtype=bool)
    inter_item_values = correlation_matrix[off_diagonal_mask]
    inter_item_values = inter_item_values[~np.isnan(inter_item_values)]
    average_inter_item = float(inter_item_values.mean()) if inter_item_values.size else None

    standardized_alpha: float | None = None
    if average_inter_item is not None and not math.isnan(average_inter_item):
        denominator = 1.0 + (k - 1) * average_inter_item
        if denominator != 0.0:
            standardized_alpha = (k * average_inter_item) / denominator

    items: list[ItemReliabilityRead] = []
    for item_id in ordered_ids:
        rest = [other for other in ordered_ids if other != item_id]
        rest_total = complete[rest].sum(axis=1)
        item_series = complete[item_id]
        if float(item_variances[item_id]) == 0.0 or float(rest_total.var(ddof=1)) == 0.0:
            item_total_correlation = None
        else:
            item_total_correlation = float(item_series.corr(rest_total))

        alpha_if_deleted: float | None = None
        if len(rest) >= 2:
            rest_item_var = float(item_variances[rest].sum())
            rest_total_var = float(rest_total.var(ddof=1))
            if rest_total_var != 0.0:
                alpha_if_deleted = (len(rest) / (len(rest) - 1)) * (1.0 - rest_item_var / rest_total_var)

        items.append(
            ItemReliabilityRead(
                item_id=item_id,
                label=item_labels.get(item_id),
                valid_n=n_valid,
                mean=_round(float(item_series.mean()), decimals),
                variance=_round(float(item_variances[item_id]), decimals),
                item_total_correlation=_round(item_total_correlation, decimals),
                alpha_if_deleted=_round(alpha_if_deleted, decimals),
            )
        )

    if alpha < 0:
        warnings.append("negative_alpha")
    if n_valid < 30:
        warnings.append("small_sample")
    if alpha < 0.7:
        warnings.append("low_reliability")
    if n_excluded > 0:
        warnings.append("listwise_excluded_cases")

    classification = _classify_alpha(alpha)
    rounded_alpha = _round(alpha, decimals)

    return CronbachAlphaRead(
        alpha=rounded_alpha,
        standardized_alpha=_round(standardized_alpha, decimals),
        n_items=k,
        n_valid_cases=n_valid,
        n_excluded_cases=n_excluded,
        average_inter_item_correlation=_round(average_inter_item, decimals),
        sum_item_variances=_round(sum_item_variances, decimals),
        total_variance=_round(total_variance, decimals),
        classification=classification,
        interpretation=build_reliability_interpretation(classification, rounded_alpha, k),
        items=items,
        warnings=list(dict.fromkeys(warnings)),
    )
