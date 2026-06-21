from fastapi.testclient import TestClient


def create_project(client: TestClient, title: str = "Proyecto decision") -> dict:
    response = client.post("/api/v1/projects", json={"title": title, "approach": "cuantitativo"})
    assert response.status_code == 201
    return response.json()


def create_form(client: TestClient, project_id: str, title: str = "Formulario decision") -> dict:
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


def prepare_correlation_form(client: TestClient) -> tuple[dict, dict, dict, dict]:
    project = create_project(client, "Proyecto correlacion")
    form = create_form(client, project["id"], "Formulario correlacion")
    x_question = create_question(
        client,
        form["id"],
        {
            "code": "x",
            "label": "Variable X",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 1,
        },
    )
    y_question = create_question(
        client,
        form["id"],
        {
            "code": "y",
            "label": "Variable Y",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 2,
        },
    )
    skew_question = create_question(
        client,
        form["id"],
        {
            "code": "skew",
            "label": "Variable sesgada",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 3,
        },
    )
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
            "is_required": True,
            "sort_order": 4,
        },
    )
    sexo_f = create_option(client, sexo_question["id"], {"label": "Femenino", "value": "F", "sort_order": 1})
    sexo_m = create_option(client, sexo_question["id"], {"label": "Masculino", "value": "M", "sort_order": 2})

    grupo_question = create_question(
        client,
        form["id"],
        {
            "code": "grupo",
            "label": "Grupo",
            "question_type": "single_choice",
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 5,
        },
    )
    grupo_a = create_option(client, grupo_question["id"], {"label": "A", "value": "A", "sort_order": 1})
    grupo_b = create_option(client, grupo_question["id"], {"label": "B", "value": "B", "sort_order": 2})
    grupo_c = create_option(client, grupo_question["id"], {"label": "C", "value": "C", "sort_order": 3})

    publish = client.post(f"/api/v1/forms/{form['id']}/publish")
    assert publish.status_code == 200
    slug = publish.json()["public_slug"]

    x_values = [49, 52, 47, 55, 50, 46, 53, 51, 48, 54, 45, 56, 49, 52, 47, 53, 50, 48, 55, 46, 51, 49, 54, 47, 52, 50, 48, 53, 46, 55]
    y_values = [58, 61, 56, 64, 59, 55, 62, 60, 57, 63, 54, 65, 58, 61, 56, 62, 59, 57, 64, 55, 60, 58, 63, 56, 61, 59, 57, 62, 55, 64]
    skew_values = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 5, 8, 13, 21, 34]
    for index in range(30):
        if index < 10:
            group_option = grupo_a["id"]
        elif index < 20:
            group_option = grupo_b["id"]
        else:
            group_option = grupo_c["id"]
        submit_public_response(
            client,
            slug,
            {
                "answers": [
                    {"question_id": x_question["id"], "value_number": x_values[index]},
                    {"question_id": y_question["id"], "value_number": y_values[index]},
                    {"question_id": skew_question["id"], "value_number": skew_values[index]},
                    {"question_id": sexo_question["id"], "option_id": sexo_f["id"] if index % 2 else sexo_m["id"]},
                    {"question_id": grupo_question["id"], "option_id": group_option},
                ]
            },
        )

    return form, x_question, y_question, skew_question, sexo_question, grupo_question


def test_statistical_decisions(client: TestClient):
    form, x_question, y_question, skew_question, sexo_question, grupo_question = prepare_correlation_form(client)

    pearson_oriented = client.post(
        f"/api/v1/forms/{form['id']}/statistical-decision",
        json={
            "analysis_goal": "correlation",
            "variables": [
                {"question_id": x_question["id"], "role": "x"},
                {"question_id": y_question["id"], "role": "y"},
            ],
            "alpha": 0.05,
            "normality_method": "auto",
            "score_aggregation": "mean",
            "include_discarded": False,
        },
    )
    assert pearson_oriented.status_code == 200
    pearson_body = pearson_oriented.json()
    assert pearson_body["recommended_test"] in {"pearson", "spearman"}
    assert pearson_body["explanation"]

    spearman_oriented = client.post(
        f"/api/v1/forms/{form['id']}/statistical-decision",
        json={
            "analysis_goal": "correlation",
            "variables": [
                {"question_id": x_question["id"], "role": "x"},
                {"question_id": skew_question["id"], "role": "y"},
            ],
            "alpha": 0.05,
            "normality_method": "auto",
            "score_aggregation": "mean",
            "include_discarded": False,
        },
    )
    assert spearman_oriented.status_code == 200
    spearman_body = spearman_oriented.json()
    assert spearman_body["recommended_test"] == "spearman"

    categorical_association = client.post(
        f"/api/v1/forms/{form['id']}/statistical-decision",
        json={
            "analysis_goal": "association_categorical",
            "variables": [
                {"question_id": sexo_question["id"], "role": "x"},
                {"question_id": grupo_question["id"], "role": "y"},
            ],
            "alpha": 0.05,
            "normality_method": "auto",
            "score_aggregation": "mean",
            "include_discarded": False,
        },
    )
    assert categorical_association.status_code == 200
    assert categorical_association.json()["recommended_test"] == "chi_square"

    two_group_project = create_project(client, "Proyecto comparacion 2 grupos")
    two_group_form = create_form(client, two_group_project["id"], "Formulario comparacion 2 grupos")
    outcome_question = create_question(
        client,
        two_group_form["id"],
        {
            "code": "outcome",
            "label": "Outcome",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 1,
        },
    )
    group_question = create_question(
        client,
        two_group_form["id"],
        {
            "code": "grupo",
            "label": "Grupo",
            "question_type": "single_choice",
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 2,
        },
    )
    g1 = create_option(client, group_question["id"], {"label": "G1", "value": "G1", "sort_order": 1})
    g2 = create_option(client, group_question["id"], {"label": "G2", "value": "G2", "sort_order": 2})
    publish_two = client.post(f"/api/v1/forms/{two_group_form['id']}/publish").json()["public_slug"]
    for index, value in enumerate([10, 11, 12, 13, 14, 18, 19, 20, 21, 22], start=1):
        submit_public_response(
            client,
            publish_two,
            {
                "answers": [
                    {"question_id": outcome_question["id"], "value_number": value},
                    {"question_id": group_question["id"], "option_id": g1["id"] if index <= 5 else g2["id"]},
                ]
            },
        )
    independent_two = client.post(
        f"/api/v1/forms/{two_group_form['id']}/statistical-decision",
        json={
            "analysis_goal": "comparison_independent_groups",
            "variables": [
                {"question_id": outcome_question["id"], "role": "outcome"},
                {"question_id": group_question["id"], "role": "group"},
            ],
            "alpha": 0.05,
            "normality_method": "auto",
            "score_aggregation": "mean",
            "include_discarded": False,
        },
    )
    assert independent_two.status_code == 200
    assert independent_two.json()["recommended_test"] == "mann_whitney_u"

    independent_three = client.post(
        f"/api/v1/forms/{form['id']}/statistical-decision",
        json={
            "analysis_goal": "comparison_independent_groups",
            "variables": [
                {"question_id": x_question["id"], "role": "outcome"},
                {"question_id": grupo_question["id"], "role": "group"},
            ],
            "alpha": 0.05,
            "normality_method": "auto",
            "score_aggregation": "mean",
            "include_discarded": False,
        },
    )
    assert independent_three.status_code == 200
    assert independent_three.json()["recommended_test"] in {"anova", "kruskal_wallis"}

    descriptive_only = client.post(
        f"/api/v1/forms/{form['id']}/statistical-decision",
        json={
            "analysis_goal": "descriptive_only",
            "variables": [],
            "alpha": 0.05,
            "normality_method": "auto",
            "score_aggregation": "mean",
            "include_discarded": False,
        },
    )
    assert descriptive_only.status_code == 200
    assert descriptive_only.json()["recommended_test"] == "descriptive_only"

    another_project = create_project(client, "Proyecto ajeno")
    another_form = create_form(client, another_project["id"], "Formulario ajeno")
    foreign_question = create_question(
        client,
        another_form["id"],
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
    invalid_variable = client.post(
        f"/api/v1/forms/{form['id']}/statistical-decision",
        json={
            "analysis_goal": "correlation",
            "variables": [
                {"question_id": x_question["id"], "role": "x"},
                {"question_id": foreign_question["id"], "role": "y"},
            ],
            "alpha": 0.05,
            "normality_method": "auto",
            "score_aggregation": "mean",
            "include_discarded": False,
        },
    )
    assert invalid_variable.status_code == 404

    low_n_project = create_project(client, "Proyecto low n")
    low_n_form = create_form(client, low_n_project["id"], "Formulario low n")
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
    for x_value, y_value in [(10, 11), (12, 12), (13, 15), (14, 16)]:
        submit_public_response(
            client,
            low_slug,
            {"answers": [{"question_id": low_x["id"], "value_number": x_value}, {"question_id": low_y["id"], "value_number": y_value}]},
        )
    low_n_decision = client.post(
        f"/api/v1/forms/{low_n_form['id']}/statistical-decision",
        json={
            "analysis_goal": "correlation",
            "variables": [
                {"question_id": low_x["id"], "role": "x"},
                {"question_id": low_y["id"], "role": "y"},
            ],
            "alpha": 0.05,
            "normality_method": "auto",
            "score_aggregation": "mean",
            "include_discarded": False,
            "store_result": True,
        },
    )
    assert low_n_decision.status_code == 200
    assert low_n_decision.json()["warnings"]
    assert low_n_decision.json()["explanation"]
