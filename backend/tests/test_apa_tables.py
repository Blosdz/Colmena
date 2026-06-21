from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.export_artifact import ExportArtifact
from tests.test_analysis_orchestrator import prepare_orchestrator_fixture
from tests.test_group_comparisons import create_form, create_project


def export_artifact_exists(artifact_id: str) -> bool:
    with SessionLocal() as session:
        artifact = session.scalar(select(ExportArtifact).where(ExportArtifact.id == artifact_id))
        return artifact is not None


def test_apa_tables_end_to_end(client: TestClient):
    fixture = prepare_orchestrator_fixture(client)
    form = fixture["form"]
    questions = fixture["questions"]
    instrument = fixture["instrument"]
    dimension = fixture["dimension"]

    frequency_response = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/generate",
        json={
            "table_type": "frequencies",
            "source_type": "live",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {"question_ids": [questions["sexo"]["id"]]},
        },
    )
    assert frequency_response.status_code == 200
    frequency_body = frequency_response.json()
    assert frequency_body["table_type"] == "frequencies"
    assert [column["label"] for column in frequency_body["columns"]][1:] == ["n", "%", "% valido", "% acumulado"]
    assert frequency_body["markdown"]
    assert frequency_body["html"]
    assert any("porcentajes validos" in note["text"].lower() for note in frequency_body["notes"])

    descriptive_response = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/generate",
        json={
            "table_type": "descriptives",
            "source_type": "live",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {"question_ids": [questions["edad"]["id"], questions["rendimiento"]["id"]]},
        },
    )
    assert descriptive_response.status_code == 200
    descriptive_body = descriptive_response.json()
    descriptive_labels = [column["label"] for column in descriptive_body["columns"]]
    assert "M" in descriptive_labels
    assert "DE" in descriptive_labels
    assert "Mdn" in descriptive_labels
    assert any("de = desviacion estandar" in note["text"].lower() for note in descriptive_body["notes"])

    normality_response = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/generate",
        json={
            "table_type": "normality",
            "source_type": "live",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert normality_response.status_code == 200
    normality_body = normality_response.json()
    assert [column["label"] for column in normality_body["columns"]] == [
        "Variable",
        "n",
        "Prueba",
        "Estadistico",
        "p",
        "Decision",
    ]

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

    correlation_table = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/from-analysis-run/{correlation_run_id}"
    )
    assert correlation_table.status_code == 200
    correlation_table_body = correlation_table.json()
    assert correlation_table_body["total_tables"] == 1
    assert correlation_table_body["tables"][0]["table_type"] == "correlation"
    assert "< .001" in correlation_table_body["tables"][0]["markdown"] or "= ." in correlation_table_body["tables"][0]["markdown"]

    correlation_matrix_response = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/generate",
        json={
            "table_type": "correlation_matrix",
            "source_type": "live",
            "target_ids": [questions["edad"]["id"], questions["rendimiento"]["id"], questions["item_01"]["id"]],
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {"target_type": "question", "method": "auto"},
        },
    )
    assert correlation_matrix_response.status_code == 200
    correlation_matrix_body = correlation_matrix_response.json()
    assert correlation_matrix_body["table_type"] == "correlation_matrix"
    assert len(correlation_matrix_body["rows"]) == 3

    comparison_run = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["rendimiento"]["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "t_student_independent",
            "store_result": True,
        },
    )
    assert comparison_run.status_code == 200
    comparison_run_id = comparison_run.json()["analysis_run_id"]
    comparison_table = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/from-analysis-run/{comparison_run_id}"
    )
    assert comparison_table.status_code == 200
    assert comparison_table.json()["tables"][0]["table_type"] == "group_comparison"

    association_run = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": questions["ansiedad"]["id"]},
            "method": "chi_square",
            "store_result": True,
        },
    )
    assert association_run.status_code == 200
    association_run_id = association_run.json()["analysis_run_id"]
    association_table = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/from-analysis-run/{association_run_id}"
    )
    assert association_table.status_code == 200
    assert association_table.json()["tables"][0]["table_type"] == "categorical_association"

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
    orchestrated_tables = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/from-orchestrated-run/{orchestrated_run_id}"
    )
    assert orchestrated_tables.status_code == 200
    assert orchestrated_tables.json()["total_tables"] >= 1

    batch_response = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/batch",
        json={
            "form_id": form["id"],
            "table_types": ["frequencies", "descriptives", "normality"],
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert batch_response.status_code == 200
    batch_body = batch_response.json()
    assert batch_body["total_tables"] == 3

    markdown_export = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/export/markdown",
        json={
            "form_id": form["id"],
            "table_types": ["frequencies", "descriptives", "normality"],
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert markdown_export.status_code == 200
    markdown_export_body = markdown_export.json()
    assert markdown_export_body["artifact_id"] is not None
    assert Path(markdown_export_body["file_path"]).exists()
    assert export_artifact_exists(markdown_export_body["artifact_id"])

    html_export = client.post(
        f"/api/v1/forms/{form['id']}/apa-tables/export/html",
        json={
            "form_id": form["id"],
            "table_types": ["frequencies", "descriptives", "normality"],
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert html_export.status_code == 200
    html_export_body = html_export.json()
    assert html_export_body["artifact_id"] is not None
    assert Path(html_export_body["file_path"]).exists()
    assert export_artifact_exists(html_export_body["artifact_id"])

    options_response = client.get(f"/api/v1/forms/{form['id']}/apa-tables/options")
    assert options_response.status_code == 200
    options_body = options_response.json()
    assert "descriptives" in options_body["table_types"]
    assert options_body["analysis_runs"]

    empty_project = create_project(client, "Proyecto vacio APA")
    empty_form = create_form(client, empty_project["id"], "Formulario vacio APA")
    empty_table = client.post(
        f"/api/v1/forms/{empty_form['id']}/apa-tables/generate",
        json={
            "table_type": "descriptives",
            "source_type": "live",
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "options": {},
        },
    )
    assert empty_table.status_code == 200
    assert empty_table.json()["warnings"]

    exe_paths = list(Path("E:/Colmena/backend").rglob("*.exe"))
    assert all(".venv" in str(path) for path in exe_paths)
    assert not list(Path("E:/Colmena/backend").rglob("u.exe"))
