"""Encuesta pública: resolución de estudio por public_id sin autenticación.

DRAFT -> 404 (no filtra existencia), OPEN -> bundle sin datos internos,
crear sesión -> responder -> completar -> aparece en el dataset del owner.
"""

from httpx import AsyncClient


async def _build_open_study(client: AsyncClient, seed_user, seed_project, seed_instrument_draft):
    _instrument, version = seed_instrument_draft
    project = seed_project

    item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={
                "code": "P1",
                "question_text": "¿Qué tan satisfecho estás?",
                "question_type": "SINGLE_CHOICE",
                "option_set": {
                    "name": "Satisfacción",
                    "options": [
                        {"raw_code": "1", "label": "Poco"},
                        {"raw_code": "2", "label": "Mucho"},
                    ],
                },
            },
        )
    ).json()

    survey = (
        await client.post(
            f"/api/v1/projects/{project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta pública",
            },
        )
    ).json()

    study = (
        await client.post(
            f"/api/v1/projects/{project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio público", "study_type": "CUSTOM"},
        )
    ).json()

    return study, item


async def test_public_study_not_found_and_draft_are_both_404(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    random_uuid_resp = await client.get(
        "/api/v1/public/studies/00000000-0000-0000-0000-000000000000"
    )
    assert random_uuid_resp.status_code == 404
    assert random_uuid_resp.json()["error_code"] == "PUBLIC_RESOURCE_UNAVAILABLE"

    study, _item = await _build_open_study(client, seed_user, seed_project, seed_instrument_draft)
    assert study["status"] == "DRAFT"

    draft_resp = await client.get(f"/api/v1/public/studies/{study['public_id']}")
    assert draft_resp.status_code == 404
    assert draft_resp.json() == random_uuid_resp.json()


async def test_public_survey_full_flow(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    study, item = await _build_open_study(client, seed_user, seed_project, seed_instrument_draft)

    open_resp = await client.post(f"/api/v1/studies/{study['id']}/open")
    assert open_resp.status_code == 200

    bundle_resp = await client.get(f"/api/v1/public/studies/{study['public_id']}")
    assert bundle_resp.status_code == 200, bundle_resp.text
    bundle = bundle_resp.json()

    assert bundle["study_public_id"] == study["public_id"]
    assert len(bundle["questions"]) == 1
    question = bundle["questions"][0]
    assert question["id"] == item["id"]
    assert len(question["options"]) == 2

    # No debe filtrar ids internos del propietario/proyecto/survey.
    assert "owner_user_id" not in bundle
    assert "project_id" not in bundle

    session_resp = await client.post(
        f"/api/v1/public/studies/{study['public_id']}/response-sessions"
    )
    assert session_resp.status_code == 201, session_resp.text
    response_session = session_resp.json()
    assert response_session["status"] == "STARTED"

    answer_resp = await client.put(
        f"/api/v1/response-sessions/{response_session['id']}/responses/{question['id']}",
        json={"option_id": question["options"][0]["id"]},
    )
    assert answer_resp.status_code == 200, answer_resp.text

    complete_resp = await client.post(
        f"/api/v1/response-sessions/{response_session['id']}/complete"
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"

    long_resp = await client.get(f"/api/v1/studies/{study['id']}/dataset/long")
    assert long_resp.status_code == 200
    rows = long_resp.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["raw_code"] == question["options"][0]["raw_code"]


async def test_public_session_rejected_after_end_at(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    """E-17: `end_at` no se chequeaba en absoluto — un estudio OPEN seguía
    aceptando respuestas públicas por siempre."""
    study, _item = await _build_open_study(client, seed_user, seed_project, seed_instrument_draft)
    await client.post(f"/api/v1/studies/{study['id']}/open")
    await client.patch(f"/api/v1/studies/{study['id']}", json={"end_at": "2000-01-01T00:00:00Z"})

    resp = await client.post(f"/api/v1/public/studies/{study['public_id']}/response-sessions")
    assert resp.status_code == 404, resp.text
    assert resp.json()["error_code"] == "PUBLIC_RESOURCE_UNAVAILABLE"


async def test_internal_session_rejected_after_end_at(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    study, _item = await _build_open_study(client, seed_user, seed_project, seed_instrument_draft)
    await client.post(f"/api/v1/studies/{study['id']}/open")
    await client.patch(f"/api/v1/studies/{study['id']}", json={"end_at": "2000-01-01T00:00:00Z"})

    resp = await client.post(f"/api/v1/studies/{study['id']}/response-sessions")
    assert resp.status_code == 409, resp.text
    assert resp.json()["error_code"] == "CONFLICT"
