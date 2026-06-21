from fastapi.testclient import TestClient


def create_project(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={"title": "Proyecto descriptivos", "approach": "cuantitativo"},
    )
    assert response.status_code == 201
    return response.json()


def create_project_variable(client: TestClient, project_id: str, payload: dict) -> dict:
    response = client.post(f"/api/v1/projects/{project_id}/variables", json=payload)
    assert response.status_code == 201
    return response.json()


def create_form(client: TestClient, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/forms",
        json={"title": "Formulario descriptivo", "instructions": "Responder"},
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


def test_descriptive_engine_end_to_end(client: TestClient):
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
    ansiedad_variable = create_project_variable(
        client,
        project["id"],
        {
            "name": "Ansiedad academica",
            "code": "ansiedad",
            "variable_role": "dependent",
            "measurement_level": "ordinal",
            "data_type": "numeric",
        },
    )

    form = create_form(client, project["id"])
    instrumento = client.post(
        f"/api/v1/forms/{form['id']}/instruments",
        json={
            "name": "Escala de ansiedad",
            "acronym": "EA",
            "project_variable_id": ansiedad_variable["id"],
            "sort_order": 1,
        },
    )
    assert instrumento.status_code == 201
    instrument = instrumento.json()

    dimension_response = client.post(
        f"/api/v1/form-instruments/{instrument['id']}/dimensions",
        json={"name": "Sintomas", "sort_order": 1},
    )
    assert dimension_response.status_code == 201
    dimension = dimension_response.json()

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
            "is_required": True,
            "project_variable_id": sexo_variable["id"],
            "sort_order": 1,
        },
    )
    sexo_f = create_option(client, sexo_question["id"], {"label": "Femenino", "value": "F", "sort_order": 1})
    sexo_m = create_option(client, sexo_question["id"], {"label": "Masculino", "value": "M", "sort_order": 2})

    modalidad_question = create_question(
        client,
        form["id"],
        {
            "code": "modalidad",
            "label": "Modalidad",
            "question_type": "single_choice",
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 2,
        },
    )
    modalidad_p = create_option(
        client,
        modalidad_question["id"],
        {"label": "Presencial", "value": "presencial", "sort_order": 1},
    )
    modalidad_v = create_option(
        client,
        modalidad_question["id"],
        {"label": "Virtual", "value": "virtual", "sort_order": 2},
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
            "max_value": 65,
            "sort_order": 3,
        },
    )

    item_01 = create_question(
        client,
        form["id"],
        {
            "code": "item_01",
            "label": "Siento nervios antes de rendir examenes.",
            "question_type": "likert",
            "question_role": "dimension_item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "instrument_id": instrument["id"],
            "dimension_id": dimension["id"],
            "project_variable_id": ansiedad_variable["id"],
            "is_required": True,
            "is_scored": True,
            "sort_order": 4,
        },
    )
    item_01_options = [
        create_option(
            client,
            item_01["id"],
            {"label": f"Likert {score}", "value": str(score), "score": float(score), "sort_order": score},
        )
        for score in range(1, 6)
    ]

    item_02 = create_question(
        client,
        form["id"],
        {
            "code": "item_02",
            "label": "Me mantengo calmado en evaluaciones.",
            "question_type": "likert",
            "question_role": "dimension_item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "instrument_id": instrument["id"],
            "dimension_id": dimension["id"],
            "project_variable_id": ansiedad_variable["id"],
            "is_required": True,
            "is_scored": True,
            "is_reverse_scored": True,
            "sort_order": 5,
        },
    )
    item_02_options = [
        create_option(
            client,
            item_02["id"],
            {"label": f"Likert {score}", "value": str(score), "score": float(score), "sort_order": score},
        )
        for score in range(1, 6)
    ]

    publish_response = client.post(f"/api/v1/forms/{form['id']}/publish")
    assert publish_response.status_code == 200
    public_slug = publish_response.json()["public_slug"]

    responses = [
        {"sexo": sexo_f["id"], "modalidad": modalidad_p["id"], "edad": 20, "item_01": item_01_options[0]["id"], "item_02": item_02_options[0]["id"]},
        {"sexo": sexo_m["id"], "modalidad": modalidad_v["id"], "edad": 22, "item_01": item_01_options[1]["id"], "item_02": item_02_options[1]["id"]},
        {"sexo": sexo_f["id"], "modalidad": modalidad_v["id"], "edad": 24, "item_01": item_01_options[2]["id"], "item_02": item_02_options[2]["id"]},
        {"sexo": sexo_f["id"], "modalidad": modalidad_p["id"], "edad": 26, "item_01": item_01_options[3]["id"], "item_02": item_02_options[3]["id"]},
        {"sexo": sexo_m["id"], "modalidad": modalidad_p["id"], "edad": 28, "item_01": item_01_options[4]["id"], "item_02": item_02_options[4]["id"]},
    ]

    created_responses: list[dict] = []
    for index, payload in enumerate(responses, start=1):
        created_responses.append(
            submit_public_response(
                client,
                public_slug,
                {
                    "respondent_code": f"R-{index:03d}",
                    "answers": [
                        {"question_id": sexo_question["id"], "option_id": payload["sexo"]},
                        {"question_id": modalidad_question["id"], "option_id": payload["modalidad"]},
                        {"question_id": edad_question["id"], "value_number": payload["edad"]},
                        {"question_id": item_01["id"], "option_id": payload["item_01"]},
                        {"question_id": item_02["id"], "option_id": payload["item_02"]},
                    ],
                },
            )
        )

    overview = client.get(f"/api/v1/forms/{form['id']}/descriptives/overview")
    assert overview.status_code == 200
    overview_body = overview.json()
    assert overview_body["total_responses"] == 5
    assert overview_body["included_responses"] == 5

    full_report = client.get(f"/api/v1/forms/{form['id']}/descriptives?decimals=3&score_aggregation=mean")
    assert full_report.status_code == 200
    report_body = full_report.json()
    question_map = {item["code"]: item for item in report_body["questions"]}
    assert len(question_map["sexo"]["frequencies"]) == 2
    sexo_freq = {row["label"]: row["frequency"] for row in question_map["sexo"]["frequencies"]}
    assert sexo_freq["Femenino"] == 3
    assert sexo_freq["Masculino"] == 2
    assert question_map["edad"]["numeric"]["mean"] == 24.0
    assert question_map["item_01"]["numeric"]["mean"] == 3.0
    assert question_map["item_02"]["numeric"]["mean"] == 3.0

    question_descriptive = client.get(
        f"/api/v1/forms/{form['id']}/descriptives/questions/{item_01['id']}?decimals=3"
    )
    assert question_descriptive.status_code == 200
    assert question_descriptive.json()["numeric"]["median"] == 3.0

    dimensions = client.get(
        f"/api/v1/forms/{form['id']}/descriptives/dimensions?score_aggregation=mean"
    )
    assert dimensions.status_code == 200
    dimension_item = dimensions.json()["items"][0]
    assert dimension_item["scored_item_count"] == 2
    assert dimension_item["numeric"]["mean"] == 3.0

    instruments = client.get(
        f"/api/v1/forms/{form['id']}/descriptives/instruments?score_aggregation=mean"
    )
    assert instruments.status_code == 200
    instrument_item = instruments.json()["items"][0]
    assert instrument_item["scored_item_count"] == 2
    assert instrument_item["numeric"]["mean"] == 3.0

    project_variables = client.get(f"/api/v1/forms/{form['id']}/descriptives/project-variables")
    assert project_variables.status_code == 200
    variable_items = {item["name"]: item for item in project_variables.json()["items"]}
    assert variable_items["Sexo"]["frequencies"][0]["frequency"] >= 1
    assert variable_items["Ansiedad academica"]["numeric"]["mean"] == 3.0

    crosstab = client.get(
        f"/api/v1/forms/{form['id']}/descriptives/crosstab?row_question_id={sexo_question['id']}&column_question_id={modalidad_question['id']}"
    )
    assert crosstab.status_code == 200
    crosstab_body = crosstab.json()
    assert crosstab_body["total_n"] == 5
    assert len(crosstab_body["cells"]) == 4
    cell_map = {(cell["row_value"], cell["column_value"]): cell["count"] for cell in crosstab_body["cells"]}
    assert cell_map[("Femenino", "Presencial")] == 2
    assert cell_map[("Masculino", "Virtual")] == 1

    discard_response = client.patch(
        f"/api/v1/form-responses/{created_responses[4]['response_id']}/status",
        json={"status": "discarded"},
    )
    assert discard_response.status_code == 200

    overview_without_discarded = client.get(f"/api/v1/forms/{form['id']}/descriptives/overview")
    assert overview_without_discarded.status_code == 200
    assert overview_without_discarded.json()["included_responses"] == 4

    overview_with_discarded = client.get(
        f"/api/v1/forms/{form['id']}/descriptives/overview?include_discarded=true"
    )
    assert overview_with_discarded.status_code == 200
    assert overview_with_discarded.json()["included_responses"] == 5

    empty_form = create_form(client, project["id"])
    empty_overview = client.get(f"/api/v1/forms/{empty_form['id']}/descriptives/overview")
    assert empty_overview.status_code == 200
    assert "no_responses" in empty_overview.json()["warnings"]

    empty_report = client.get(f"/api/v1/forms/{empty_form['id']}/descriptives")
    assert empty_report.status_code == 200
    assert empty_report.json()["overview"]["included_responses"] == 0

    run_response = client.post(
        f"/api/v1/forms/{form['id']}/descriptives/run",
        json={
            "include_discarded": False,
            "decimals": 3,
            "score_aggregation": "mean",
            "store_result": True,
        },
    )
    assert run_response.status_code == 200
    run_body = run_response.json()
    assert run_body["stored"] is True
    assert run_body["analysis_run"] is not None
    assert run_body["analysis_run"]["analysis_type"] == "descriptive"
