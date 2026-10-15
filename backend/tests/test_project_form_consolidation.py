from fastapi.testclient import TestClient


def create_project(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={
            "title": "Relación entre clima y compromiso",
            "approach": "cuantitativo",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_variable(client: TestClient, project_id: str, name: str, code: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/variables",
        json={
            "name": name,
            "code": code,
            "variable_role": "main",
            "variable_classification": "independent",
            "measurement_mode": "instrument",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "is_required_for_analysis": True,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_legacy_variable_form(
    client: TestClient,
    project_id: str,
    variable: dict,
    question_code: str,
) -> tuple[dict, dict, dict, dict]:
    form_response = client.post(
        f"/api/v1/projects/{project_id}/forms",
        json={"title": variable["name"], "status": "draft"},
    )
    assert form_response.status_code == 201
    form = form_response.json()

    section = client.post(
        f"/api/v1/forms/{form['id']}/sections",
        json={"title": "Datos del participante", "sort_order": 0},
    ).json()
    age_question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "section_id": section["id"],
            "code": "edad",
            "label": "Edad",
            "question_type": "number",
            "question_role": "sociodemographic",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 0,
        },
    ).json()
    instrument = client.post(
        f"/api/v1/forms/{form['id']}/instruments",
        json={
            "name": variable["name"],
            "project_variable_id": variable["id"],
            "sort_order": 0,
        },
    ).json()
    question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "instrument_id": instrument["id"],
            "project_variable_id": variable["id"],
            "code": question_code,
            "label": f"Ítem {question_code}",
            "question_type": "likert",
            "question_role": "item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "is_required": True,
            "is_scored": True,
            "sort_order": 0,
        },
    ).json()
    option = client.post(
        f"/api/v1/form-questions/{question['id']}/options",
        json={"label": "De acuerdo", "value": "1", "score": 1, "sort_order": 0},
    ).json()
    published = client.post(f"/api/v1/forms/{form['id']}/publish")
    assert published.status_code == 200
    return form, age_question, question, option


def test_consolidates_two_variable_forms_into_one_public_questionnaire(client: TestClient):
    project = create_project(client)
    first_variable = create_variable(client, project["id"], "Clima", "CLI")
    second_variable = create_variable(client, project["id"], "Compromiso", "COM")
    first_form, first_age, first_question, first_option = create_legacy_variable_form(
        client, project["id"], first_variable, "P1"
    )
    second_form, _, second_question, second_option = create_legacy_variable_form(
        client, project["id"], second_variable, "P2"
    )

    first_link = client.get(f"/api/v1/forms/{first_form['id']}/public-link").json()
    old_response = client.post(
        f"/api/public/forms/{first_link['public_slug']}/responses",
        json={
            "answers": [
                {"question_id": first_age["id"], "value_number": 30},
                {"question_id": first_question["id"], "option_id": first_option["id"]},
            ]
        },
    )
    assert old_response.status_code == 201

    consolidated = client.post(f"/api/v1/projects/{project['id']}/forms/consolidate")
    assert consolidated.status_code == 200
    assert consolidated.json()["id"] == first_form["id"]
    assert consolidated.json()["title"] == project["title"]

    project_forms = client.get(f"/api/v1/projects/{project['id']}/forms").json()
    assert project_forms["total"] == 1

    consolidated_again = client.post(f"/api/v1/projects/{project['id']}/forms/consolidate")
    assert consolidated_again.status_code == 200
    assert consolidated_again.json()["id"] == first_form["id"]

    instruments = client.get(f"/api/v1/forms/{first_form['id']}/instruments").json()
    assert instruments["total"] == 2
    assert {item["name"] for item in instruments["items"]} == {"Clima", "Compromiso"}

    questions = client.get(f"/api/v1/forms/{first_form['id']}/questions").json()
    assert questions["total"] == 3
    assert {item["code"] for item in questions["items"]} == {"edad", "P1", "P2"}

    stored_old_response = client.get(
        f"/api/v1/form-responses/{old_response.json()['response_id']}"
    )
    assert stored_old_response.status_code == 200
    assert stored_old_response.json()["status"] == "partial"

    published = client.post(f"/api/v1/forms/{first_form['id']}/publish")
    assert published.status_code == 200
    public_form = client.get(
        f"/api/public/forms/{published.json()['public_slug']}"
    ).json()
    assert len(public_form["instruments"]) == 2
    assert len(public_form["questions"]) == 3
    assert [section["title"] for section in public_form["sections"]] == [
        "Datos del participante",
        "Clima",
        "Compromiso",
    ]

    complete_response = client.post(
        f"/api/public/forms/{published.json()['public_slug']}/responses",
        json={
            "snapshot_id": public_form["snapshot_id"],
            "answers": [
                {"question_id": first_age["id"], "value_number": 25},
                {"question_id": first_question["id"], "option_id": first_option["id"]},
                {"question_id": second_question["id"], "option_id": second_option["id"]},
            ],
        },
    )
    assert complete_response.status_code == 201
    stored_complete = client.get(
        f"/api/v1/form-responses/{complete_response.json()['response_id']}"
    )
    assert stored_complete.json()["status"] == "complete"

    second_instrument = next(
        item for item in instruments["items"] if item["name"] == "Compromiso"
    )
    selected_publish = client.post(
        f"/api/v1/forms/{first_form['id']}/publish",
        json={"instrument_ids": [second_instrument["id"]]},
    )
    assert selected_publish.status_code == 200
    assert selected_publish.json()["published_instrument_ids"] == [second_instrument["id"]]

    selected_public_form = client.get(
        f"/api/public/forms/{selected_publish.json()['public_slug']}"
    ).json()
    assert [item["name"] for item in selected_public_form["instruments"]] == ["Compromiso"]
    assert {item["code"] for item in selected_public_form["questions"]} == {"edad", "P2"}
    assert [section["title"] for section in selected_public_form["sections"]] == [
        "Datos del participante",
        "Compromiso",
    ]

    selected_response = client.post(
        f"/api/public/forms/{selected_publish.json()['public_slug']}/responses",
        json={
            "snapshot_id": selected_public_form["snapshot_id"],
            "answers": [
                {"question_id": first_age["id"], "value_number": 28},
                {"question_id": second_question["id"], "option_id": second_option["id"]},
            ],
        },
    )
    assert selected_response.status_code == 201
    stored_selected = client.get(
        f"/api/v1/form-responses/{selected_response.json()['response_id']}"
    )
    assert stored_selected.json()["status"] == "complete"

    empty_selection = client.post(
        f"/api/v1/forms/{first_form['id']}/publish",
        json={"instrument_ids": []},
    )
    assert empty_selection.status_code == 422

    removed_form = client.get(f"/api/v1/forms/{second_form['id']}")
    assert removed_form.status_code == 404
