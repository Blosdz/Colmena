from fastapi.testclient import TestClient


def create_project(client: TestClient, title: str = "Proyecto comparaciones") -> dict:
    response = client.post("/api/v1/projects", json={"title": title, "approach": "cuantitativo"})
    assert response.status_code == 201
    return response.json()


def create_project_variable(client: TestClient, project_id: str, payload: dict) -> dict:
    response = client.post(f"/api/v1/projects/{project_id}/variables", json=payload)
    assert response.status_code == 201
    return response.json()


def create_form(client: TestClient, project_id: str, title: str = "Formulario comparaciones") -> dict:
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


def prepare_group_fixture(client: TestClient) -> dict:
    project = create_project(client)
    performance_variable = create_project_variable(
        client,
        project["id"],
        {
            "name": "Rendimiento",
            "code": "performance",
            "variable_role": "outcome",
            "measurement_level": "ratio",
            "data_type": "numeric",
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
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 1,
        },
    )
    sexo_f = create_option(client, sexo_question["id"], {"label": "Femenino", "value": "F", "sort_order": 1})
    sexo_m = create_option(client, sexo_question["id"], {"label": "Masculino", "value": "M", "sort_order": 2})

    ciclo_question = create_question(
        client,
        form["id"],
        {
            "code": "ciclo",
            "label": "Ciclo",
            "question_type": "single_choice",
            "question_role": "grouping_variable",
            "measurement_level": "ordinal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 2,
        },
    )
    ciclo_1 = create_option(client, ciclo_question["id"], {"label": "Ciclo 1", "value": "1", "sort_order": 1})
    ciclo_2 = create_option(client, ciclo_question["id"], {"label": "Ciclo 2", "value": "2", "sort_order": 2})
    ciclo_3 = create_option(client, ciclo_question["id"], {"label": "Ciclo 3", "value": "3", "sort_order": 3})

    performance_question = create_question(
        client,
        form["id"],
        {
            "code": "performance_score",
            "label": "Puntaje de rendimiento",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "project_variable_id": performance_variable["id"],
            "is_required": True,
            "min_value": 0,
            "max_value": 100,
            "sort_order": 3,
        },
    )

    instrument = client.post(
        f"/api/v1/forms/{form['id']}/instruments",
        json={"name": "Escala de compromiso", "project_variable_id": performance_variable["id"], "sort_order": 1},
    )
    assert instrument.status_code == 201
    instrument = instrument.json()

    dimension = client.post(
        f"/api/v1/form-instruments/{instrument['id']}/dimensions",
        json={"name": "Compromiso", "sort_order": 1},
    )
    assert dimension.status_code == 201
    dimension = dimension.json()

    item_codes = ["item_01", "item_02", "item_03"]
    items: dict[str, dict] = {}
    options: dict[str, list[dict]] = {}
    for sort_order, code in enumerate(item_codes, start=4):
        item = create_question(
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
                "project_variable_id": performance_variable["id"],
                "is_required": True,
                "is_scored": True,
                "sort_order": sort_order,
            },
        )
        items[code] = item
        options[code] = [
            create_option(
                client,
                item["id"],
                {"label": f"Likert {score}", "value": str(score), "score": float(score), "sort_order": score},
            )
            for score in range(1, 6)
        ]

    publish = client.post(f"/api/v1/forms/{form['id']}/publish")
    assert publish.status_code == 200
    public_slug = publish.json()["public_slug"]

    performance_values = [40, 42, 44, 50, 52, 54, 60, 62, 64, 70, 72, 74, 80, 82, 84, 90, 92, 94]
    cycle_options = [ciclo_1["id"]] * 6 + [ciclo_2["id"]] * 6 + [ciclo_3["id"]] * 6
    sex_options = [sexo_f["id"]] * 9 + [sexo_m["id"]] * 9
    likert_levels = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5]

    response_ids: list[str] = []
    for index, performance in enumerate(performance_values):
        response = submit_public_response(
            client,
            public_slug,
            {
                "respondent_code": f"G-{index + 1:03d}",
                "answers": [
                    {"question_id": sexo_question["id"], "option_id": sex_options[index]},
                    {"question_id": ciclo_question["id"], "option_id": cycle_options[index]},
                    {"question_id": performance_question["id"], "value_number": performance},
                    {"question_id": items["item_01"]["id"], "option_id": options["item_01"][likert_levels[index] - 1]["id"]},
                    {"question_id": items["item_02"]["id"], "option_id": options["item_02"][min(likert_levels[index] + 1, 5) - 1]["id"]},
                    {"question_id": items["item_03"]["id"], "option_id": options["item_03"][likert_levels[index] - 1]["id"]},
                ],
            },
        )
        response_ids.append(response["response_id"])

    return {
        "project": project,
        "form": form,
        "responses": response_ids,
        "questions": {
            "sexo": sexo_question,
            "ciclo": ciclo_question,
            "performance": performance_question,
            **items,
        },
        "instrument": instrument,
        "dimension": dimension,
        "variable": performance_variable,
    }


def test_group_comparisons_end_to_end(client: TestClient):
    fixture = prepare_group_fixture(client)
    form = fixture["form"]
    questions = fixture["questions"]
    instrument = fixture["instrument"]
    dimension = fixture["dimension"]
    variable = fixture["variable"]

    options_response = client.get(f"/api/v1/forms/{form['id']}/group-comparisons/options")
    assert options_response.status_code == 200
    options_body = options_response.json()
    assert any(item["target_id"] == questions["performance"]["id"] for item in options_body["outcomes"])
    assert any(item["target_id"] == questions["sexo"]["id"] for item in options_body["groups"])

    t_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "t_student_independent",
            "store_result": True,
        },
    )
    assert t_response.status_code == 200
    t_body = t_response.json()
    assert t_body["analysis_run_id"] is not None
    assert t_body["result"]["method_used"] == "t_student_independent"
    assert t_body["result"]["variance_homogeneity"]["method"] == "levene"
    assert t_body["result"]["effect_size"]["name"] == "cohens_d"
    assert t_body["result"]["groups"]

    welch_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "welch_t",
            "store_result": False,
        },
    )
    assert welch_response.status_code == 200
    assert welch_response.json()["analysis_run_id"] is None
    assert welch_response.json()["result"]["method_used"] == "welch_t"

    mann_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "mann_whitney_u",
            "store_result": False,
        },
    )
    assert mann_response.status_code == 200
    assert mann_response.json()["result"]["method_used"] == "mann_whitney_u"

    anova_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["ciclo"]["id"]},
            "method": "anova_one_way",
            "store_result": False,
        },
    )
    assert anova_response.status_code == 200
    anova_body = anova_response.json()
    assert anova_body["result"]["method_used"] == "anova_one_way"
    assert anova_body["result"]["effect_size"]["name"] == "eta_squared"
    assert "posthoc_required" in anova_body["result"]["warnings"]

    kruskal_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["ciclo"]["id"]},
            "method": "kruskal_wallis",
            "store_result": False,
        },
    )
    assert kruskal_response.status_code == 200
    assert kruskal_response.json()["result"]["method_used"] == "kruskal_wallis"

    auto_two_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert auto_two_response.status_code == 200
    auto_two_body = auto_two_response.json()
    assert auto_two_body["result"]["method_used"] in {"t_student_independent", "welch_t", "mann_whitney_u"}
    assert "method_auto_selected" in auto_two_body["result"]["warnings"]

    auto_three_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "instrument", "target_id": instrument["id"]},
            "group": {"target_type": "question", "target_id": questions["ciclo"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert auto_three_response.status_code == 200
    auto_three_body = auto_three_response.json()
    assert auto_three_body["result"]["method_used"] in {"anova_one_way", "kruskal_wallis"}
    assert auto_three_body["result"]["interpretation"]

    dimension_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "dimension", "target_id": dimension["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "t_student_independent",
            "store_result": False,
        },
    )
    assert dimension_response.status_code == 200
    assert dimension_response.json()["result"]["method_used"] == "t_student_independent"

    project_variable_response = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "project_variable", "target_id": variable["id"]},
            "group": {"target_type": "question", "target_id": questions["ciclo"]["id"]},
            "method": "anova_one_way",
            "store_result": False,
        },
    )
    assert project_variable_response.status_code == 200
    assert project_variable_response.json()["result"]["method_used"] == "anova_one_way"

    discard_response = client.patch(
        f"/api/v1/form-responses/{fixture['responses'][0]}/status",
        json={"status": "discarded"},
    )
    assert discard_response.status_code == 200

    without_discarded = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "t_student_independent",
            "store_result": False,
        },
    )
    assert without_discarded.status_code == 200
    assert without_discarded.json()["result"]["valid_n"] == 17

    with_discarded = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "t_student_independent",
            "include_discarded": True,
            "store_result": False,
        },
    )
    assert with_discarded.status_code == 200
    assert with_discarded.json()["result"]["valid_n"] == 18

    outcome_categorical = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "group": {"target_type": "question", "target_id": questions["ciclo"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert outcome_categorical.status_code == 200
    assert outcome_categorical.json()["result"]["classification"] == "not_applicable"

    grouping_numeric = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "group": {"target_type": "question", "target_id": questions["performance"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert grouping_numeric.status_code == 200
    assert grouping_numeric.json()["result"]["classification"] == "not_applicable"

    constant_project = create_project(client, "Proyecto constante grupos")
    constant_form = create_form(client, constant_project["id"], "Formulario constante grupos")
    constant_group = create_question(
        client,
        constant_form["id"],
        {
            "code": "grp",
            "label": "Grupo",
            "question_type": "single_choice",
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 1,
        },
    )
    group_a = create_option(client, constant_group["id"], {"label": "A", "value": "A", "sort_order": 1})
    group_b = create_option(client, constant_group["id"], {"label": "B", "value": "B", "sort_order": 2})
    constant_outcome = create_question(
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
            "sort_order": 2,
        },
    )
    constant_slug = client.post(f"/api/v1/forms/{constant_form['id']}/publish").json()["public_slug"]
    for option_id in [group_a["id"], group_a["id"], group_b["id"], group_b["id"]]:
        submit_public_response(
            client,
            constant_slug,
            {
                "answers": [
                    {"question_id": constant_group["id"], "option_id": option_id},
                    {"question_id": constant_outcome["id"], "value_number": 5},
                ]
            },
        )
    constant_result = client.post(
        f"/api/v1/forms/{constant_form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": constant_outcome["id"]},
            "group": {"target_type": "question", "target_id": constant_group["id"]},
            "method": "t_student_independent",
            "store_result": False,
        },
    )
    assert constant_result.status_code == 200
    assert constant_result.json()["result"]["classification"] == "not_applicable"
    assert "constant_values" in constant_result.json()["result"]["warnings"]

    low_n_project = create_project(client, "Proyecto low n grupos")
    low_n_form = create_form(client, low_n_project["id"], "Formulario low n grupos")
    low_group = create_question(
        client,
        low_n_form["id"],
        {
            "code": "g",
            "label": "Grupo",
            "question_type": "single_choice",
            "question_role": "grouping_variable",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 1,
        },
    )
    low_a = create_option(client, low_group["id"], {"label": "A", "value": "A", "sort_order": 1})
    low_b = create_option(client, low_group["id"], {"label": "B", "value": "B", "sort_order": 2})
    low_c = create_option(client, low_group["id"], {"label": "C", "value": "C", "sort_order": 3})
    low_outcome = create_question(
        client,
        low_n_form["id"],
        {
            "code": "y",
            "label": "Outcome",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 2,
        },
    )
    low_slug = client.post(f"/api/v1/forms/{low_n_form['id']}/publish").json()["public_slug"]
    for option_id, value in [(low_a["id"], 10), (low_a["id"], 12), (low_b["id"], 20), (low_b["id"], 22), (low_c["id"], 30)]:
        submit_public_response(
            client,
            low_slug,
            {
                "answers": [
                    {"question_id": low_group["id"], "option_id": option_id},
                    {"question_id": low_outcome["id"], "value_number": value},
                ]
            },
        )
    low_n_result = client.post(
        f"/api/v1/forms/{low_n_form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": low_outcome["id"]},
            "group": {"target_type": "question", "target_id": low_group["id"]},
            "method": "kruskal_wallis",
            "store_result": False,
        },
    )
    assert low_n_result.status_code == 200
    assert "group_with_low_n" in low_n_result.json()["result"]["warnings"]

    foreign_project = create_project(client, "Proyecto ajeno grupos")
    foreign_form = create_form(client, foreign_project["id"], "Formulario ajeno grupos")
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
    foreign_result = client.post(
        f"/api/v1/forms/{form['id']}/group-comparisons",
        json={
            "outcome": {"target_type": "question", "target_id": foreign_question["id"]},
            "group": {"target_type": "question", "target_id": questions["sexo"]["id"]},
            "method": "auto",
            "store_result": False,
        },
    )
    assert foreign_result.status_code == 404
