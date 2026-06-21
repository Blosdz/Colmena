from fastapi.testclient import TestClient


def create_project_payload(title: str = "Proyecto base") -> dict:
    return {
        "title": title,
        "research_type": "correlacional",
        "design_type": "no experimental transversal",
        "approach": "cuantitativo",
        "institution": "Universidad de prueba",
        "faculty": "Facultad de Ciencias Sociales",
        "career": "Psicologia",
        "sample_size_planned": 120,
    }


def test_health_returns_ok(client: TestClient):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_project(client: TestClient):
    response = client.post("/api/v1/projects", json=create_project_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Proyecto base"
    assert body["status"] == "draft"
    assert body["sample_size_current"] == 0
    assert body["id"]


def test_list_projects(client: TestClient):
    client.post("/api/v1/projects", json=create_project_payload("Proyecto listado"))

    response = client.get("/api/v1/projects")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "Proyecto listado"


def test_get_project_by_id(client: TestClient):
    created = client.post("/api/v1/projects", json=create_project_payload("Proyecto detalle")).json()

    response = client.get(f"/api/v1/projects/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_project(client: TestClient):
    created = client.post("/api/v1/projects", json=create_project_payload("Proyecto editable")).json()

    response = client.patch(
        f"/api/v1/projects/{created['id']}",
        json={
            "title": "Proyecto actualizado",
            "sample_size_current": 45,
            "status": "active",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Proyecto actualizado"
    assert body["sample_size_current"] == 45
    assert body["status"] == "active"


def test_soft_delete_project(client: TestClient):
    created = client.post("/api/v1/projects", json=create_project_payload("Proyecto eliminable")).json()

    response = client.delete(f"/api/v1/projects/{created['id']}")

    assert response.status_code == 200
    assert response.json() == {"status": "deleted", "id": created["id"]}


def test_get_after_delete_returns_404(client: TestClient):
    created = client.post("/api/v1/projects", json=create_project_payload("Proyecto oculto")).json()
    client.delete(f"/api/v1/projects/{created['id']}")

    response = client.get(f"/api/v1/projects/{created['id']}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"
