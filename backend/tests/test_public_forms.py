from fastapi.testclient import TestClient


def create_project(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={"title": "Proyecto publico", "approach": "cuantitativo"},
    )
    assert response.status_code == 201
    return response.json()


def create_form(client: TestClient, project_id: str, title: str = "Formulario publico") -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/forms",
        json={"title": title, "instructions": "Responda con sinceridad"},
    )
    assert response.status_code == 201
    return response.json()


def create_basic_public_question(client: TestClient, form_id: str) -> tuple[dict, dict]:
    question_response = client.post(
        f"/api/v1/forms/{form_id}/questions",
        json={
            "code": "sex",
            "label": "Sexo",
            "question_type": "single_choice",
            "question_role": "sociodemographic",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "is_required": True,
            "sort_order": 1,
        },
    )
    assert question_response.status_code == 201
    question = question_response.json()
    option_response = client.post(
        f"/api/v1/form-questions/{question['id']}/options",
        json={"label": "Femenino", "value": "F", "score": 2, "sort_order": 1},
    )
    assert option_response.status_code == 201
    return question, option_response.json()


def publish_form(client: TestClient, form_id: str) -> dict:
    response = client.post(f"/api/v1/forms/{form_id}/publish")
    assert response.status_code == 200
    return response.json()


def test_public_form_must_be_published(client: TestClient):
    project = create_project(client)
    form = create_form(client, project["id"])

    response = client.get("/api/public/forms/non-existent-slug")
    assert response.status_code == 404

    link = client.get(f"/api/v1/forms/{form['id']}/public-link")
    assert link.status_code == 200
    assert link.json()["public_slug"] is None


def test_publish_without_questions_fails(client: TestClient):
    project = create_project(client)
    form = create_form(client, project["id"], "Formulario sin preguntas")

    response = client.post(f"/api/v1/forms/{form['id']}/publish")

    assert response.status_code == 400
    assert "without active questions" in response.json()["detail"]


def test_public_publish_read_submit_close_reopen_flow(client: TestClient):
    project = create_project(client)
    form = create_form(client, project["id"], "Formulario de ansiedad publica")
    choice_question, choice_option = create_basic_public_question(client, form["id"])

    likert_question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "code": "item_01",
            "label": "Siento tension al rendir examenes",
            "question_type": "likert",
            "question_role": "item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "is_required": True,
            "is_scored": True,
            "is_reverse_scored": True,
            "sort_order": 2,
        },
    ).json()
    likert_options = []
    for score in range(1, 6):
        likert_options.append(
            client.post(
                f"/api/v1/form-questions/{likert_question['id']}/options",
                json={"label": f"Opcion {score}", "value": str(score), "score": float(score), "sort_order": score},
            ).json()
        )

    number_question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "code": "age",
            "label": "Edad",
            "question_type": "number",
            "question_role": "variable_item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "min_value": 18,
            "max_value": 60,
            "is_required": False,
            "is_scored": True,
            "sort_order": 3,
        },
    ).json()

    before_publish = client.get(f"/api/v1/forms/{form['id']}/public-link")
    assert before_publish.status_code == 200
    assert before_publish.json()["public_slug"] is None

    publish = publish_form(client, form["id"])
    assert publish["public_slug"] is not None
    public_slug = publish["public_slug"]

    public_form = client.get(f"/api/public/forms/{public_slug}")
    assert public_form.status_code == 200
    public_body = public_form.json()
    assert public_body["status"] == "published"
    assert len(public_body["questions"]) == 3
    assert public_body["questions"][0]["options"][0]["id"] == choice_option["id"]

    submitted = client.post(
        f"/api/public/forms/{public_slug}/responses",
        json={
            "respondent_code": None,
            "answers": [
                {"question_id": choice_question["id"], "option_id": choice_option["id"]},
                {"question_id": likert_question["id"], "option_id": likert_options[0]["id"]},
                {"question_id": number_question["id"], "value_number": 25},
            ],
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert submitted.status_code == 201
    response_id = submitted.json()["response_id"]

    internal_responses = client.get(f"/api/v1/forms/{form['id']}/responses")
    assert internal_responses.status_code == 200
    assert internal_responses.json()["total"] == 1
    stored_response = internal_responses.json()["items"][0]
    assert stored_response["source"] == "public_link"
    assert len(stored_response["answers"]) == 3

    choice_answer = next(answer for answer in stored_response["answers"] if answer["question_id"] == choice_question["id"])
    likert_answer = next(answer for answer in stored_response["answers"] if answer["question_id"] == likert_question["id"])
    number_answer = next(answer for answer in stored_response["answers"] if answer["question_id"] == number_question["id"])
    assert choice_answer["option_id"] == choice_option["id"]
    assert choice_answer["score_value"] == 2.0
    assert likert_answer["score_value"] == 5.0
    assert number_answer["score_value"] == 25.0

    missing_required = client.post(
        f"/api/public/forms/{public_slug}/responses",
        json={"answers": [{"question_id": number_question["id"], "value_number": 30}]},
    )
    assert missing_required.status_code == 422

    out_of_range = client.post(
        f"/api/public/forms/{public_slug}/responses",
        json={
            "answers": [
                {"question_id": choice_question["id"], "option_id": choice_option["id"]},
                {"question_id": likert_question["id"], "option_id": likert_options[2]["id"]},
                {"question_id": number_question["id"], "value_number": 10},
            ]
        },
    )
    assert out_of_range.status_code == 422

    closed = client.post(f"/api/v1/forms/{form['id']}/close")
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    closed_submit = client.post(
        f"/api/public/forms/{public_slug}/responses",
        json={"answers": [{"question_id": choice_question["id"], "option_id": choice_option["id"]}]},
    )
    assert closed_submit.status_code == 409

    reopened = client.post(f"/api/v1/forms/{form['id']}/reopen")
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "published"

    second_submit = client.post(
        f"/api/public/forms/{public_slug}/responses",
        json={
            "answers": [
                {"question_id": choice_question["id"], "option_id": choice_option["id"]},
                {"question_id": likert_question["id"], "option_id": likert_options[4]["id"]},
            ]
        },
    )
    assert second_submit.status_code == 201

    invalid_option = client.post(
        f"/api/public/forms/{public_slug}/responses",
        json={
            "answers": [
                {"question_id": choice_question["id"], "option_id": likert_options[0]["id"]},
                {"question_id": likert_question["id"], "option_id": likert_options[1]["id"]},
            ]
        },
    )
    assert invalid_option.status_code == 400

    delete_question = client.delete(f"/api/v1/form-questions/{choice_question['id']}")
    assert delete_question.status_code == 200

    deleted_question_submit = client.post(
        f"/api/public/forms/{public_slug}/responses",
        json={
            "answers": [
                {"question_id": choice_question["id"], "option_id": choice_option["id"]},
                {"question_id": likert_question["id"], "option_id": likert_options[1]["id"]},
            ]
        },
    )
    assert deleted_question_submit.status_code == 400

    fetched_response = client.get(f"/api/v1/form-responses/{response_id}")
    assert fetched_response.status_code == 200
    assert fetched_response.json()["id"] == response_id
