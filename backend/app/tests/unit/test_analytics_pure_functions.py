from app.analytics.crosstabs import compute_crosstab
from app.analytics.descriptive import compute_descriptive
from app.analytics.frequencies import compute_frequencies
from app.services.privacy_service import PrivacyService


def test_descriptive_basic_stats() -> None:
    result = compute_descriptive([18, 20, 22, 24, 26])
    assert result["n_valid"] == 5
    assert result["mean"] == 22
    assert result["median"] == 22
    assert result["min"] == 18
    assert result["max"] == 26
    assert result["quartiles"] is not None


def test_descriptive_empty_list() -> None:
    result = compute_descriptive([])
    assert result["n_valid"] == 0
    assert result["mean"] is None


def test_descriptive_single_value_no_variance_error() -> None:
    result = compute_descriptive([42])
    assert result["n_valid"] == 1
    assert result["std"] == 0.0
    assert result["quartiles"] is None


def test_frequencies_counts_and_percentages() -> None:
    result = compute_frequencies(["M", "F", "F", "M", "F"])
    assert result["n_valid"] == 5
    by_value = {c["value"]: c for c in result["categories"]}
    assert by_value["F"]["n"] == 3
    assert by_value["F"]["pct"] == 60.0
    assert by_value["M"]["n"] == 2
    assert by_value["M"]["pct"] == 40.0


def test_crosstab_count_mode() -> None:
    pairs = [("M", "Alto"), ("M", "Bajo"), ("F", "Alto"), ("F", "Alto")]
    result = compute_crosstab(pairs, "COUNT")
    assert result["grand_total"] == 4
    row_m = next(r for r in result["table"] if r["row"] == "M")
    assert row_m["cells"]["Alto"] == 1
    assert row_m["cells"]["Bajo"] == 1


def test_crosstab_row_percent_mode() -> None:
    pairs = [("M", "Alto"), ("M", "Bajo"), ("F", "Alto"), ("F", "Alto")]
    result = compute_crosstab(pairs, "ROW_PERCENT")
    row_f = next(r for r in result["table"] if r["row"] == "F")
    assert row_f["cells"]["Alto"] == 100.0


def test_crosstab_raw_counts_are_independent_of_percentage_mode() -> None:
    pairs = [("M", "Alto"), ("M", "Bajo"), ("F", "Alto"), ("F", "Alto")]
    result = compute_crosstab(pairs, "ROW_PERCENT")
    assert result["raw_counts"]["F"]["Alto"] == 2
    assert result["raw_counts"]["M"]["Bajo"] == 1


def test_suppress_crosstab_table_hides_cells_below_min_n() -> None:
    """Inspirado en el ejemplo de E-05 del documento de auditoría: una fila
    con n = [16,7,5,6,5,5,0] y min_publishable_n=5 -> sólo la celda con n=0
    se suprime por debajo del umbral. Se añade una segunda fila para que la
    columna "g" exista en col_values (compute_crosstab sólo incluye
    columnas observadas en algún par)."""
    pairs = (
        [("1", "a")] * 16
        + [("1", "b")] * 7
        + [("1", "c")] * 5
        + [("1", "d")] * 6
        + [("1", "e")] * 5
        + [("1", "f")] * 5
        # fila "1" nunca tiene la columna "g" -> n=0 en esa celda
        + [("2", "g")] * 5
    )
    stats = compute_crosstab(pairs, "COUNT")
    result = PrivacyService.suppress_crosstab_table(stats, min_publishable_n=5)

    row = next(r for r in result["table"] if r["row"] == "1")
    # "g" se suprime por debajo del umbral; al quedar como única celda
    # suprimida de la fila, la supresión secundaria oculta además la celda
    # visible más pequeña ("c", empatada en n=5 con "e"/"f" pero primera en
    # orden alfabético) para que row_total no permita deducir "g" por resta.
    assert row["cells"]["g"] is None
    assert row["cells"]["c"] is None
    assert row["cells"]["a"] == 16
    assert row["cells"]["d"] == 6
    assert sorted(row["suppressed_columns"]) == ["c", "g"]
    assert "raw_counts" not in result


def test_suppress_crosstab_table_applies_secondary_suppression() -> None:
    """Si sólo se suprime una celda de la fila, el row_total permitiría
    deducirla por resta -> se suprime también la celda visible más chica."""
    pairs = [("1", "a")] * 10 + [("1", "b")] * 2 + [("1", "c")] * 1
    stats = compute_crosstab(pairs, "COUNT")
    result = PrivacyService.suppress_crosstab_table(stats, min_publishable_n=5)

    row = next(r for r in result["table"] if r["row"] == "1")
    assert row["cells"]["c"] is None
    assert row["cells"]["b"] is None
    assert row["cells"]["a"] == 10
    assert sorted(row["suppressed_columns"]) == ["b", "c"]
