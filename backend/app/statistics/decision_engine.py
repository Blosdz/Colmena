from typing import Any


def recommend_correlation(
    *,
    all_normal: bool,
    has_ordinal: bool,
    min_valid_n: int,
    has_dichotomous_continuous: bool = False,
    many_ties: bool = False,
) -> dict[str, Any]:
    if has_dichotomous_continuous:
        return {
            "recommended_test": "point_biserial",
            "alternative_tests": ["spearman"],
            "route": "parametric",
            "confidence": "medium",
            "assumptions_failed": [],
            "warnings": ["dichotomous_continuous_pair"] if min_valid_n >= 3 else ["dichotomous_continuous_pair", "small_sample_low_power"],
            "explanation": "Se recomienda la correlación punto-biserial porque una variable es dicotómica y la otra es cuantitativa continua.",
        }
    if has_ordinal:
        if many_ties and min_valid_n < 30:
            return {
                "recommended_test": "kendall",
                "alternative_tests": ["spearman"],
                "route": "non_parametric",
                "confidence": "medium",
                "assumptions_failed": ["ordinal_scale"],
                "warnings": ["ordinal_data_present", "many_ties", "small_sample_low_power"],
                "explanation": "Se recomienda Tau de Kendall porque al menos una variable es ordinal, presenta un número elevado de empates y el tamaño muestral es reducido (n < 30), condiciones ante las cuales resulta más robusta que Spearman.",
            }
        return {
            "recommended_test": "spearman",
            "alternative_tests": ["pearson"],
            "route": "non_parametric",
            "confidence": "medium",
            "assumptions_failed": ["ordinal_scale"],
            "warnings": ["ordinal_data_present"] if min_valid_n >= 3 else ["ordinal_data_present", "small_sample_low_power"],
            "explanation": "Se recomienda Spearman porque al menos una de las variables corresponde a una escala ordinal o puntuación tipo Likert, por lo que una ruta no paramétrica es más prudente en esta fase.",
        }
    if all_normal and min_valid_n >= 30:
        return {
            "recommended_test": "pearson",
            "alternative_tests": ["spearman"],
            "route": "parametric",
            "confidence": "high",
            "assumptions_failed": [],
            "warnings": [],
            "explanation": "Se recomienda Pearson porque ambas variables son numéricas y sus distribuciones resultaron compatibles con normalidad para una decisión analítica inicial.",
        }
    return {
        "recommended_test": "spearman",
        "alternative_tests": ["pearson"],
        "route": "non_parametric",
        "confidence": "medium" if min_valid_n >= 10 else "low",
        "assumptions_failed": [] if not all_normal else ["small_sample_low_power"],
        "warnings": ["small_sample_low_power"] if min_valid_n < 30 else [],
        "explanation": "Se recomienda Spearman porque al menos una variable no presentó una distribución compatible con normalidad o el tamaño muestral todavía sugiere cautela para una ruta paramétrica.",
    }


def recommend_independent_groups(
    *,
    group_count: int,
    outcome_normal: bool,
    min_group_n: int,
    categorical_outcome: bool,
) -> dict[str, Any]:
    if categorical_outcome:
        return {
            "recommended_test": "chi_square",
            "alternative_tests": ["fisher_exact_future"],
            "route": "categorical",
            "confidence": "medium",
            "assumptions_failed": [],
            "warnings": [],
            "explanation": "El resultado es categórico, por lo que la ruta inicial más consistente es una prueba de asociación entre variables categóricas.",
        }
    if group_count <= 1:
        return {
            "recommended_test": "descriptive_only",
            "alternative_tests": [],
            "route": "descriptive",
            "confidence": "low",
            "assumptions_failed": ["insufficient_groups"],
            "warnings": ["insufficient_groups"],
            "explanation": "No hay suficientes grupos independientes para recomendar una prueba de comparación.",
        }
    if group_count == 2:
        if outcome_normal and min_group_n >= 15:
            return {
                "recommended_test": "t_student_independent",
                "alternative_tests": ["mann_whitney_u"],
                "route": "parametric",
                "confidence": "medium",
                "assumptions_failed": [],
                "warnings": [],
                "explanation": "Se recomienda t de Student para grupos independientes como ruta inicial porque el outcome es numérico y la distribución resulta compatible con normalidad en los grupos observados.",
            }
        return {
            "recommended_test": "mann_whitney_u",
            "alternative_tests": ["t_student_independent"],
            "route": "non_parametric",
            "confidence": "medium" if min_group_n >= 10 else "low",
            "assumptions_failed": [] if not outcome_normal else ["small_sample_low_power"],
            "warnings": ["small_sample_low_power"] if min_group_n < 15 else [],
            "explanation": "Se recomienda U de Mann-Whitney porque la normalidad no es suficientemente convincente o el tamaño de grupo todavía es reducido para una ruta paramétrica.",
        }
    if outcome_normal and min_group_n >= 15:
        return {
            "recommended_test": "anova",
            "alternative_tests": ["kruskal_wallis"],
            "route": "parametric",
            "confidence": "medium",
            "assumptions_failed": [],
            "warnings": [],
            "explanation": "Se recomienda ANOVA como ruta inicial porque el outcome es numérico, existen más de dos grupos y la distribución observada es compatible con normalidad para una evaluación preliminar.",
        }
    return {
        "recommended_test": "kruskal_wallis",
        "alternative_tests": ["anova"],
        "route": "non_parametric",
        "confidence": "medium" if min_group_n >= 10 else "low",
        "assumptions_failed": [] if not outcome_normal else ["small_sample_low_power"],
        "warnings": ["small_sample_low_power"] if min_group_n < 15 else [],
        "explanation": "Se recomienda Kruskal-Wallis porque hay más de dos grupos y la información disponible no favorece una ruta paramétrica robusta.",
    }


def recommend_related_groups(
    *,
    both_normal: bool,
    min_valid_n: int,
) -> dict[str, Any]:
    if both_normal and min_valid_n >= 15:
        return {
            "recommended_test": "t_student_paired",
            "alternative_tests": ["wilcoxon"],
            "route": "parametric",
            "confidence": "medium",
            "assumptions_failed": [],
            "warnings": [],
            "explanation": "Se recomienda t de Student para muestras relacionadas como ruta inicial, sujeto a confirmar la distribución de las diferencias en una fase posterior.",
        }
    return {
        "recommended_test": "wilcoxon",
        "alternative_tests": ["t_student_paired"],
        "route": "non_parametric",
        "confidence": "medium" if min_valid_n >= 10 else "low",
        "assumptions_failed": [] if not both_normal else ["small_sample_low_power"],
        "warnings": ["small_sample_low_power"] if min_valid_n < 15 else [],
        "explanation": "Se recomienda Wilcoxon como decisión inicial prudente porque todavía no se cuenta con evidencia suficiente para sostener una ruta paramétrica en mediciones relacionadas.",
    }


def recommend_association_categorical() -> dict[str, Any]:
    return {
        "recommended_test": "chi_square",
        "alternative_tests": ["fisher_exact_future"],
        "route": "categorical",
        "confidence": "medium",
        "assumptions_failed": [],
        "warnings": [],
        "explanation": "Se recomienda chi cuadrado como ruta inicial porque ambas variables son categóricas. La prueba no se ejecuta en esta fase; solo se orienta el procedimiento futuro.",
    }


def recommend_descriptive_only(reason: str) -> dict[str, Any]:
    return {
        "recommended_test": "descriptive_only",
        "alternative_tests": [],
        "route": "descriptive",
        "confidence": "low",
        "assumptions_failed": [reason],
        "warnings": [reason],
        "explanation": "Con la información disponible no corresponde recomendar todavía una prueba inferencial. Se sugiere mantener una lectura descriptiva hasta completar los supuestos necesarios.",
    }
