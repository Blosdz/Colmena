from fastapi.testclient import TestClient


def create_project(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={"title": "Proyecto formulario"},
    )
    assert response.status_code == 201
    return response.json()


def create_variable(client: TestClient, project_id: str, name: str, code: str, role: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/variables",
        json={
            "name": name,
            "code": code,
            "variable_role": role,
            "measurement_level": "ordinal" if role == "main" else "nominal",
            "data_type": "numeric" if role == "main" else "categorical",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_form_structure_crud_flow(client: TestClient):
    project = create_project(client)
    sex_variable = create_variable(client, project["id"], "Sexo", "sex", "sociodemographic")
    anxiety_variable = create_variable(client, project["id"], "Ansiedad academica", "anxiety", "main")

    form = client.post(
        f"/api/v1/projects/{project['id']}/forms",
        json={
            "title": "Formulario de investigacion",
            "description": "Base del formulario",
            "instructions": "Responda con sinceridad",
        },
    )
    assert form.status_code == 201
    form_data = form.json()

    section_general = client.post(
        f"/api/v1/forms/{form_data['id']}/sections",
        json={"title": "Datos generales", "sort_order": 1},
    )
    section_instrument = client.post(
        f"/api/v1/forms/{form_data['id']}/sections",
        json={"title": "Instrumento", "sort_order": 2},
    )
    assert section_general.status_code == 201
    assert section_instrument.status_code == 201
    general_data = section_general.json()
    instrument_section_data = section_instrument.json()

    instrument = client.post(
        f"/api/v1/forms/{form_data['id']}/instruments",
        json={
            "name": "Escala de prueba",
            "project_variable_id": anxiety_variable["id"],
            "response_scale_name": "Likert de 5 puntos",
            "scoring_method": "suma total",
        },
    )
    assert instrument.status_code == 201
    instrument_data = instrument.json()

    dimension = client.post(
        f"/api/v1/form-instruments/{instrument_data['id']}/dimensions",
        json={"name": "Dimension 1", "sort_order": 1},
    )
    assert dimension.status_code == 201
    dimension_data = dimension.json()

    sex_question = client.post(
        f"/api/v1/forms/{form_data['id']}/questions",
        json={
            "section_id": general_data["id"],
            "project_variable_id": sex_variable["id"],
            "code": "sex",
            "label": "Sexo",
            "question_type": "single_choice",
            "question_role": "sociodemographic",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "sort_order": 1,
        },
    )
    assert sex_question.status_code == 201
    sex_question_data = sex_question.json()

    option_male = client.post(
        f"/api/v1/form-questions/{sex_question_data['id']}/options",
        json={"label": "Masculino", "value": "male", "sort_order": 1},
    )
    option_female = client.post(
        f"/api/v1/form-questions/{sex_question_data['id']}/options",
        json={"label": "Femenino", "value": "female", "sort_order": 2},
    )
    assert option_male.status_code == 201
    assert option_female.status_code == 201

    likert_question = client.post(
        f"/api/v1/forms/{form_data['id']}/questions",
        json={
            "section_id": instrument_section_data["id"],
            "instrument_id": instrument_data["id"],
            "dimension_id": dimension_data["id"],
            "project_variable_id": anxiety_variable["id"],
            "code": "item_01",
            "label": "Siento tension al rendir examenes",
            "question_type": "likert",
            "question_role": "dimension_item",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "is_scored": True,
            "sort_order": 2,
        },
    )
    assert likert_question.status_code == 201
    likert_question_data = likert_question.json()

    likert_options = []
    for score in range(1, 6):
        option_response = client.post(
            f"/api/v1/form-questions/{likert_question_data['id']}/options",
            json={
                "label": f"Opcion {score}",
                "value": str(score),
                "score": float(score),
                "sort_order": score,
            },
        )
        assert option_response.status_code == 201
        likert_options.append(option_response.json())

    question_list = client.get(f"/api/v1/forms/{form_data['id']}/questions")
    option_list = client.get(f"/api/v1/form-questions/{likert_question_data['id']}/options")
    deleted = client.delete(f"/api/v1/form-questions/{sex_question_data['id']}")
    question_list_after_delete = client.get(f"/api/v1/forms/{form_data['id']}/questions")

    assert question_list.status_code == 200
    assert question_list.json()["total"] == 2
    assert option_list.status_code == 200
    assert option_list.json()["total"] == 5
    assert deleted.status_code == 200
    assert question_list_after_delete.json()["total"] == 1
    assert question_list_after_delete.json()["items"][0]["id"] == likert_question_data["id"]
