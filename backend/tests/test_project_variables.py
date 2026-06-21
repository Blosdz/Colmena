from fastapi.testclient import TestClient


def create_project(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={
            "title": "Proyecto con variables",
            "research_type": "correlacional",
            "approach": "cuantitativo",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_project_variables(client: TestClient):
    project = create_project(client)

    sex_response = client.post(
        f"/api/v1/projects/{project['id']}/variables",
        json={
            "name": "Sexo",
            "code": "sex",
            "variable_role": "sociodemographic",
            "measurement_level": "nominal",
            "data_type": "categorical",
        },
    )
    anxiety_response = client.post(
        f"/api/v1/projects/{project['id']}/variables",
        json={
            "name": "Ansiedad academica",
            "code": "anxiety",
            "variable_role": "main",
            "measurement_level": "ordinal",
            "data_type": "numeric",
            "is_required_for_analysis": True,
        },
    )

    assert sex_response.status_code == 201
    assert anxiety_response.status_code == 201
    assert sex_response.json()["variable_role"] == "sociodemographic"
    assert anxiety_response.json()["is_required_for_analysis"] is True


def test_list_update_and_soft_delete_project_variable(client: TestClient):
    project = create_project(client)
    created = client.post(
        f"/api/v1/projects/{project['id']}/variables",
        json={
            "name": "Edad",
            "code": "age",
            "variable_role": "sociodemographic",
            "measurement_level": "ratio",
            "data_type": "numeric",
        },
    ).json()

    listed = client.get(f"/api/v1/projects/{project['id']}/variables")
    fetched = client.get(f"/api/v1/project-variables/{created['id']}")
    updated = client.patch(
        f"/api/v1/project-variables/{created['id']}",
        json={"name": "Edad actual", "notes": "Variable numerica"},
    )
    deleted = client.delete(f"/api/v1/project-variables/{created['id']}")
    listed_after_delete = client.get(f"/api/v1/projects/{project['id']}/variables")

    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert fetched.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["name"] == "Edad actual"
    assert deleted.status_code == 200
    assert listed_after_delete.json()["total"] == 0
