import math
import warnings as warnings_module

import numpy as np
import pandas as pd

from app.schemas.reliability import CompositeReliabilityRead, ItemLoadingRead


def _round(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return round(float(value), decimals)


def _classify_composite(composite_reliability: float | None, ave: float | None) -> str:
    if composite_reliability is None or ave is None:
        return "not_applicable"
    if composite_reliability >= 0.7 and ave >= 0.5:
        return "adecuada"
    if composite_reliability >= 0.7:
        return "fiabilidad_adecuada_validez_insuficiente"
    if ave >= 0.5:
        return "validez_adecuada_fiabilidad_insuficiente"
    return "insuficiente"


def build_composite_interpretation(classification: str, cr: float | None, ave: float | None, n_items: int) -> str:
    if classification == "not_applicable":
        return (
            "No fue posible ajustar un modelo de un factor (analisis factorial confirmatorio) con los datos "
            "disponibles. Se requieren al menos tres items puntuables y suficientes casos validos con varianza "
            "no nula, y el modelo debe converger numericamente."
        )
    prose = {
        "adecuada": "indican fiabilidad compuesta y validez convergente adecuadas",
        "fiabilidad_adecuada_validez_insuficiente": (
            "indican fiabilidad compuesta adecuada, pero la varianza media extraida (AVE) es insuficiente "
            "para sostener validez convergente"
        ),
        "validez_adecuada_fiabilidad_insuficiente": (
            "indican varianza media extraida (AVE) adecuada, pero la fiabilidad compuesta es insuficiente"
        ),
        "insuficiente": "indican fiabilidad compuesta y validez convergente insuficientes",
    }[classification]
    detail = (
        f"Los resultados del analisis factorial confirmatorio de un factor sobre {n_items} items "
        f"(CR = {cr}, AVE = {ave}) {prose}."
    )
    if classification != "adecuada":
        detail += (
            " Se recomienda revisar los items con cargas factoriales bajas y considerar su depuracion o "
            "reformulacion."
        )
    return detail


def single_factor_cfa(
    dataframe: pd.DataFrame,
    item_columns: dict[str, str],
    *,
    item_labels: dict[str, str] | None = None,
    decimals: int = 3,
) -> CompositeReliabilityRead:
    """Ajusta un modelo CFA de un factor sobre los items dados y deriva CR/AVE.

    Todos los items se especifican cargando sobre un unico factor latente. Los datos
    se estandarizan (media 0, varianza 1) antes de ajustar el modelo para que las
    cargas resultantes sean cargas estandarizadas, requisito de las formulas de
    Fiabilidad Compuesta (CR) y Varianza Media Extraida (AVE).
    """
    item_labels = item_labels or {}

    ordered_ids = [item_id for item_id in item_columns if item_columns[item_id] in dataframe.columns]
    columns = [item_columns[item_id] for item_id in ordered_ids]

    def _empty(warning_list: list[str]) -> CompositeReliabilityRead:
        return CompositeReliabilityRead(
            composite_reliability=None,
            ave=None,
            n_items=len(ordered_ids),
            n_valid_cases=0,
            convergence=False,
            classification="not_applicable",
            interpretation=build_composite_interpretation("not_applicable", None, None, len(ordered_ids)),
            items=[],
            warnings=list(dict.fromkeys(warning_list)),
        )

    if len(ordered_ids) < 3:
        return _empty(["insufficient_items"])

    numeric = dataframe[columns].apply(pd.to_numeric, errors="coerce")
    numeric.columns = ordered_ids
    complete = numeric.dropna(axis=0, how="any")
    n_valid = int(complete.shape[0])

    if n_valid < len(ordered_ids) + 2:
        return _empty(["insufficient_cases"])

    std = complete.std(ddof=0)
    constant_items = [item_id for item_id in ordered_ids if float(std[item_id]) == 0.0]
    if constant_items:
        return _empty(["constant_item"])

    standardized = (complete - complete.mean()) / std

    try:
        from factor_analyzer.confirmatory_factor_analyzer import ConfirmatoryFactorAnalyzer, ModelSpecification

        k = len(ordered_ids)
        # Construida a mano (en vez de ModelSpecificationParser) porque la version
        # instalada de factor_analyzer genera la matriz de cargas via pandas .values,
        # que con pandas >=2 (copy-on-write) devuelve un arreglo de solo lectura y
        # rompe la libreria internamente.
        loadings_spec = np.ones((k, 1), dtype=float)
        spec = ModelSpecification(
            loadings=loadings_spec,
            n_factors=1,
            n_variables=k,
            factor_names=["F1"],
            variable_names=ordered_ids,
        )
        with warnings_module.catch_warnings():
            warnings_module.simplefilter("ignore")
            cfa = ConfirmatoryFactorAnalyzer(spec, disp=False)
            cfa.fit(standardized.to_numpy())
        loadings = cfa.loadings_.flatten()
        error_vars = cfa.error_vars_.flatten()
    except Exception:
        return _empty(["cfa_did_not_converge"])

    if not np.all(np.isfinite(loadings)) or not np.all(np.isfinite(error_vars)):
        return _empty(["cfa_did_not_converge"])

    warnings: list[str] = []
    negative_loadings = [ordered_ids[i] for i, value in enumerate(loadings) if value < 0]
    if negative_loadings:
        warnings.append("negative_loading")

    sum_loadings = float(loadings.sum())
    sum_error_vars = float(np.clip(1.0 - loadings**2, a_min=0.0, a_max=None).sum())
    composite_reliability = (sum_loadings**2) / ((sum_loadings**2) + sum_error_vars) if sum_loadings else None
    ave = float((loadings**2).sum() / len(loadings))

    if n_valid < 30:
        warnings.append("small_sample")
    if composite_reliability is not None and composite_reliability < 0.7:
        warnings.append("low_composite_reliability")
    if ave < 0.5:
        warnings.append("low_ave")

    items: list[ItemLoadingRead] = []
    for item_id, loading, error_var in zip(ordered_ids, loadings, error_vars):
        items.append(
            ItemLoadingRead(
                item_id=item_id,
                label=item_labels.get(item_id),
                standardized_loading=_round(float(loading), decimals),
                error_variance=_round(float(error_var), decimals),
            )
        )

    rounded_cr = _round(composite_reliability, decimals)
    rounded_ave = _round(ave, decimals)
    classification = _classify_composite(composite_reliability, ave)

    return CompositeReliabilityRead(
        composite_reliability=rounded_cr,
        ave=rounded_ave,
        n_items=len(ordered_ids),
        n_valid_cases=n_valid,
        convergence=True,
        classification=classification,
        interpretation=build_composite_interpretation(classification, rounded_cr, rounded_ave, len(ordered_ids)),
        items=items,
        warnings=list(dict.fromkeys(warnings)),
    )
