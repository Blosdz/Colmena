from pathlib import Path

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]


def create_project(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={
            "title": "Proyecto dataset",
            "research_type": "correlacional",
            "approach": "cuantitativo",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_form(client: TestClient, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/forms",
        json={
            "title": "Formulario base tabular",
            "description": "Formulario para validar dataset y exportaciones.",
            "instructions": "Responda todas las preguntas requeridas.",
            "thank_you_message": "Gracias por participar.",
        },
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


def test_dataset_build_edit_and_export_flow(client: TestClient):
    project = create_project(client)
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

    item_01_question = create_question(
        client,
        form["id"],
        {
            "code": "item_01",
            "label": "Me siento calmado durante las evaluaciones.",
            "question_type": "likert",
            "question_role": "item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "is_required": True,
            "is_scored": True,
            "sort_order": 3,
        },
    )
    item_01_options = [
        create_option(
            client,
            item_01_question["id"],
            {"label": f"Likert {score}", "value": str(score), "score": float(score), "sort_order": score},
        )
        for score in range(1, 6)
    ]

    item_02_question = create_question(
        client,
        form["id"],
        {
            "code": "item_02",
            "label": "Pierdo la concentracion con facilidad.",
            "question_type": "likert",
            "question_role": "item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "is_required": True,
            "is_scored": True,
            "is_reverse_scored": True,
            "sort_order": 4,
        },
    )
    item_02_options = [
        create_option(
            client,
            item_02_question["id"],
            {"label": f"Likert {score}", "value": str(score), "score": float(score), "sort_order": score},
        )
        for score in range(1, 6)
    ]

    comentario_question = create_question(
        client,
        form["id"],
        {
            "code": "comentario",
            "label": "Comentario breve",
            "question_type": "text_short",
            "question_role": "open_question",
            "measurement_level": "text",
            "data_type": "text",
            "is_required": False,
            "sort_order": 5,
        },
    )

    intereses_question = create_question(
        client,
        form["id"],
        {
            "code": "intereses",
            "label": "Intereses academicos",
            "question_type": "multiple_choice",
            "question_role": "variable_item",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": False,
            "is_scored": True,
            "sort_order": 6,
        },
    )
    interes_investigacion = create_option(
        client,
        intereses_question["id"],
        {"label": "Investigacion", "value": "investigacion", "score": 1.0, "sort_order": 1},
    )
    interes_docencia = create_option(
        client,
        intereses_question["id"],
        {"label": "Docencia", "value": "docencia", "score": 1.0, "sort_order": 2},
    )
    interes_gestion = create_option(
        client,
        intereses_question["id"],
        {"label": "Gestion", "value": "gestion", "score": 1.0, "sort_order": 3},
    )

    publish_response = client.post(f"/api/v1/forms/{form['id']}/publish")
    assert publish_response.status_code == 200
    public_slug = publish_response.json()["public_slug"]
    assert public_slug

    response_1 = submit_public_response(
        client,
        public_slug,
        {
            "respondent_code": "R-001",
            "answers": [
                {"question_id": sexo_question["id"], "option_id": sexo_f["id"]},
                {"question_id": edad_question["id"], "value_number": 22},
                {"question_id": item_01_question["id"], "option_id": item_01_options[3]["id"]},
                {"question_id": item_02_question["id"], "option_id": item_02_options[1]["id"]},
                {"question_id": comentario_question["id"], "value_text": "Respuesta uno"},
                {
                    "question_id": intereses_question["id"],
                    "value_json": [interes_investigacion["id"], interes_gestion["id"]],
                },
            ],
            "metadata_json": {"source": "dataset-test-1"},
        },
    )
    response_2 = submit_public_response(
        client,
        public_slug,
        {
            "respondent_code": "R-002",
            "answers": [
                {"question_id": sexo_question["id"], "option_id": sexo_m["id"]},
                {"question_id": edad_question["id"], "value_number": 25},
                {"question_id": item_01_question["id"], "option_id": item_01_options[4]["id"]},
                {"question_id": item_02_question["id"], "option_id": item_02_options[0]["id"]},
                {
                    "question_id": intereses_question["id"],
                    "value_json": [interes_docencia["id"]],
                },
            ],
            "metadata_json": {"source": "dataset-test-2"},
        },
    )
    response_3 = submit_public_response(
        client,
        public_slug,
        {
            "respondent_code": "R-003",
            "answers": [
                {"question_id": sexo_question["id"], "option_id": sexo_f["id"]},
                {"question_id": edad_question["id"], "value_number": 31},
                {"question_id": item_01_question["id"], "option_id": item_01_options[2]["id"]},
                {"question_id": item_02_question["id"], "option_id": item_02_options[4]["id"]},
                {"question_id": comentario_question["id"], "value_text": "Respuesta tres"},
                {
                    "question_id": intereses_question["id"],
                    "value_json": [interes_investigacion["id"], interes_docencia["id"]],
                },
            ],
            "metadata_json": {"source": "dataset-test-3"},
        },
    )

    dataset_mixed = client.get(f"/api/v1/forms/{form['id']}/dataset?mode=mixed")
    assert dataset_mixed.status_code == 200
    dataset_mixed_body = dataset_mixed.json()
    assert dataset_mixed_body["total_rows"] == 3
    assert len(dataset_mixed_body["rows"]) == 3
    expected_columns = {
        "response_id",
        "project_id",
        "form_id",
        "respondent_code",
        "response_status",
        "source",
        "submitted_at",
        "created_at",
        "sexo",
        "sexo__value",
        "edad",
        "item_01",
        "item_01__value",
        "item_01__score",
        "item_02",
        "item_02__value",
        "item_02__score",
        "comentario",
        "intereses",
        "intereses__value",
        "intereses__score",
        "intereses__json",
    }
    returned_columns = {column["name"] for column in dataset_mixed_body["columns"]}
    assert expected_columns.issubset(returned_columns)

    row_by_response = {row["response_id"]: row for row in dataset_mixed_body["rows"]}
    assert row_by_response[response_1["response_id"]]["sexo"] == "Femenino"
    assert row_by_response[response_1["response_id"]]["sexo__value"] == "F"
    assert row_by_response[response_1["response_id"]]["item_01__score"] == 4.0
    assert row_by_response[response_1["response_id"]]["item_02__score"] == 4.0
    assert row_by_response[response_1["response_id"]]["intereses__score"] == 2.0
    assert row_by_response[response_2["response_id"]]["comentario"] is None

    dataset_label = client.get(f"/api/v1/forms/{form['id']}/dataset?mode=label")
    assert dataset_label.status_code == 200
    assert dataset_label.json()["rows"][0]["sexo"] in {"Femenino", "Masculino"}

    dataset_value = client.get(f"/api/v1/forms/{form['id']}/dataset?mode=value")
    assert dataset_value.status_code == 200
    value_rows = {row["response_id"]: row for row in dataset_value.json()["rows"]}
    assert value_rows[response_1["response_id"]]["sexo"] == "F"

    dataset_score = client.get(f"/api/v1/forms/{form['id']}/dataset?mode=score")
    assert dataset_score.status_code == 200
    score_rows = {row["response_id"]: row for row in dataset_score.json()["rows"]}
    assert score_rows[response_1["response_id"]]["item_01"] == 4.0
    assert score_rows[response_1["response_id"]]["item_02"] == 4.0
    assert score_rows[response_2["response_id"]]["intereses"] == 1.0

    dataset_expanded = client.get(
        f"/api/v1/forms/{form['id']}/dataset?mode=mixed&expand_multiple_choice=true"
    )
    assert dataset_expanded.status_code == 200
    expanded_columns = {column["name"] for column in dataset_expanded.json()["columns"]}
    assert "intereses__investigacion" in expanded_columns
    assert "intereses__docencia" in expanded_columns
    assert "intereses__gestion" in expanded_columns

    data_dictionary = client.get(f"/api/v1/forms/{form['id']}/data-dictionary")
    assert data_dictionary.status_code == 200
    dictionary_items = {item["column_name"]: item for item in data_dictionary.json()["items"]}
    assert dictionary_items["item_02"]["is_reverse_scored"] is True
    assert dictionary_items["intereses"]["question_type"] == "multiple_choice"

    completeness = client.get(f"/api/v1/forms/{form['id']}/completeness")
    assert completeness.status_code == 200
    completeness_items = {item["column_name"]: item for item in completeness.json()["items"]}
    assert completeness_items["sexo"]["answered_count"] == 3
    assert completeness_items["comentario"]["missing_count"] == 1
    assert completeness_items["comentario"]["warning_level"] == "critical"

    responses_list = client.get(f"/api/v1/forms/{form['id']}/responses")
    assert responses_list.status_code == 200
    stored_responses = responses_list.json()["items"]
    age_answer_id = next(
        answer["id"]
        for response in stored_responses
        if response["id"] == response_1["response_id"]
        for answer in response["answers"]
        if answer["question_id"] == edad_question["id"]
    )
    sex_answer_id = next(
        answer["id"]
        for response in stored_responses
        if response["id"] == response_1["response_id"]
        for answer in response["answers"]
        if answer["question_id"] == sexo_question["id"]
    )

    discard_response = client.patch(
        f"/api/v1/form-responses/{response_2['response_id']}/status",
        json={"status": "discarded"},
    )
    assert discard_response.status_code == 200
    assert discard_response.json()["status"] == "discarded"

    dataset_without_discarded = client.get(f"/api/v1/forms/{form['id']}/dataset?mode=mixed")
    assert dataset_without_discarded.status_code == 200
    response_ids_without_discarded = {row["response_id"] for row in dataset_without_discarded.json()["rows"]}
    assert response_2["response_id"] not in response_ids_without_discarded

    dataset_with_discarded = client.get(
        f"/api/v1/forms/{form['id']}/dataset?mode=mixed&include_discarded=true"
    )
    assert dataset_with_discarded.status_code == 200
    response_ids_with_discarded = {row["response_id"] for row in dataset_with_discarded.json()["rows"]}
    assert response_2["response_id"] in response_ids_with_discarded

    restore_response = client.post(f"/api/v1/form-responses/{response_2['response_id']}/restore")
    assert restore_response.status_code == 200
    assert restore_response.json()["status"] == "complete"

    update_answer = client.patch(
        f"/api/v1/form-answers/{age_answer_id}",
        json={"value_number": 29},
    )
    assert update_answer.status_code == 200
    assert update_answer.json()["value_number"] == 29.0

    dataset_after_edit = client.get(f"/api/v1/forms/{form['id']}/dataset?mode=mixed")
    assert dataset_after_edit.status_code == 200
    edited_row = next(
        row for row in dataset_after_edit.json()["rows"] if row["response_id"] == response_1["response_id"]
    )
    assert edited_row["edad"] == 29.0

    invalid_option_update = client.patch(
        f"/api/v1/form-answers/{sex_answer_id}",
        json={"option_id": item_01_options[0]["id"]},
    )
    assert invalid_option_update.status_code == 400

    invalid_number_update = client.patch(
        f"/api/v1/form-answers/{age_answer_id}",
        json={"value_number": 70},
    )
    assert invalid_number_update.status_code == 422

    export_payload = {
        "mode": "mixed",
        "include_metadata": True,
        "include_discarded": False,
        "expand_multiple_choice": False,
    }
    export_excel = client.post(f"/api/v1/forms/{form['id']}/exports/excel", json=export_payload)
    assert export_excel.status_code == 201
    export_excel_body = export_excel.json()
    export_excel_path = BACKEND_DIR / export_excel_body["file_path"].replace("/", "\\")
    assert export_excel_path.exists()

    export_csv = client.post(f"/api/v1/forms/{form['id']}/exports/csv", json=export_payload)
    assert export_csv.status_code == 201
    export_csv_body = export_csv.json()
    export_csv_path = BACKEND_DIR / export_csv_body["file_path"].replace("/", "\\")
    assert export_csv_path.exists()

    exports_list = client.get(f"/api/v1/forms/{form['id']}/exports")
    assert exports_list.status_code == 200
    exports_body = exports_list.json()
    assert exports_body["total"] >= 2
    assert {item["artifact_type"] for item in exports_body["items"]} >= {"dataset_excel", "dataset_csv"}
