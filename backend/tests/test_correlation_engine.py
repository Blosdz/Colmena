import pandas as pd

from app.statistics.correlation_engine import (
    classify_correlation_magnitude,
    correlation_magnitude_label,
    is_dichotomous,
    point_biserial_correlation,
    run_correlation,
)
from app.statistics.decision_engine import recommend_correlation


def test_magnitude_bands_align_with_five_level_table():
    assert classify_correlation_magnitude(0.10) == "very_weak"
    assert classify_correlation_magnitude(0.30) == "weak"
    assert classify_correlation_magnitude(0.50) == "moderate"
    assert classify_correlation_magnitude(-0.70) == "strong"
    assert classify_correlation_magnitude(0.90) == "very_strong"
    assert classify_correlation_magnitude(None) == "not_applicable"


def test_magnitude_band_boundaries():
    assert classify_correlation_magnitude(0.199) == "very_weak"
    assert classify_correlation_magnitude(0.20) == "weak"
    assert classify_correlation_magnitude(0.399) == "weak"
    assert classify_correlation_magnitude(0.40) == "moderate"
    assert classify_correlation_magnitude(0.60) == "strong"
    assert classify_correlation_magnitude(0.80) == "very_strong"


def test_magnitude_labels_are_spanish():
    assert correlation_magnitude_label("very_weak") == "muy débil"
    assert correlation_magnitude_label("moderate") == "moderada"
    assert correlation_magnitude_label("very_strong") == "muy fuerte"
    assert correlation_magnitude_label("not_applicable") == "no aplicable"


def test_is_dichotomous_detects_two_categories():
    assert is_dichotomous(pd.Series([0, 1, 0, 1, 1])) is True
    assert is_dichotomous(pd.Series([1, 2, 3, 4])) is False
    assert is_dichotomous(pd.Series([], dtype="float")) is False


def test_point_biserial_executes_with_dichotomous_and_continuous():
    binary = pd.Series([0, 0, 0, 1, 1, 1, 0, 1, 0, 1])
    continuous = pd.Series([10.0, 11.0, 9.5, 20.0, 21.0, 19.5, 10.5, 22.0, 9.0, 20.5])
    result = point_biserial_correlation(binary, continuous, alpha=0.05, decimals=3)
    assert result["method_used"] == "point_biserial"
    assert result["coefficient"] is not None
    assert result["p_value"] is not None
    assert result["direction"] == "positive"
    assert "dichotomous_continuous_pair" in result["assumptions"]


def test_point_biserial_not_applicable_without_dichotomous():
    x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    y = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])
    result = point_biserial_correlation(x, y, alpha=0.05)
    assert result["method_used"] == "point_biserial"
    assert result["coefficient"] is None
    assert "no_dichotomous_variable" in result["warnings"]


def test_run_correlation_dispatches_point_biserial():
    binary = pd.Series([0, 1, 0, 1, 0, 1])
    continuous = pd.Series([1.0, 5.0, 1.5, 4.5, 2.0, 6.0])
    result = run_correlation(binary, continuous, method="point_biserial")
    assert result["method_used"] == "point_biserial"


def test_recommend_correlation_prefers_point_biserial():
    result = recommend_correlation(
        all_normal=True,
        has_ordinal=False,
        min_valid_n=40,
        has_dichotomous_continuous=True,
    )
    assert result["recommended_test"] == "point_biserial"


def test_recommend_correlation_prefers_kendall_for_small_tied_ordinal():
    result = recommend_correlation(
        all_normal=False,
        has_ordinal=True,
        min_valid_n=12,
        many_ties=True,
    )
    assert result["recommended_test"] == "kendall"


def test_recommend_correlation_ordinal_large_sample_uses_spearman():
    result = recommend_correlation(
        all_normal=False,
        has_ordinal=True,
        min_valid_n=120,
        many_ties=True,
    )
    assert result["recommended_test"] == "spearman"


def test_recommend_correlation_normal_large_sample_uses_pearson():
    result = recommend_correlation(all_normal=True, has_ordinal=False, min_valid_n=50)
    assert result["recommended_test"] == "pearson"
