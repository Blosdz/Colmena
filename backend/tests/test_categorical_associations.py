from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models.analysis_run import AnalysisRun


def create_project(client: TestClient, title: str = "Proyecto asociacion") -> dict:
    response = client.post("/api/v1/projects", json={"title": title, "approach": "cuantitativo"})
    assert response.status_code == 201
    return response.json()


def create_project_variable(client: TestClient, project_id: str, payload: dict) -> dict:
    response = client.post(f"/api/v1/projects/{project_id}/variables", json=payload)
    assert response.status_code == 201
    return response.json()


def create_form(client: TestClient, project_id: str, title: str = "Formulario asociacion") -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/forms",
        json={"title": title, "instructions": "Responder"},
    )
    assert response.status_code == 201
    return response.json()


def create_question(client: TestClient, form_id: str, payload: dict) -> dict:
    response = client.post(f"/api/v1/forms/{form_id}/questions", json=payload)
    assert response.status_code == 201
    return response.json()


def create_option(client: TestClient, question_id: str, payload: dict) -> dict:
    response = client.post(f"/api/v1/form-questions/{question_id}/options", json=payload)
    assert response.status_code == 201
    return response.json()


def submit_public_response(client: TestClient, public_slug: str, payload: dict) -> dict:
    response = client.post(f"/api/public/forms/{public_slug}/responses", json=payload)
    assert response.status_code == 201
    return response.json()


def count_analysis_runs() -> int:
    with SessionLocal() as session:
        return int(session.scalar(select(func.count()).select_from(AnalysisRun)) or 0)


def prepare_association_fixture(client: TestClient) -> dict:
    project = create_project(client)
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

    form = create_form(client, project["id"])

    sexo_question = create_question(
        client,
        form["id"],
        {
            "code": "sexo",
            "label": "Sexo",
            "question_type": "single_choice",
            "question_role": "sociodemographic",
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
            "code": "ansiedad_nivel",
            "label": "Nivel de ansiedad",
            "question_type": "single_choice",
            "question_role": "variable_item",
            "measurement_level": "ordinal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 2,
        },
    )
    procedencia_question = create_question(
        client,
        form["id"],
        {
            "code": "procedencia",
            "label": "Procedencia",
            "question_type": "single_choice",
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 3,
        },
    )
    beca_question = create_question(
        client,
        form["id"],
        {
            "code": "beca",
            "label": "Beca activa",
            "question_type": "boolean",
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 4,
        },
    )
    ingreso_question = create_question(
        client,
        form["id"],
        {
            "code": "ingreso",
            "label": "Ingreso mensual",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "min_value": 500,
            "max_value": 5000,
            "sort_order": 5,
        },
    )
    unica_question = create_question(
        client,
        form["id"],
        {
            "code": "categoria_unica",
            "label": "Categoria unica",
            "question_type": "single_choice",
            "question_role": "variable_item",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 6,
        },
    )

    sexo_f = create_option(client, sexo_question["id"], {"label": "Femenino", "value": "F", "sort_order": 1})
    sexo_m = create_option(client, sexo_question["id"], {"label": "Masculino", "value": "M", "sort_order": 2})

    ansiedad_bajo = create_option(client, ansiedad_question["id"], {"label": "Bajo", "value": "bajo", "sort_order": 1})
    ansiedad_medio = create_option(client, ansiedad_question["id"], {"label": "Medio", "value": "medio", "sort_order": 2})
    ansiedad_alto = create_option(client, ansiedad_question["id"], {"label": "Alto", "value": "alto", "sort_order": 3})

    proc_costa = create_option(client, procedencia_question["id"], {"label": "Costa", "value": "costa", "sort_order": 1})
    proc_sierra = create_option(client, procedencia_question["id"], {"label": "Sierra", "value": "sierra", "sort_order": 2})
    proc_selva = create_option(client, procedencia_question["id"], {"label": "Selva", "value": "selva", "sort_order": 3})
    proc_ext = create_option(client, procedencia_question["id"], {"label": "Extranjero", "value": "extranjero", "sort_order": 4})

    beca_si = create_option(client, beca_question["id"], {"label": "Si", "value": "si", "sort_order": 1})
    beca_no = create_option(client, beca_question["id"], {"label": "No", "value": "no", "sort_order": 2})

    unica_a = create_option(client, unica_question["id"], {"label": "A", "value": "A", "sort_order": 1})
    unica_b = create_option(client, unica_question["id"], {"label": "B", "value": "B", "sort_order": 2})

    publish = client.post(f"/api/v1/forms/{form['id']}/publish")
    assert publish.status_code == 200
    public_slug = publish.json()["public_slug"]

    sexes = [sexo_f["id"]] * 10 + [sexo_m["id"]] * 10
    anxiety = [
        ansiedad_bajo["id"],
        ansiedad_bajo["id"],
        ansiedad_bajo["id"],
        ansiedad_medio["id"],
        ansiedad_medio["id"],
        ansiedad_medio["id"],
        ansiedad_alto["id"],
        ansiedad_alto["id"],
        ansiedad_alto["id"],
        ansiedad_alto["id"],
        ansiedad_bajo["id"],
        ansiedad_bajo["id"],
        ansiedad_medio["id"],
        ansiedad_medio["id"],
        ansiedad_medio["id"],
        ansiedad_alto["id"],
        ansiedad_alto["id"],
        ansiedad_alto["id"],
        ansiedad_alto["id"],
        ansiedad_alto["id"],
    ]
    procedencias = [
        proc_costa["id"],
        proc_sierra["id"],
        proc_selva["id"],
        proc_ext["id"],
        proc_costa["id"],
        proc_sierra["id"],
        proc_selva["id"],
        proc_ext["id"],
        proc_costa["id"],
        proc_sierra["id"],
        proc_selva["id"],
        proc_ext["id"],
        proc_costa["id"],
        proc_sierra["id"],
        proc_selva["id"],
        proc_ext["id"],
        proc_costa["id"],
        proc_sierra["id"],
        proc_selva["id"],
        proc_ext["id"],
    ]
    becas = [beca_si["id"]] + ([beca_no["id"]] * 9) + ([beca_no["id"]] * 10)
    ingresos = [1200 + index * 50 for index in range(20)]

    response_ids: list[str] = []
    for index in range(20):
        response = submit_public_response(
            client,
            public_slug,
            {
                "respondent_code": f"A-{index + 1:03d}",
                "answers": [
                    {"question_id": sexo_question["id"], "option_id": sexes[index]},
                    {"question_id": ansiedad_question["id"], "option_id": anxiety[index]},
                    {"question_id": procedencia_question["id"], "option_id": procedencias[index]},
                    {"question_id": beca_question["id"], "option_id": becas[index]},
                    {"question_id": ingreso_question["id"], "value_number": ingresos[index]},
                    {"question_id": unica_question["id"], "option_id": unica_a["id"]},
                ],
            },
        )
        response_ids.append(response["response_id"])

    return {
        "project": project,
        "form": form,
        "public_slug": public_slug,
        "responses": response_ids,
        "variables": {"sexo": sexo_variable},
        "questions": {
            "sexo": sexo_question,
            "ansiedad": ansiedad_question,
            "procedencia": procedencia_question,
            "beca": beca_question,
            "ingreso": ingreso_question,
            "unica": unica_question,
        },
    }


def test_categorical_associations_end_to_end(client: TestClient):
    fixture = prepare_association_fixture(client)
    form = fixture["form"]
    questions = fixture["questions"]
    variables = fixture["variables"]

    chi_response = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": questions["ansiedad"]["id"]},
            "method": "chi_square",
            "store_result": True,
        },
    )
    assert chi_response.status_code == 200
    chi_body = chi_response.json()
    assert chi_body["analysis_run_id"] is not None
    assert chi_body["result"]["method_used"] == "chi_square"
    assert chi_body["result"]["statistic"] is not None
    assert chi_body["result"]["degrees_of_freedom"] == 2
    assert chi_body["result"]["p_value"] is not None
    assert chi_body["result"]["observed_table"]
    assert chi_body["result"]["expected_table"]
    assert len(chi_body["result"]["cells"]) == 6
    assert chi_body["result"]["effect_size"]["name"] == "cramers_v"
    assert chi_body["result"]["interpretation"]
    assert "association_not_causation" in chi_body["result"]["warnings"]

    auto_before = count_analysis_runs()
    auto_response = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": questions["beca"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert auto_response.status_code == 200
    auto_body = auto_response.json()
    assert auto_body["analysis_run_id"] is None
    assert auto_body["result"]["method_used"] == "fisher_exact"
    assert auto_body["result"]["odds_ratio"] is not None
    assert auto_body["result"]["effect_size"]["name"] == "phi"
    assert "method_auto_selected" in auto_body["result"]["warnings"]
    assert "expected_counts_low" in auto_body["result"]["warnings"]
    assert count_analysis_runs() == auto_before

    fisher_response = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": questions["beca"]["id"]},
            "method": "fisher_exact",
            "store_result": False,
        },
    )
    assert fisher_response.status_code == 200
    fisher_body = fisher_response.json()
    assert fisher_body["result"]["method_used"] == "fisher_exact"
    assert fisher_body["result"]["odds_ratio"] is not None

    fisher_invalid = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": questions["ansiedad"]["id"]},
            "method": "fisher_exact",
            "store_result": False,
        },
    )
    assert fisher_invalid.status_code == 200
    fisher_invalid_body = fisher_invalid.json()
    assert fisher_invalid_body["result"]["classification"] == "not_applicable"
    assert "fisher_only_for_2x2" in fisher_invalid_body["result"]["warnings"]

    discard_response = client.patch(
        f"/api/v1/form-responses/{fixture['responses'][0]}/status",
        json={"status": "discarded"},
    )
    assert discard_response.status_code == 200

    without_discarded = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": questions["ansiedad"]["id"]},
            "method": "chi_square",
            "store_result": False,
        },
    )
    assert without_discarded.status_code == 200
    assert without_discarded.json()["result"]["valid_n"] == 19

    with_discarded = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": questions["ansiedad"]["id"]},
            "method": "chi_square",
            "include_discarded": True,
            "store_result": False,
        },
    )
    assert with_discarded.status_code == 200
    assert with_discarded.json()["result"]["valid_n"] == 20

    non_categorical = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["ingreso"]["id"]},
            "column": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert non_categorical.status_code == 200
    assert non_categorical.json()["result"]["classification"] == "not_applicable"

    one_category = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["unica"]["id"]},
            "column": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert one_category.status_code == 200
    assert one_category.json()["result"]["classification"] == "not_applicable"
    assert "only_one_category" in one_category.json()["result"]["warnings"]

    options_response = client.get(f"/api/v1/forms/{form['id']}/categorical-associations/options")
    assert options_response.status_code == 200
    options_body = options_response.json()
    assert options_body["form_id"] == form["id"]
    option_keys = {(item["target_type"], item["target_id"]) for item in options_body["categorical_targets"]}
    assert ("question", questions["sexo"]["id"]) in option_keys
    assert ("project_variable", variables["sexo"]["id"]) in option_keys

    project_variable_assoc = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "project_variable", "target_id": variables["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": questions["ansiedad"]["id"]},
            "method": "chi_square",
            "store_result": False,
        },
    )
    assert project_variable_assoc.status_code == 200
    assert project_variable_assoc.json()["result"]["method_used"] == "chi_square"

    foreign_project = create_project(client, "Proyecto ajeno asociacion")
    foreign_form = create_form(client, foreign_project["id"], "Formulario ajeno asociacion")
    foreign_question = create_question(
        client,
        foreign_form["id"],
        {
            "code": "foreign_cat",
            "label": "Foreign cat",
            "question_type": "single_choice",
            "question_role": "variable_item",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 1,
        },
    )
    create_option(client, foreign_question["id"], {"label": "A", "value": "A", "sort_order": 1})
    create_option(client, foreign_question["id"], {"label": "B", "value": "B", "sort_order": 2})

    foreign_response = client.post(
        f"/api/v1/forms/{form['id']}/categorical-associations",
        json={
            "row": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "column": {"target_type": "question", "target_id": foreign_question["id"]},
            "method": "chi_square",
            "store_result": False,
        },
    )
    assert foreign_response.status_code == 404
