from fastapi.testclient import TestClient


def setup_form_structure(client: TestClient) -> dict:
    project = client.post(
        "/api/v1/projects",
        json={"title": "Proyecto respuestas", "approach": "cuantitativo"},
    ).json()

    sex_variable = client.post(
        f"/api/v1/projects/{project['id']}/variables",
        json={
            "name": "Sexo",
            "code": "sex",
            "variable_role": "sociodemographic",
            "measurement_level": "nominal",
            "data_type": "categorical",
        },
    ).json()
    anxiety_variable = client.post(
        f"/api/v1/projects/{project['id']}/variables",
        json={
            "name": "Ansiedad academica",
            "code": "anxiety",
            "variable_role": "main",
            "measurement_level": "ordinal",
            "data_type": "numeric",
        },
    ).json()

    form = client.post(
        f"/api/v1/projects/{project['id']}/forms",
        json={"title": "Formulario de respuestas"},
    ).json()
    section = client.post(
        f"/api/v1/forms/{form['id']}/sections",
        json={"title": "Datos", "sort_order": 1},
    ).json()
    instrument = client.post(
        f"/api/v1/forms/{form['id']}/instruments",
        json={"name": "Escala de prueba", "project_variable_id": anxiety_variable["id"]},
    ).json()
    dimension = client.post(
        f"/api/v1/form-instruments/{instrument['id']}/dimensions",
        json={"name": "Dimension 1"},
    ).json()

    sex_question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "section_id": section["id"],
            "project_variable_id": sex_variable["id"],
            "code": "sex",
            "label": "Sexo",
            "question_type": "single_choice",
            "question_role": "sociodemographic",
            "measurement_level": "nominal",
            "data_type": "categorical",
        },
    ).json()
    male_option = client.post(
        f"/api/v1/form-questions/{sex_question['id']}/options",
        json={"label": "Masculino", "value": "male", "sort_order": 1},
    ).json()
    female_option = client.post(
        f"/api/v1/form-questions/{sex_question['id']}/options",
        json={"label": "Femenino", "value": "female", "sort_order": 2},
    ).json()

    likert_question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "section_id": section["id"],
            "instrument_id": instrument["id"],
            "dimension_id": dimension["id"],
            "project_variable_id": anxiety_variable["id"],
            "code": "item_01",
            "label": "Siento tension al rendir examenes",
            "question_type": "likert",
            "question_role": "dimension_item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "is_scored": True,
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

    return {
        "project": project,
        "form": form,
        "sex_question": sex_question,
        "male_option": male_option,
        "female_option": female_option,
        "likert_question": likert_question,
        "likert_options": likert_options,
    }


def test_create_and_get_internal_form_response(client: TestClient):
    data = setup_form_structure(client)

    create_response = client.post(
        f"/api/v1/forms/{data['form']['id']}/responses",
        json={
            "respondent_code": "R-001",
            "status": "complete",
            "source": "internal",
            "answers": [
                {
                    "question_id": data["sex_question"]["id"],
                    "option_id": data["female_option"]["id"],
                },
                {
                    "question_id": data["likert_question"]["id"],
                    "option_id": data["likert_options"][4]["id"],
                },
            ],
        },
    )

    assert create_response.status_code == 201
    response_data = create_response.json()
    assert response_data["form_id"] == data["form"]["id"]
    assert len(response_data["answers"]) == 2
    assert response_data["answers"][1]["score_value"] == 5.0

    listed = client.get(f"/api/v1/forms/{data['form']['id']}/responses")
    fetched = client.get(f"/api/v1/form-responses/{response_data['id']}")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert fetched.status_code == 200
    assert fetched.json()["id"] == response_data["id"]
    assert len(fetched.json()["answers"]) == 2
