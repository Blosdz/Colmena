import pandas as pd
import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.analysis_run import AnalysisRun
from app.statistics import cronbach_alpha
from tests.test_analysis_orchestrator import prepare_orchestrator_fixture


def _classic_formula(df: pd.DataFrame) -> float:
    values = df.to_numpy(dtype=float)
    k = values.shape[1]
    item_variance = values.var(axis=0, ddof=1).sum()
    total_variance = values.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - item_variance / total_variance)


def test_cronbach_alpha_matches_classic_formula():
    df = pd.DataFrame(
        {
            "a": [4, 5, 3, 4, 5, 2, 4, 5, 3, 4],
            "b": [3, 5, 3, 4, 4, 2, 3, 5, 3, 4],
            "c": [4, 4, 2, 5, 5, 1, 4, 4, 2, 3],
            "d": [5, 5, 3, 4, 5, 2, 3, 4, 3, 4],
        }
    )
    item_columns = {f"item_{i}": col for i, col in enumerate(df.columns)}

    result = cronbach_alpha(df, item_columns, decimals=6)

    assert result.alpha == pytest.approx(_classic_formula(df), abs=1e-4)
    assert result.n_items == 4
    assert result.n_valid_cases == 10
    assert result.n_excluded_cases == 0
    assert result.classification in {"excelente", "bueno", "aceptable"}
    assert len(result.items) == 4
    # item-total corregida y alfa-si-se-elimina presentes para cada ítem
    assert all(item.item_total_correlation is not None for item in result.items)
    assert all(item.alpha_if_deleted is not None for item in result.items)


def test_cronbach_alpha_listwise_deletion():
    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, None],
            "b": [2, 2, 3, 4, 5],
            "c": [1, 3, 3, 4, 5],
        }
    )
    result = cronbach_alpha(df, {"i0": "a", "i1": "b", "i2": "c"})
    assert result.n_valid_cases == 4
    assert result.n_excluded_cases == 1
    assert "listwise_excluded_cases" in result.warnings


def test_cronbach_alpha_insufficient_items():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
    result = cronbach_alpha(df, {"i0": "a"})
    assert result.alpha is None
    assert result.classification == "not_applicable"
    assert "insufficient_items" in result.warnings


def test_cronbach_alpha_negative_flags_low_reliability():
    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            "b": [5, 4, 3, 2, 1],
            "c": [1, 5, 1, 5, 1],
        }
    )
    result = cronbach_alpha(df, {"i0": "a", "i1": "b", "i2": "c"})
    assert result.alpha is not None and result.alpha < 0
    assert result.classification == "inaceptable"
    assert "negative_alpha" in result.warnings
    assert "low_reliability" in result.warnings


def test_cronbach_alpha_constant_item_detected():
    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            "b": [3, 3, 3, 3, 3],
            "c": [2, 3, 3, 4, 5],
        }
    )
    result = cronbach_alpha(df, {"i0": "a", "i1": "b", "i2": "c"})
    assert "constant_item" in result.warnings
    constant = next(item for item in result.items if item.item_id == "i1")
    assert constant.item_total_correlation is None


def test_reliability_report_endpoint(client):
    fixture = prepare_orchestrator_fixture(client)
    form_id = fixture["form"]["id"]
    instrument_id = fixture["instrument"]["id"]

    response = client.get(f"/api/v1/forms/{form_id}/reliability")
    assert response.status_code == 200
    body = response.json()
    assert body["form_id"] == form_id
    assert body["total_targets"] >= 1

    instrument_targets = [t for t in body["results"] if t["target_type"] == "instrument"]
    assert instrument_targets, "expected at least one instrument target"
    instrument_target = next(t for t in instrument_targets if t["target_id"] == instrument_id)
    result = instrument_target["result"]
    assert result["n_items"] >= 2
    assert result["alpha"] is not None
    assert result["classification"] != "not_applicable"
    assert len(result["items"]) == result["n_items"]


def test_reliability_single_instrument_endpoint(client):
    fixture = prepare_orchestrator_fixture(client)
    form_id = fixture["form"]["id"]
    instrument_id = fixture["instrument"]["id"]

    response = client.get(f"/api/v1/forms/{form_id}/reliability/instruments/{instrument_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["target_type"] == "instrument"
    assert body["target_id"] == instrument_id
    assert body["result"]["alpha"] is not None


def test_reliability_unknown_instrument_returns_404(client):
    fixture = prepare_orchestrator_fixture(client)
    form_id = fixture["form"]["id"]
    response = client.get(f"/api/v1/forms/{form_id}/reliability/instruments/does-not-exist")
    assert response.status_code == 404


def test_reliability_run_persists_analysis_run(client):
    fixture = prepare_orchestrator_fixture(client)
    form_id = fixture["form"]["id"]

    response = client.post(f"/api/v1/forms/{form_id}/reliability/run", json={"store_result": True})
    assert response.status_code == 200
    body = response.json()
    assert body["analysis_run_id"] is not None
    assert body["report"]["total_targets"] >= 1

    with SessionLocal() as session:
        run = session.scalar(
            select(AnalysisRun).where(AnalysisRun.id == body["analysis_run_id"])
        )
        assert run is not None
        assert run.analysis_type == "reliability"
        assert run.status == "completed"
        assert run.result_json["total_targets"] == body["report"]["total_targets"]
