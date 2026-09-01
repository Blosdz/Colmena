from app.analytics.inferential import (
    compute_chi_square,
    compute_kruskal_wallis,
    compute_mann_whitney,
    compute_spearman,
)
from app.analytics.multiple_testing import adjust_pvalues_bh
from app.analytics.reliability import compute_cronbach_alpha, compute_mcdonald_omega


def test_chi_square_warns_on_low_expected_frequency() -> None:
    result = compute_chi_square([[1, 1], [1, 8]])
    assert result["warnings"]


def test_chi_square_no_warning_with_adequate_frequencies() -> None:
    result = compute_chi_square([[20, 20], [20, 20]])
    assert result["warnings"] == []
    assert result["p_value"] == 1.0


def test_mann_whitney_effect_size_range() -> None:
    result = compute_mann_whitney([1, 2, 3], [10, 11, 12])
    assert result["effect_size"] == 1.0
    assert result["effect_label"] == "LARGE"


def test_kruskal_wallis_three_groups() -> None:
    result = compute_kruskal_wallis([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    assert result["degrees_freedom"] == 2
    assert result["n"] == 9


def test_spearman_perfect_monotonic_relationship() -> None:
    result = compute_spearman([1, 2, 3, 4], [10, 20, 30, 40])
    assert result["statistic"] == 1.0


def test_adjust_pvalues_bh_monotonic_and_bounded() -> None:
    adjusted = adjust_pvalues_bh([0.5, 0.01, 0.3, 0.04])
    assert all(0 <= p <= 1 for p in adjusted)
    # El más pequeño original debe seguir siendo el más pequeño ajustado.
    assert adjusted[1] == min(adjusted)


def test_adjust_pvalues_bh_empty() -> None:
    assert adjust_pvalues_bh([]) == []


def test_cronbach_alpha_perfectly_consistent_items() -> None:
    matrix = [[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]]
    alpha = compute_cronbach_alpha(matrix)
    assert alpha == 1.0


def test_cronbach_alpha_insufficient_data_returns_none() -> None:
    assert compute_cronbach_alpha([[1, 2, 3]]) is None
    assert compute_cronbach_alpha([[1], [2]]) is None


def test_mcdonald_omega_returns_value_for_correlated_items() -> None:
    matrix = [[1, 1, 2], [2, 2, 3], [3, 3, 4], [4, 5, 5], [5, 4, 5]]
    omega = compute_mcdonald_omega(matrix)
    assert omega is not None
    assert 0 <= omega <= 1.5  # aproximación; se acepta un margen razonable
