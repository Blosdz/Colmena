from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.export_artifact import ExportArtifact
from tests.test_analysis_orchestrator import prepare_orchestrator_fixture
from tests.test_group_comparisons import create_form, create_project


def chart_export_artifact_exists(artifact_id: str) -> bool:
    with SessionLocal() as session:
        artifact = session.scalar(select(ExportArtifact).where(ExportArtifact.id == artifact_id))
        return artifact is not None


def test_charts_end_to_end(client: TestClient):
    fixture = prepare_orchestrator_fixture(client)
    form = fixture["form"]
    questions = fixture["questions"]

    bar_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/generate",
        json={
            "chart_type": "bar",
            "source_type": "live",
            "analysis_goal": "frequencies",
            "targets": [{"target_type": "question", "target_id": questions["sexo"]["id"], "role": "target"}],
            "theme": "colmena_premium",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {"show_percentages": True, "show_frequencies": True},
        },
    )
    assert bar_response.status_code == 200
    bar_body = bar_response.json()
    assert bar_body["chart_type"] == "bar"
    assert bar_body["plotly_data"]
    assert bar_body["plotly_layout"]
    assert bar_body["plotly_config"]
    assert bar_body["editable_options"]["can_change_chart_type"] is True
    assert bar_body["recommended_alternatives"]
    assert bar_body["plain_language_explanation"]

    donut_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/generate",
        json={
            "chart_type": "donut",
            "source_type": "live",
            "analysis_goal": "frequencies",
            "targets": [{"target_type": "question", "target_id": questions["sexo"]["id"], "role": "target"}],
            "theme": "colmena_premium",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert donut_response.status_code == 200
    assert donut_response.json()["chart_type"] == "donut"

    histogram_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/generate",
        json={
            "chart_type": "histogram",
            "source_type": "live",
            "analysis_goal": "descriptives",
            "targets": [{"target_type": "question", "target_id": questions["edad"]["id"], "role": "target"}],
            "theme": "academic_light",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert histogram_response.status_code == 200
    assert histogram_response.json()["chart_type"] == "histogram"

    boxplot_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/generate",
        json={
            "chart_type": "boxplot",
            "source_type": "live",
            "analysis_goal": "descriptives",
            "targets": [{"target_type": "question", "target_id": questions["rendimiento"]["id"], "role": "target"}],
            "theme": "academic_light",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert boxplot_response.status_code == 200
    assert boxplot_response.json()["chart_type"] == "boxplot"

    scatter_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/generate",
        json={
            "chart_type": "scatter",
            "source_type": "live",
            "analysis_goal": "correlation",
            "targets": [
                {"target_type": "question", "target_id": questions["edad"]["id"], "role": "x"},
                {"target_type": "question", "target_id": questions["rendimiento"]["id"], "role": "y"},
            ],
            "theme": "colmena_premium",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {"method": "pearson"},
        },
    )
    assert scatter_response.status_code == 200
    assert scatter_response.json()["chart_type"] == "scatter"

    heatmap_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/generate",
        json={
            "chart_type": "heatmap",
            "source_type": "live",
            "analysis_goal": "correlation_matrix",
            "targets": [
                {"target_type": "question", "target_id": questions["edad"]["id"], "role": "target"},
                {"target_type": "question", "target_id": questions["rendimiento"]["id"], "role": "target"},
                {"target_type": "question", "target_id": questions["item_01"]["id"], "role": "target"},
            ],
            "theme": "colmena_premium",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {"method": "auto"},
        },
    )
    assert heatmap_response.status_code == 200
    assert heatmap_response.json()["chart_type"] == "heatmap"

    grouped_bar_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/generate",
        json={
            "chart_type": "grouped_bar",
            "source_type": "live",
            "analysis_goal": "categorical_association",
            "targets": [
                {"target_type": "question", "target_id": questions["sexo"]["id"], "role": "row"},
                {"target_type": "question", "target_id": questions["ansiedad"]["id"], "role": "column"},
            ],
            "theme": "presentation_clean",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {"method": "chi_square"},
        },
    )
    assert grouped_bar_response.status_code == 200
    assert grouped_bar_response.json()["chart_type"] == "grouped_bar"

    correlation_run = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["edad"]["id"]},
            "y": {"target_type": "question", "target_id": questions["rendimiento"]["id"]},
            "method": "pearson",
            "store_result": True,
        },
    )
    assert correlation_run.status_code == 200
    correlation_run_id = correlation_run.json()["analysis_run_id"]
    assert correlation_run_id is not None

    from_analysis_run = client.post(
        f"/api/v1/forms/{form['id']}/charts/from-analysis-run/{correlation_run_id}"
    )
    assert from_analysis_run.status_code == 200
    from_analysis_body = from_analysis_run.json()
    assert from_analysis_body["total_charts"] >= 1
    assert from_analysis_body["charts"][0]["plotly_data"]

    orchestrated_run = client.post(
        f"/api/v1/forms/{form['id']}/analysis/run",
        json={
            "analysis_goal": "correlation",
            "targets": [
                {"target_type": "question", "target_id": questions["edad"]["id"], "role": "x"},
                {"target_type": "question", "target_id": questions["rendimiento"]["id"], "role": "y"},
            ],
            "method": "auto",
            "store_result": True,
            "options": {"include_normality": True, "include_descriptives": True, "include_recommendations": True},
        },
    )
    assert orchestrated_run.status_code == 200
    orchestrated_run_id = orchestrated_run.json()["analysis_run_id"]
    assert orchestrated_run_id is not None

    from_orchestrated = client.post(
        f"/api/v1/forms/{form['id']}/charts/from-orchestrated-run/{orchestrated_run_id}"
    )
    assert from_orchestrated.status_code == 200
    from_orchestrated_body = from_orchestrated.json()
    assert from_orchestrated_body["total_charts"] >= 1
    assert from_orchestrated_body["charts"][0]["plotly_layout"]

    recommended_response = client.get(
        f"/api/v1/forms/{form['id']}/charts/recommended?theme=colmena_premium&max_charts=10"
    )
    assert recommended_response.status_code == 200
    recommended_body = recommended_response.json()
    assert recommended_body["total_charts"] >= 1

    batch_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/batch",
        json={
            "source_type": "live",
            "chart_types": ["bar", "histogram", "boxplot"],
            "theme": "colmena_premium",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert batch_response.status_code == 200
    assert batch_response.json()["total_charts"] == 3

    options_response = client.get(f"/api/v1/forms/{form['id']}/charts/options")
    assert options_response.status_code == 200
    options_body = options_response.json()
    assert "bar" in options_body["available_chart_types"]
    assert "colmena_premium" in options_body["available_themes"]
    assert options_body["analysis_runs"]

    export_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/export/json",
        json={
            "format": "json",
            "source_type": "live",
            "chart_types": ["bar", "histogram", "boxplot"],
            "theme": "colmena_premium",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert export_response.status_code == 200
    export_body = export_response.json()
    assert export_body["artifact_id"] is not None
    assert Path(export_body["file_path"]).exists()
    assert chart_export_artifact_exists(export_body["artifact_id"])

    incompatible_response = client.post(
        f"/api/v1/forms/{form['id']}/charts/generate",
        json={
            "chart_type": "scatter",
            "source_type": "live",
            "analysis_goal": "frequencies",
            "targets": [{"target_type": "question", "target_id": questions["sexo"]["id"], "role": "target"}],
            "theme": "colmena_premium",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert incompatible_response.status_code == 200
    assert "incompatible_chart_type" in incompatible_response.json()["warnings"]

    empty_project = create_project(client, "Proyecto vacio charts")
    empty_form = create_form(client, empty_project["id"], "Formulario vacio charts")
    empty_chart_response = client.post(
        f"/api/v1/forms/{empty_form['id']}/charts/generate",
        json={
            "chart_type": "histogram",
            "source_type": "live",
            "analysis_goal": "descriptives",
            "theme": "colmena_premium",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert empty_chart_response.status_code == 200
    assert empty_chart_response.json()["warnings"]

    exe_paths = list(Path("E:/Colmena/backend").rglob("*.exe"))
    assert all(".venv" in str(path) for path in exe_paths)
    assert not list(Path("E:/Colmena/backend").rglob("u.exe"))
