import pytest

from app.analytics.censopas.classification import (
    classify_collective_result,
    classify_construct_score,
    cutoff_to_bands,
    summarize_trichotomy,
)
from app.analytics.censopas.scoring import (
    aggregate_construct_score,
    apply_direction,
    derive_item_values,
    score_item,
)


def test_score_item_maps_raw_code() -> None:
    assert score_item("1", {"1": 0, "2": 50, "3": 100}) == 0
    assert score_item("3", {"1": 0, "2": 50, "3": 100}) == 100


def test_score_item_missing_code_returns_none() -> None:
    assert score_item(None, {"1": 0}) is None
    assert score_item("9", {"1": 0}) is None


def test_apply_direction_reverses_score() -> None:
    assert apply_direction(80, "REVERSE") == 20
    assert apply_direction(80, "DIRECT") == 80
    assert apply_direction(80, None) == 80


def test_aggregate_construct_score_weighted_average() -> None:
    # dos ítems, mismo peso, uno REVERSE
    score = aggregate_construct_score([(80, 1, "DIRECT"), (80, 1, "REVERSE")])
    assert score == 50.0  # (80 + 20) / 2


def test_aggregate_construct_score_empty_returns_none() -> None:
    assert aggregate_construct_score([]) is None


def test_classify_construct_score_higher_better() -> None:
    assert classify_construct_score(10, 33, 66, "HIGHER_BETTER") == "DESFAVORABLE"
    assert classify_construct_score(50, 33, 66, "HIGHER_BETTER") == "INTERMEDIO"
    assert classify_construct_score(90, 33, 66, "HIGHER_BETTER") == "FAVORABLE"


def test_classify_construct_score_lower_better() -> None:
    assert classify_construct_score(10, 33, 66, "LOWER_BETTER") == "FAVORABLE"
    assert classify_construct_score(90, 33, 66, "LOWER_BETTER") == "DESFAVORABLE"



def test_derive_item_values_keeps_risk_and_transformed_score_separate() -> None:
    risk, score = derive_item_values("1", {"1": 1, "5": 5}, "REVERSE")
    assert risk == 5
    assert score == 100
    risk, score = derive_item_values("5", {"1": 1, "5": 5}, "DIRECT")
    assert risk == 5
    assert score == 100


def test_classification_includes_exact_cutoff_boundaries() -> None:
    assert classify_construct_score(33, 33, 66, "LOWER_BETTER") == "FAVORABLE"
    assert classify_construct_score(66, 33, 66, "LOWER_BETTER") == "INTERMEDIO"


@pytest.mark.parametrize(
    ("fav", "inter", "unfav", "expected"),
    [
        (10, 20, 70, "RIESGO_ALTO"),
        (60, 20, 20, "FACTOR_PROTECTOR"),
        (20, 60, 20, "RIESGO_MEDIO"),
        (34, 33, 33, "REVISION"),
    ],
)
def test_classify_collective_result(fav, inter, unfav, expected) -> None:
    assert classify_collective_result(fav, inter, unfav) == expected


def test_cutoff_to_bands_lower_better_codes_are_language_stable() -> None:
    bands = cutoff_to_bands(33, 66, "LOWER_BETTER", "Favorable", "Intermedio", "Desfavorable")
    by_code = {band["code"]: band for band in bands}
    assert set(by_code) == {"FAVORABLE", "INTERMEDIATE", "UNFAVORABLE"}
    assert by_code["FAVORABLE"]["min_value"] == 0.0
    assert by_code["FAVORABLE"]["max_value"] == 33.0
    assert by_code["UNFAVORABLE"]["min_value"] == 66.0
    assert by_code["UNFAVORABLE"]["max_value"] == 100.0
    # classification_code nunca depende del idioma/texto del label visible.
    assert by_code["UNFAVORABLE"]["label"] == "Desfavorable"
    assert all(band["classification_code"] == band["code"] for band in bands)


def test_cutoff_to_bands_higher_better_flips_ranges() -> None:
    bands = cutoff_to_bands(33, 66, "HIGHER_BETTER", "Favorable", "Intermedio", "Desfavorable")
    by_code = {band["code"]: band for band in bands}
    assert by_code["UNFAVORABLE"]["min_value"] == 0.0
    assert by_code["FAVORABLE"]["max_value"] == 100.0


def test_summarize_trichotomy_empty() -> None:
    summary = summarize_trichotomy([])
    assert summary["n_valid"] == 0
    assert summary["classification"] is None


def test_summarize_trichotomy_computes_collective_classification() -> None:
    values = [(10.0, "UNFAVORABLE")] * 8 + [(50.0, "INTERMEDIATE")] * 1 + [(90.0, "FAVORABLE")] * 1
    summary = summarize_trichotomy(values)
    assert summary["n_valid"] == 10
    assert summary["unfavorable_n"] == 8
    assert summary["unfavorable_pct"] == 80.0
    assert summary["classification"] == "RIESGO_ALTO"
