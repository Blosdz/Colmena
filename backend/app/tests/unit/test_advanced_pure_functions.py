from app.analytics.binning import bin_points
from app.analytics.clustering import compute_kmeans
from app.analytics.regression import compute_logistic_regression


def test_logistic_regression_separates_clear_groups() -> None:
    predictors = [[1], [2], [3], [4], [5], [6]]
    outcome = [0, 0, 0, 1, 1, 1]
    result = compute_logistic_regression(predictors, outcome)
    assert result["n"] == 6
    assert result["accuracy"] == 1.0
    assert result["coefficients"][0] > 0  # a mayor predictor, mayor prob. de outcome=1


def test_kmeans_finds_two_well_separated_clusters() -> None:
    points = [[0, 0], [0, 1], [1, 0], [10, 10], [10, 11], [11, 10]]
    result = compute_kmeans(points, k=2)
    assert result["k"] == 2
    assert result["cluster_sizes"] == [3, 3]
    assert result["inertia"] < 10


def test_bin_points_preserves_total_count() -> None:
    points = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (2.0, 2.0), (5.0, 5.0)]
    bins = bin_points(points, bin_count=10)
    assert sum(bucket["n"] for bucket in bins) == len(points)
    assert len(bins) <= 100


def test_bin_points_never_exposes_individual_coordinates() -> None:
    points = [(1.23456, 7.89), (1.23457, 7.891)]
    bins = bin_points(points, bin_count=10)
    for bucket in bins:
        assert set(bucket) == {"x_bin_center", "y_bin_center", "n"}
    assert {(1.23456, 7.89), (1.23457, 7.891)}.isdisjoint(
        {(b["x_bin_center"], b["y_bin_center"]) for b in bins}
    )


def test_bin_points_empty_returns_empty() -> None:
    assert bin_points([]) == []


def test_bin_points_single_repeated_point_falls_in_one_bin() -> None:
    bins = bin_points([(3.0, 3.0)] * 5, bin_count=10)
    assert len(bins) == 1
    assert bins[0]["n"] == 5


def test_kmeans_labels_length_matches_input() -> None:
    points = [[i, i] for i in range(9)]
    result = compute_kmeans(points, k=3)
    assert len(result["labels"]) == 9
    assert len(result["centroids"]) == 3
