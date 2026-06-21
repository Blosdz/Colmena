from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models.analysis_run import AnalysisRun
from tests.test_group_comparisons import (
    create_form,
    create_option,
    create_project,
    create_project_variable,
    create_question,
    submit_public_response,
)


def count_orchestrated_runs() -> int:
    with SessionLocal() as session:
        return int(
            session.scalar(
                select(func.count()).select_from(AnalysisRun).where(AnalysisRun.analysis_type == "orchestrated_analysis")
            )
            or 0
        )


def prepare_orchestrator_fixture(client: TestClient) -> dict:
    project = create_project(client, "Proyecto orquestador")
    sexo_variable = create_project_variable(
        client,
        project["id"],
        {
            "name": "Sexo",
            "code": "sexo",
            "variable_role": "sociodemographic",
            "measurement_level": "nominal",
            "data_type": "categorical",
        },
    )
    rendimiento_variable = create_project_variable(
        client,
        project["id"],
        {
            "name": "Rendimiento academico",
            "code": "rendimiento",
            "variable_role": "outcome",
            "measurement_level": "ratio",
            "data_type": "numeric",
        },
    )

    form = create_form(client, project["id"], "Formulario orquestador")

    sexo_question = create_question(
        client,
        form["id"],
        {
            "code": "sexo",
            "label": "Sexo",
            "question_type": "single_choice",
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "project_variable_id": sexo_variable["id"],
            "is_required": True,
            "sort_order": 1,
        },
    )
    ansiedad_question = create_question(
        client,
        form["id"],
        {
            "code": "ansiedad",
            "label": "Nivel de ansiedad",
            "question_type": "single_choice",
            "question_role": "variable_item",
            "measurement_level": "ordinal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 2,
        },
    )
    edad_question = create_question(
        client,
        form["id"],
        {
            "code": "edad",
            "label": "Edad",
            "question_type": "number",
            "question_role": "sociodemographic",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "min_value": 18,
            "max_value": 60,
            "sort_order": 3,
        },
    )
    rendimiento_question = create_question(
        client,
        form["id"],
        {
            "code": "rendimiento",
            "label": "Rendimiento academico",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "project_variable_id": rendimiento_variable["id"],
            "is_required": True,
            "min_value": 0,
            "max_value": 100,
            "sort_order": 4,
        },
    )

    sexo_f = create_option(client, sexo_question["id"], {"label": "Femenino", "value": "F", "sort_order": 1})
    sexo_m = create_option(client, sexo_question["id"], {"label": "Masculino", "value": "M", "sort_order": 2})
    ansiedad_baja = create_option(client, ansiedad_question["id"], {"label": "Baja", "value": "baja", "sort_order": 1})
    ansiedad_media = create_option(client, ansiedad_question["id"], {"label": "Media", "value": "media", "sort_order": 2})
    ansiedad_alta = create_option(client, ansiedad_question["id"], {"label": "Alta", "value": "alta", "sort_order": 3})

    instrument_response = client.post(
        f"/api/v1/forms/{form['id']}/instruments",
        json={"name": "Escala de compromiso", "project_variable_id": rendimiento_variable["id"], "sort_order": 1},
    )
    assert instrument_response.status_code == 201
    instrument = instrument_response.json()

    dimension_response = client.post(
        f"/api/v1/form-instruments/{instrument['id']}/dimensions",
        json={"name": "Compromiso academico", "sort_order": 1},
    )
    assert dimension_response.status_code == 201
    dimension = dimension_response.json()

    likert_questions: dict[str, dict] = {}
    likert_options: dict[str, list[dict]] = {}
    for sort_order, code in enumerate(["item_01", "item_02", "item_03"], start=5):
        question = create_question(
            client,
            form["id"],
            {
                "code": code,
                "label": f"Pregunta {code}",
                "question_type": "likert",
                "question_role": "dimension_item",
                "measurement_level": "ordinal",
                "data_type": "numeric",
                "instrument_id": instrument["id"],
                "dimension_id": dimension["id"],
                "project_variable_id": rendimiento_variable["id"],
                "is_required": True,
                "is_scored": True,
                "sort_order": sort_order,
            },
        )
        likert_questions[code] = question
        likert_options[code] = [
            create_option(
                client,
                question["id"],
                {"label": f"Likert {score}", "value": str(score), "score": float(score), "sort_order": score},
            )
            for score in range(1, 6)
        ]

    publish = client.post(f"/api/v1/forms/{form['id']}/publish")
    assert publish.status_code == 200
    public_slug = publish.json()["public_slug"]

    edades = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]
    rendimientos = [48, 50, 52, 54, 55, 57, 60, 62, 63, 65, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86]
    sexos = [sexo_f["id"]] * 10 + [sexo_m["id"]] * 10
    ansiedad = [
        ansiedad_baja["id"],
        ansiedad_baja["id"],
        ansiedad_media["id"],
        ansiedad_media["id"],
        ansiedad_media["id"],
        ansiedad_alta["id"],
        ansiedad_alta["id"],
        ansiedad_alta["id"],
        ansiedad_alta["id"],
        ansiedad_alta["id"],
        ansiedad_baja["id"],
        ansiedad_baja["id"],
        ansiedad_media["id"],
        ansiedad_media["id"],
        ansiedad_media["id"],
        ansiedad_alta["id"],
        ansiedad_alta["id"],
        ansiedad_alta["id"],
        ansiedad_alta["id"],
        ansiedad_alta["id"],
    ]
    likert_levels = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 4, 4]

    response_ids: list[str] = []
    for index in range(20):
        response = submit_public_response(
            client,
            public_slug,
            {
                "respondent_code": f"O-{index + 1:03d}",
                "answers": [
                    {"question_id": sexo_question["id"], "option_id": sexos[index]},
                    {"question_id": ansiedad_question["id"], "option_id": ansiedad[index]},
                    {"question_id": edad_question["id"], "value_number": edades[index]},
                    {"question_id": rendimiento_question["id"], "value_number": rendimientos[index]},
                    {"question_id": likert_questions["item_01"]["id"], "option_id": likert_options["item_01"][likert_levels[index] - 1]["id"]},
                    {"question_id": likert_questions["item_02"]["id"], "option_id": likert_options["item_02"][min(likert_levels[index] + 1, 5) - 1]["id"]},
                    {"question_id": likert_questions["item_03"]["id"], "option_id": likert_options["item_03"][likert_levels[index] - 1]["id"]},
                ],
            },
        )
        response_ids.append(response["response_id"])

    return {
        "project": project,
        "form": form,
        "public_slug": public_slug,
        "responses": response_ids,
        "variables": {"sexo": sexo_variable, "rendimiento": rendimiento_variable},
        "questions": {
            "sexo": sexo_question,
            "ansiedad": ansiedad_question,
            "edad": edad_question,
            "rendimiento": rendimiento_question,
            **likert_questions,
        },
        "instrument": instrument,
        "dimension": dimension,
    }


def test_analysis_orchestrator_end_to_end(client: TestClient):
    fixture = prepare_orchestrator_fixture(client)
    form = fixture["form"]
    questions = fixture["questions"]
    instrument = fixture["instrument"]
    dimension = fixture["dimension"]

    descriptive_response = client.post(
        f"/api/v1/forms/{form['id']}/analysis/run",
        json={
            "analysis_goal": "descriptive_summary",
            "targets": [],
            "method": "auto",
            "store_result": True,
            "options": {"include_recommendations": True},
        },
    )
    assert descriptive_response.status_code == 200
    descriptive_body = descriptive_response.json()
    assert descriptive_body["analysis_run_id"] is not None
    assert descriptive_body["executive_summary"]
    assert descriptive_body["result_blocks"]
    assert descriptive_body["apa_table_blocks"]
    assert descriptive_body["chart_blocks"]
    assert descriptive_body["export_blocks"]

    correlation_response = client.post(
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
    assert correlation_response.status_code == 200
    correlation_body = correlation_response.json()
    block_types = {block["block_type"] for block in correlation_body["result_blocks"]}
    assert {"descriptive", "normality", "decision", "correlation"}.issubset(block_types)

    matrix_response = client.post(
        f"/api/v1/forms/{form['id']}/analysis/run",
        json={
            "analysis_goal": "correlation_matrix",
            "targets": [
                {"target_type": "question", "target_id": questions["edad"]["id"], "role": "target"},
                {"target_type": "question", "target_id": questions["rendimiento"]["id"], "role": "target"},
                {"target_type": "dimension", "target_id": dimension["id"], "role": "target"},
            ],
            "method": "auto",
            "store_result": True,
        },
    )
    assert matrix_response.status_code == 200
    assert matrix_response.json()["chart_blocks"][0]["chart_type"] == "heatmap"

    comparison_response = client.post(
        f"/api/v1/forms/{form['id']}/analysis/run",
        json={
            "analysis_goal": "group_comparison",
            "targets": [
                {"target_type": "question", "target_id": questions["rendimiento"]["id"], "role": "outcome"},
                {"target_type": "question", "target_id": questions["sexo"]["id"], "role": "group"},
            ],
            "method": "auto",
            "store_result": True,
        },
    )
    assert comparison_response.status_code == 200
    comparison_body = comparison_response.json()
    assert comparison_body["plain_language_explanation"]
    assert any(block["block_type"] == "group_comparison" for block in comparison_body["result_blocks"])

    association_response = client.post(
        f"/api/v1/forms/{form['id']}/analysis/run",
        json={
            "analysis_goal": "categorical_association",
            "targets": [
                {"target_type": "question", "target_id": questions["sexo"]["id"], "role": "row"},
                {"target_type": "question", "target_id": questions["ansiedad"]["id"], "role": "column"},
            ],
            "method": "auto",
            "store_result": True,
        },
    )
    assert association_response.status_code == 200
    association_body = association_response.json()
    assert any(block["block_type"] == "categorical_association" for block in association_body["result_blocks"])

    full_scan_response = client.post(
        f"/api/v1/forms/{form['id']}/analysis/full-scan",
        json={
            "alpha": 0.05,
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "store_result": True,
            "options": {"max_targets": 5, "max_pairwise_tests": 2},
        },
    )
    assert full_scan_response.status_code == 200
    full_scan_body = full_scan_response.json()
    assert full_scan_body["executive_summary"]
    assert "pairwise_limit_reached" in full_scan_body["warnings"]

    options_response = client.get(f"/api/v1/forms/{form['id']}/analysis/options")
    assert options_response.status_code == 200
    options_body = options_response.json()
    assert "correlation" in options_body["goals"]
    assert options_body["available_targets"]["numeric"]
    assert options_body["available_targets"]["categorical"]

    summary_response = client.get(f"/api/v1/forms/{form['id']}/analysis/summary")
    assert summary_response.status_code == 200
    summary_body = summary_response.json()
    assert summary_body["total_responses"] == 20
    assert summary_body["available_analyses"]
    assert summary_body["recent_analysis_runs"]

    before_runs = count_orchestrated_runs()
    no_store_response = client.post(
        f"/api/v1/forms/{form['id']}/analysis/run",
        json={
            "analysis_goal": "correlation",
            "targets": [
                {"target_type": "question", "target_id": questions["edad"]["id"], "role": "x"},
                {"target_type": "question", "target_id": questions["rendimiento"]["id"], "role": "y"},
            ],
            "method": "auto",
            "store_result": False,
        },
    )
    assert no_store_response.status_code == 200
    assert no_store_response.json()["analysis_run_id"] is None
    assert count_orchestrated_runs() == before_runs

    empty_project = create_project(client, "Proyecto vacio orquestador")
    empty_form = create_form(client, empty_project["id"], "Formulario vacio orquestador")
    empty_descriptive = client.post(
        f"/api/v1/forms/{empty_form['id']}/analysis/run",
        json={
            "analysis_goal": "descriptive_summary",
            "targets": [],
            "method": "auto",
            "store_result": False,
        },
    )
    assert empty_descriptive.status_code == 200
    assert empty_descriptive.json()["status"] in {"completed_with_warnings", "not_applicable"}
    assert empty_descriptive.json()["warnings"]

    invalid_project = create_project(client, "Proyecto ajeno orquestador")
    invalid_form = create_form(client, invalid_project["id"], "Formulario ajeno orquestador")
    invalid_question = create_question(
        client,
        invalid_form["id"],
        {
            "code": "foreign_num",
            "label": "Foreign num",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 1,
        },
    )
    invalid_response = client.post(
        f"/api/v1/forms/{form['id']}/analysis/run",
        json={
            "analysis_goal": "correlation",
            "targets": [
                {"target_type": "question", "target_id": questions["edad"]["id"], "role": "x"},
                {"target_type": "question", "target_id": invalid_question["id"], "role": "y"},
            ],
            "method": "auto",
            "store_result": False,
        },
    )
    assert invalid_response.status_code == 404

    u_exe = list(Path("E:/Colmena/backend").rglob("u.exe"))
    assert not u_exe
