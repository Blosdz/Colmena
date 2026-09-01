"""E-03: `raw_code`/`numeric_value` deben resolverse contra el catálogo de
opciones del ítem (`option_set`) cuando este existe."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.response import Response


async def _setup_study_with_choice_item(
    client: AsyncClient, seed_user, seed_project, version, *, with_catalog: bool
) -> tuple[dict, dict]:
    payload = {
        "code": "P1",
        "question_text": "¿Qué tan satisfecho estás?",
        "question_type": "SINGLE_CHOICE",
    }
    if with_catalog:
        payload["option_set"] = {
            "name": "Satisfacción",
            "options": [
                {"raw_code": "1", "label": "Poco", "numeric_value": 1},
                {"raw_code": "2", "label": "Mucho", "numeric_value": 2},
            ],
        }
    item = (
        await client.post(f"/api/v1/instrument-versions/{version.id}/items", json=payload)
    ).json()

    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta catálogo",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio catálogo", "study_type": "CUSTOM"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")
    response_session = (
        await client.post(f"/api/v1/studies/{study['id']}/response-sessions")
    ).json()
    return response_session, item


async def test_raw_code_outside_catalog_is_rejected(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    response_session, item = await _setup_study_with_choice_item(
        client, seed_user, seed_project, version, with_catalog=True
    )

    resp = await client.put(
        f"/api/v1/response-sessions/{response_session['id']}/responses/{item['id']}",
        json={"raw_code": "99"},
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error_code"] == "VALIDATION_ERROR"


async def test_raw_code_resolves_numeric_value_and_option_id(
    client: AsyncClient, session: AsyncSession, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    response_session, item = await _setup_study_with_choice_item(
        client, seed_user, seed_project, version, with_catalog=True
    )

    resp = await client.put(
        f"/api/v1/response-sessions/{response_session['id']}/responses/{item['id']}",
        json={"raw_code": "2"},
    )
    assert resp.status_code == 200, resp.text

    stmt = select(Response).where(
        Response.response_session_id == response_session["id"], Response.question_id == item["id"]
    )
    stored = (await session.execute(stmt)).scalar_one()
    assert stored.option_id is not None
    assert float(stored.numeric_value) == 2.0
    assert stored.raw_code == "2"


async def test_raw_code_with_inconsistent_numeric_value_rejected(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    response_session, item = await _setup_study_with_choice_item(
        client, seed_user, seed_project, version, with_catalog=True
    )

    resp = await client.put(
        f"/api/v1/response-sessions/{response_session['id']}/responses/{item['id']}",
        json={"raw_code": "1", "numeric_value": 999},
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error_code"] == "VALIDATION_ERROR"


async def test_raw_code_without_catalog_still_free_text(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    response_session, item = await _setup_study_with_choice_item(
        client, seed_user, seed_project, version, with_catalog=False
    )

    resp = await client.put(
        f"/api/v1/response-sessions/{response_session['id']}/responses/{item['id']}",
        json={"raw_code": "M"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["raw_code"] == "M"
