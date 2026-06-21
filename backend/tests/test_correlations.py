from fastapi.testclient import TestClient


def create_project(client: TestClient, title: str = "Proyecto correlaciones") -> dict:
    response = client.post("/api/v1/projects", json={"title": title, "approach": "cuantitativo"})
    assert response.status_code == 201
    return response.json()


def create_project_variable(client: TestClient, project_id: str, payload: dict) -> dict:
    response = client.post(f"/api/v1/projects/{project_id}/variables", json=payload)
    assert response.status_code == 201
    return response.json()


def create_form(client: TestClient, project_id: str, title: str = "Formulario correlaciones") -> dict:
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


def prepare_correlation_fixture(client: TestClient) -> dict:
    project = create_project(client)
    age_variable = create_project_variable(
        client,
        project["id"],
        {
            "name": "Edad",
            "code": "edad",
            "variable_role": "control",
            "measurement_level": "ratio",
            "data_type": "numeric",
        },
    )
    performance_variable = create_project_variable(
        client,
        project["id"],
        {
            "name": "Rendimiento",
            "code": "rendimiento",
            "variable_role": "outcome",
            "measurement_level": "ratio",
            "data_type": "numeric",
        },
    )
    anxiety_variable = create_project_variable(
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
    stress_variable = create_project_variable(
        client,
        project["id"],
        {
            "name": "Estres academico",
            "code": "estres",
            "variable_role": "dependent",
            "measurement_level": "ordinal",
            "data_type": "numeric",
        },
    )

    form = create_form(client, project["id"])

    instrument_1 = client.post(
        f"/api/v1/forms/{form['id']}/instruments",
        json={"name": "Escala de Ansiedad", "project_variable_id": anxiety_variable["id"], "sort_order": 1},
    )
    assert instrument_1.status_code == 201
    instrument_1 = instrument_1.json()

    instrument_2 = client.post(
        f"/api/v1/forms/{form['id']}/instruments",
        json={"name": "Escala de Estres", "project_variable_id": stress_variable["id"], "sort_order": 2},
    )
    assert instrument_2.status_code == 201
    instrument_2 = instrument_2.json()

    dimension_1 = client.post(
        f"/api/v1/form-instruments/{instrument_1['id']}/dimensions",
        json={"name": "Cognitiva", "sort_order": 1},
    )
    assert dimension_1.status_code == 201
    dimension_1 = dimension_1.json()

    dimension_2 = client.post(
        f"/api/v1/form-instruments/{instrument_1['id']}/dimensions",
        json={"name": "Somatica", "sort_order": 2},
    )
    assert dimension_2.status_code == 201
    dimension_2 = dimension_2.json()

    dimension_3 = client.post(
        f"/api/v1/form-instruments/{instrument_2['id']}/dimensions",
        json={"name": "Sobrecarga", "sort_order": 1},
    )
    assert dimension_3.status_code == 201
    dimension_3 = dimension_3.json()

    age_question = create_question(
        client,
        form["id"],
        {
            "code": "edad",
            "label": "Edad",
            "question_type": "number",
            "question_role": "sociodemographic",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "project_variable_id": age_variable["id"],
            "is_required": True,
            "min_value": 18,
            "max_value": 65,
            "sort_order": 1,
        },
    )
    performance_question = create_question(
        client,
        form["id"],
        {
            "code": "rendimiento",
            "label": "Rendimiento academico",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "project_variable_id": performance_variable["id"],
            "is_required": True,
            "min_value": 0,
            "max_value": 100,
            "sort_order": 2,
        },
    )
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
            "sort_order": 3,
        },
    )
    sexo_f = create_option(client, sexo_question["id"], {"label": "Femenino", "value": "F", "sort_order": 1})
    sexo_m = create_option(client, sexo_question["id"], {"label": "Masculino", "value": "M", "sort_order": 2})

    likert_configs = [
        ("anx_item_01", "Me preocupa mi rendimiento.", instrument_1["id"], dimension_1["id"], anxiety_variable["id"], False, 4),
        ("anx_item_02", "Me siento tranquilo ante examenes.", instrument_1["id"], dimension_1["id"], anxiety_variable["id"], True, 5),
        ("anx_item_03", "Siento tension fisica.", instrument_1["id"], dimension_2["id"], anxiety_variable["id"], False, 6),
        ("stress_item_01", "La carga academica me supera.", instrument_2["id"], dimension_3["id"], stress_variable["id"], False, 7),
        ("stress_item_02", "Tengo poco tiempo para descansar.", instrument_2["id"], dimension_3["id"], stress_variable["id"], False, 8),
    ]
    questions: dict[str, dict] = {}
    options: dict[str, list[dict]] = {}

    for code, label, instrument_id, dimension_id, variable_id, reverse, sort_order in likert_configs:
        question = create_question(
            client,
            form["id"],
            {
                "code": code,
                "label": label,
                "question_type": "likert",
                "question_role": "dimension_item",
                "measurement_level": "ordinal",
                "data_type": "numeric",
                "instrument_id": instrument_id,
                "dimension_id": dimension_id,
                "project_variable_id": variable_id,
                "is_required": True,
                "is_scored": True,
                "is_reverse_scored": reverse,
                "sort_order": sort_order,
            },
        )
        questions[code] = question
        options[code] = [
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

    ages = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    performance = [58, 60, 61, 63, 64, 66, 67, 69, 71, 72, 74, 76]
    anxiety_pattern = [1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
    stress_pattern = [2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5]

    response_ids: list[str] = []
    for index in range(12):
        response = submit_public_response(
            client,
            public_slug,
            {
                "respondent_code": f"C-{index + 1:03d}",
                "answers": [
                    {
                        "question_id": age_question["id"],
                        "value_number": ages[index],
                    },
                    {
                        "question_id": performance_question["id"],
                        "value_number": performance[index],
                    },
                    {
                        "question_id": sexo_question["id"],
                        "option_id": sexo_f["id"] if index % 2 == 0 else sexo_m["id"],
                    },
                    {
                        "question_id": questions["anx_item_01"]["id"],
                        "option_id": options["anx_item_01"][anxiety_pattern[index] - 1]["id"],
                    },
                    {
                        "question_id": questions["anx_item_02"]["id"],
                        "option_id": options["anx_item_02"][anxiety_pattern[index] - 1]["id"],
                    },
                    {
                        "question_id": questions["anx_item_03"]["id"],
                        "option_id": options["anx_item_03"][min(anxiety_pattern[index] + 1, 5) - 1]["id"],
                    },
                    {
                        "question_id": questions["stress_item_01"]["id"],
                        "option_id": options["stress_item_01"][stress_pattern[index] - 1]["id"],
                    },
                    {
                        "question_id": questions["stress_item_02"]["id"],
                        "option_id": options["stress_item_02"][min(stress_pattern[index] + 1, 5) - 1]["id"],
                    },
                ],
            },
        )
        response_ids.append(response["response_id"])

    return {
        "project": project,
        "form": form,
        "public_slug": public_slug,
        "responses": response_ids,
        "variables": {
            "age": age_variable,
            "performance": performance_variable,
            "anxiety": anxiety_variable,
            "stress": stress_variable,
        },
        "questions": {
            "age": age_question,
            "performance": performance_question,
            "sexo": sexo_question,
            **questions,
        },
        "dimensions": {
            "cognitiva": dimension_1,
            "somatica": dimension_2,
            "sobrecarga": dimension_3,
        },
        "instruments": {
            "anxiety": instrument_1,
            "stress": instrument_2,
        },
    }


def test_correlations_end_to_end(client: TestClient):
    fixture = prepare_correlation_fixture(client)
    form = fixture["form"]
    questions = fixture["questions"]
    dimensions = fixture["dimensions"]
    instruments = fixture["instruments"]
    variables = fixture["variables"]

    pearson_response = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["age"]["id"]},
            "y": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "method": "pearson",
            "store_result": True,
        },
    )
    assert pearson_response.status_code == 200
    pearson_body = pearson_response.json()
    assert pearson_body["analysis_run_id"] is not None
    assert pearson_body["result"]["method_used"] == "pearson"
    assert pearson_body["result"]["valid_n"] == 12
    assert pearson_body["result"]["coefficient"] is not None
    assert pearson_body["result"]["p_value"] is not None
    assert pearson_body["result"]["null_hypothesis"]
    assert pearson_body["result"]["alternative_hypothesis"]
    assert pearson_body["result"]["method_justification"]

    spearman_response = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["anx_item_01"]["id"]},
            "y": {"target_type": "question", "target_id": questions["anx_item_03"]["id"]},
            "method": "spearman",
            "store_result": False,
        },
    )
    assert spearman_response.status_code == 200
    spearman_body = spearman_response.json()
    assert spearman_body["analysis_run_id"] is None
    assert spearman_body["result"]["method_used"] == "spearman"
    assert spearman_body["result"]["interpretation"]
    assert "correlation_not_causation" in spearman_body["result"]["warnings"]

    kendall_response = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["anx_item_01"]["id"]},
            "y": {"target_type": "question", "target_id": questions["anx_item_03"]["id"]},
            "method": "kendall",
            "store_result": False,
        },
    )
    assert kendall_response.status_code == 200
    assert kendall_response.json()["result"]["method_used"] == "kendall"

    auto_response = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["anx_item_01"]["id"]},
            "y": {"target_type": "question", "target_id": questions["anx_item_03"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert auto_response.status_code == 200
    auto_body = auto_response.json()
    # Par ordinal (Likert) con muchos empates y muestra pequeña (n < 30): la selección
    # automática prefiere Kendall, más robusta que Spearman en estas condiciones.
    assert auto_body["result"]["method_used"] == "kendall"
    assert "method_auto_selected" in auto_body["result"]["warnings"]
    assert "many_ties" in auto_body["result"]["warnings"]

    matrix_response = client.post(
        f"/api/v1/forms/{form['id']}/correlations/matrix",
        json={
            "targets": [
                {"target_type": "question", "target_id": questions["age"]["id"]},
                {"target_type": "question", "target_id": questions["performance"]["id"]},
                {"target_type": "dimension", "target_id": dimensions["cognitiva"]["id"]},
            ],
            "method": "auto",
            "store_result": True,
        },
    )
    assert matrix_response.status_code == 200
    matrix_body = matrix_response.json()
    assert matrix_body["analysis_run_id"] is not None
    assert len(matrix_body["cells"]) == 9

    dimension_matrix = client.get(
        f"/api/v1/forms/{form['id']}/correlations/instruments/{instruments['anxiety']['id']}/dimensions?method=auto"
    )
    assert dimension_matrix.status_code == 200
    assert len(dimension_matrix.json()["targets"]) == 2
    assert len(dimension_matrix.json()["cells"]) == 4

    instruments_matrix = client.get(f"/api/v1/forms/{form['id']}/correlations/instruments?method=auto")
    assert instruments_matrix.status_code == 200
    assert len(instruments_matrix.json()["targets"]) == 2
    assert len(instruments_matrix.json()["cells"]) == 4

    variables_matrix = client.get(f"/api/v1/forms/{form['id']}/correlations/project-variables?method=auto")
    assert variables_matrix.status_code == 200
    assert len(variables_matrix.json()["targets"]) == 4
    assert len(variables_matrix.json()["cells"]) == 16

    discard_response = client.patch(
        f"/api/v1/form-responses/{fixture['responses'][0]}/status",
        json={"status": "discarded"},
    )
    assert discard_response.status_code == 200

    without_discarded = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["age"]["id"]},
            "y": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "method": "pearson",
            "store_result": False,
        },
    )
    assert without_discarded.status_code == 200
    assert without_discarded.json()["result"]["valid_n"] == 11

    with_discarded = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["age"]["id"]},
            "y": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "method": "pearson",
            "include_discarded": True,
            "store_result": False,
        },
    )
    assert with_discarded.status_code == 200
    assert with_discarded.json()["result"]["valid_n"] == 12

    categorical_pair = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "y": {"target_type": "question", "target_id": questions["age"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert categorical_pair.status_code == 200
    assert categorical_pair.json()["result"]["classification"] == "not_applicable"

    constant_project = create_project(client, "Proyecto constante")
    constant_form = create_form(client, constant_project["id"], "Formulario constante")
    constant_question = create_question(
        client,
        constant_form["id"],
        {
            "code": "cte",
            "label": "Constante",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 1,
        },
    )
    variable_question = create_question(
        client,
        constant_form["id"],
        {
            "code": "var",
            "label": "Variable",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 2,
        },
    )
    constant_slug = client.post(f"/api/v1/forms/{constant_form['id']}/publish").json()["public_slug"]
    for value in [10, 11, 12, 13]:
        submit_public_response(
            client,
            constant_slug,
            {
                "answers": [
                    {"question_id": constant_question["id"], "value_number": 5},
                    {"question_id": variable_question["id"], "value_number": value},
                ]
            },
        )
    constant_pair = client.post(
        f"/api/v1/forms/{constant_form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": constant_question["id"]},
            "y": {"target_type": "question", "target_id": variable_question["id"]},
            "method": "pearson",
            "store_result": False,
        },
    )
    assert constant_pair.status_code == 200
    assert constant_pair.json()["result"]["classification"] == "not_applicable"
    assert "constant_values" in constant_pair.json()["result"]["warnings"]

    low_n_project = create_project(client, "Proyecto low n correlacion")
    low_n_form = create_form(client, low_n_project["id"], "Formulario low n correlacion")
    low_x = create_question(
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
    low_y = create_question(
        client,
        low_n_form["id"],
        {
            "code": "y",
            "label": "Y",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 2,
        },
    )
    low_slug = client.post(f"/api/v1/forms/{low_n_form['id']}/publish").json()["public_slug"]
    for x_value, y_value in [(10, 11), (12, 13)]:
        submit_public_response(
            client,
            low_slug,
            {"answers": [{"question_id": low_x["id"], "value_number": x_value}, {"question_id": low_y["id"], "value_number": y_value}]},
        )
    low_pair = client.post(
        f"/api/v1/forms/{low_n_form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": low_x["id"]},
            "y": {"target_type": "question", "target_id": low_y["id"]},
            "method": "pearson",
            "store_result": False,
        },
    )
    assert low_pair.status_code == 200
    assert low_pair.json()["result"]["classification"] == "not_applicable"
    assert "insufficient_n" in low_pair.json()["result"]["warnings"]

    foreign_project = create_project(client, "Proyecto ajeno correlacion")
    foreign_form = create_form(client, foreign_project["id"], "Formulario ajeno correlacion")
    foreign_question = create_question(
        client,
        foreign_form["id"],
        {
            "code": "foreign",
            "label": "Foreign",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 1,
        },
    )
    foreign_pair = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "question", "target_id": questions["age"]["id"]},
            "y": {"target_type": "question", "target_id": foreign_question["id"]},
            "method": "pearson",
            "store_result": False,
        },
    )
    assert foreign_pair.status_code == 404

    project_variable_pair = client.post(
        f"/api/v1/forms/{form['id']}/correlations/pair",
        json={
            "x": {"target_type": "project_variable", "target_id": variables["age"]["id"]},
            "y": {"target_type": "project_variable", "target_id": variables["performance"]["id"]},
            "method": "pearson",
            "store_result": False,
        },
    )
    assert project_variable_pair.status_code == 200
    assert project_variable_pair.json()["result"]["method_used"] == "pearson"
