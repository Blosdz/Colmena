from fastapi.testclient import TestClient


def create_project(client: TestClient) -> dict:
    response = client.post("/api/v1/projects", json={"title": "Proyecto normalidad", "approach": "cuantitativo"})
    assert response.status_code == 201
    return response.json()


def create_project_variable(client: TestClient, project_id: str, payload: dict) -> dict:
    response = client.post(f"/api/v1/projects/{project_id}/variables", json=payload)
    assert response.status_code == 201
    return response.json()


def create_form(client: TestClient, project_id: str, title: str = "Formulario normalidad") -> dict:
    response = client.post(f"/api/v1/projects/{project_id}/forms", json={"title": title, "instructions": "Responder"})
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


def test_normality_end_to_end(client: TestClient):
    project = create_project(client)
    score_variable = create_project_variable(
        client,
        project["id"],
        {
            "name": "Ansiedad",
            "code": "ansiedad",
            "variable_role": "dependent",
            "measurement_level": "ordinal",
            "data_type": "numeric",
        },
    )
    form = create_form(client, project["id"])
    instrument = client.post(
        f"/api/v1/forms/{form['id']}/instruments",
        json={"name": "Escala", "project_variable_id": score_variable["id"], "sort_order": 1},
    ).json()
    dimension = client.post(
        f"/api/v1/form-instruments/{instrument['id']}/dimensions",
        json={"name": "Sintomas", "sort_order": 1},
    ).json()

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
            "sort_order": 1,
        },
    )
    sexo_f = create_option(client, sexo_question["id"], {"label": "Femenino", "value": "F", "sort_order": 1})
    sexo_m = create_option(client, sexo_question["id"], {"label": "Masculino", "value": "M", "sort_order": 2})

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
            "sort_order": 2,
        },
    )
    constante_question = create_question(
        client,
        form["id"],
        {
            "code": "constante",
            "label": "Constante",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 3,
        },
    )
    item_question = create_question(
        client,
        form["id"],
        {
            "code": "item_01",
            "label": "Siento tension academica.",
            "question_type": "likert",
            "question_role": "dimension_item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "instrument_id": instrument["id"],
            "dimension_id": dimension["id"],
            "project_variable_id": score_variable["id"],
            "is_required": True,
            "is_scored": True,
            "sort_order": 4,
        },
    )
    item_options = [
        create_option(
            client,
            item_question["id"],
            {"label": f"Likert {score}", "value": str(score), "score": float(score), "sort_order": score},
        )
        for score in range(1, 6)
    ]
    reverse_question = create_question(
        client,
        form["id"],
        {
            "code": "item_02",
            "label": "Me mantengo calmado.",
            "question_type": "likert",
            "question_role": "dimension_item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "instrument_id": instrument["id"],
            "dimension_id": dimension["id"],
            "project_variable_id": score_variable["id"],
            "is_required": True,
            "is_scored": True,
            "is_reverse_scored": True,
            "sort_order": 5,
        },
    )
    reverse_options = [
        create_option(
            client,
            reverse_question["id"],
            {"label": f"Likert {score}", "value": str(score), "score": float(score), "sort_order": score},
        )
        for score in range(1, 6)
    ]

    publish = client.post(f"/api/v1/forms/{form['id']}/publish")
    assert publish.status_code == 200
    public_slug = publish.json()["public_slug"]

    ages = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
    for index, age in enumerate(ages, start=1):
        response = submit_public_response(
            client,
            public_slug,
            {
                "respondent_code": f"N-{index:03d}",
                "answers": [
                    {"question_id": sexo_question["id"], "option_id": sexo_f["id"] if index % 2 else sexo_m["id"]},
                    {"question_id": edad_question["id"], "value_number": age},
                    {"question_id": constante_question["id"], "value_number": 5},
                    {"question_id": item_question["id"], "option_id": item_options[(index - 1) % 5]["id"]},
                    {"question_id": reverse_question["id"], "option_id": reverse_options[(index - 1) % 5]["id"]},
                ],
            },
        )
        assert response["response_id"]

    report = client.get(f"/api/v1/forms/{form['id']}/normality?method=auto&alpha=0.05&decimals=3")
    assert report.status_code == 200
    report_body = report.json()
    assert report_body["form_id"] == form["id"]
    assert report_body["total_targets"] >= 5
    assert report_body["results"]
    numeric_question_result = next(item for item in report_body["results"] if item["target_id"] == edad_question["id"])
    assert numeric_question_result["method"] == "shapiro"
    assert numeric_question_result["classification"] in {"normal", "non_normal", "inconclusive", "not_applicable"}

    categorical_result = client.get(f"/api/v1/forms/{form['id']}/normality/questions/{sexo_question['id']}")
    assert categorical_result.status_code == 200
    assert categorical_result.json()["classification"] == "not_applicable"

    question_result = client.get(f"/api/v1/forms/{form['id']}/normality/questions/{item_question['id']}")
    assert question_result.status_code == 200
    assert question_result.json()["valid_n"] == 10

    dimensions = client.get(f"/api/v1/forms/{form['id']}/normality/dimensions")
    assert dimensions.status_code == 200
    assert dimensions.json()["results"][0]["target_type"] == "dimension"

    instruments = client.get(f"/api/v1/forms/{form['id']}/normality/instruments")
    assert instruments.status_code == 200
    assert instruments.json()["results"][0]["target_type"] == "instrument"

    project_variables = client.get(f"/api/v1/forms/{form['id']}/normality/project-variables")
    assert project_variables.status_code == 200
    assert any(item["target_type"] == "project_variable" for item in project_variables.json()["results"])

    constant_result = client.get(f"/api/v1/forms/{form['id']}/normality/questions/{constante_question['id']}")
    assert constant_result.status_code == 200
    assert constant_result.json()["classification"] in {"not_applicable", "inconclusive"}
    assert "constant_values" in constant_result.json()["warnings"]

    responses_list = client.get(f"/api/v1/forms/{form['id']}/responses").json()["items"]
    discard_target = responses_list[0]
    discard = client.patch(f"/api/v1/form-responses/{discard_target['id']}/status", json={"status": "discarded"})
    assert discard.status_code == 200

    without_discarded = client.get(f"/api/v1/forms/{form['id']}/normality/questions/{item_question['id']}")
    assert without_discarded.status_code == 200
    assert without_discarded.json()["valid_n"] == 9

    with_discarded = client.get(
        f"/api/v1/forms/{form['id']}/normality/questions/{item_question['id']}?include_discarded=true"
    )
    assert with_discarded.status_code == 200
    assert with_discarded.json()["valid_n"] == 10

    run_response = client.post(
        f"/api/v1/forms/{form['id']}/normality/run",
        json={
            "method": "auto",
            "alpha": 0.05,
            "decimals": 3,
            "include_discarded": False,
            "score_aggregation": "mean",
            "store_result": True,
        },
    )
    assert run_response.status_code == 200
    assert run_response.json()["analysis_run_id"] is not None

    low_n_form = create_form(client, project["id"], title="Formulario low n")
    low_n_question = create_question(
        client,
        low_n_form["id"],
        {
            "code": "x",
            "label": "X",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 1,
        },
    )
    low_publish = client.post(f"/api/v1/forms/{low_n_form['id']}/publish")
    assert low_publish.status_code == 200
    low_slug = low_publish.json()["public_slug"]
    submit_public_response(
        client,
        low_slug,
        {"answers": [{"question_id": low_n_question["id"], "value_number": 10}]},
    )
    submit_public_response(
        client,
        low_slug,
        {"answers": [{"question_id": low_n_question["id"], "value_number": 11}]},
    )
    low_n_result = client.get(f"/api/v1/forms/{low_n_form['id']}/normality/questions/{low_n_question['id']}")
    assert low_n_result.status_code == 200
    assert low_n_result.json()["classification"] == "not_applicable"
    assert "insufficient_n" in low_n_result.json()["warnings"]
