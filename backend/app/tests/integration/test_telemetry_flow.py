"""Telemetría de participación: agrega response_sessions ya creadas
(vía el flujo público), no ejecuta ningún cálculo de scoring."""

import pytest
from httpx import AsyncClient


async def test_study_and_project_telemetry(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    project = seed_project

    item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "P1", "question_text": "Pregunta 1", "question_type": "NUMBER"},
        )
    ).json()

    variable_construct = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/structure-variables",
            json={"code": "BIENESTAR", "name": "Bienestar", "role": "OUTCOME"},
        )
    ).json()
    dimension = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/constructs",
            json={
                "parent_id": variable_construct["id"],
                "code": "BIENESTAR_EMOCIONAL",
                "name": "Bienestar emocional",
                "construct_type": "DIMENSION",
            },
        )
    ).json()
    assign_resp = await client.post(
        f"/api/v1/constructs/{dimension['id']}/items",
        json={"question_id": item["id"], "weight": 1},
    )
    assert assign_resp.status_code == 201, assign_resp.text
    variable_resp = await client.post(
        f"/api/v1/projects/{project.id}/variables",
        json={
            "instrument_version_id": version.id,
            "construct_id": variable_construct["id"],
            "code": "bienestar",
            "name": "Bienestar",
            "variable_type": "DERIVED",
            "data_type": "DECIMAL",
            "measurement_level": "SCALE",
            "role": "OUTCOME",
        },
    )
    assert variable_resp.status_code == 201, variable_resp.text

    survey = (
        await client.post(
            f"/api/v1/projects/{project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta telemetría",
            },
        )
    ).json()

    study = (
        await client.post(
            f"/api/v1/projects/{project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio telemetría", "study_type": "CUSTOM"},
        )
    ).json()
    assert study["instrument_id"] == _instrument.id
    assert study["instrument_name"] == _instrument.name
    await client.post(f"/api/v1/studies/{study['id']}/open")

    # Sesión 1: completa.
    session1 = (
        await client.post(f"/api/v1/public/studies/{study['public_id']}/response-sessions")
    ).json()
    await client.put(
        f"/api/v1/response-sessions/{session1['id']}/responses/{item['id']}",
        json={"numeric_value": 5},
    )
    await client.post(f"/api/v1/response-sessions/{session1['id']}/complete")

    # Sesión 2: iniciada pero nunca completada.
    await client.post(f"/api/v1/public/studies/{study['public_id']}/response-sessions")

    study_telemetry_resp = await client.get(f"/api/v1/studies/{study['id']}/telemetry")
    assert study_telemetry_resp.status_code == 200, study_telemetry_resp.text
    study_telemetry = study_telemetry_resp.json()

    assert study_telemetry["started_count"] == 2
    assert study_telemetry["instrument_id"] == _instrument.id
    assert study_telemetry["instrument_name"] == _instrument.name
    assert study_telemetry["completed_count"] == 1
    assert study_telemetry["abandoned_count"] == 0
    # El instrumento tiene 1 solo ítem: el floor de min_answered_count queda
    # acotado a min(5, 1) == 1, así que la sesión 1/1 (100%) sí alcanza VALID.
    assert study_telemetry["valid_count"] == 1
    assert study_telemetry["review_count"] == 0
    assert study_telemetry["excluded_count"] == 0
    assert study_telemetry["completion_rate"] == 0.5
    assert study_telemetry["avg_completion_pct"] == 100.0
    assert len(study_telemetry["series"]) >= 1
    assert study_telemetry["variables"] == [
        {
            "construct_id": variable_construct["id"],
            "variable_code": "bienestar",
            "variable_name": "Bienestar",
            "role": "OUTCOME",
            "question_count": 1,
            "sessions_started": 2,
            "sessions_answered": 1,
            "sessions_completed": 1,
            "completion_rate": 0.5,
            "avg_completion_pct": 50.0,
        }
    ]

    project_telemetry_resp = await client.get(f"/api/v1/projects/{project.id}/telemetry")
    assert project_telemetry_resp.status_code == 200
    project_telemetry = project_telemetry_resp.json()
    assert any(s["study_id"] == study["id"] for s in project_telemetry["studies"])


async def test_study_telemetry_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/studies/999999/telemetry")
    assert resp.status_code == 404


async def test_study_telemetry_participation_funnel_with_invitations(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    """Convocados/tasa recibida/tasa válida sólo deben poblarse cuando el
    estudio exige invitación individual (E-17) y hay invitaciones emitidas —
    ver TelemetryService._participation_funnel."""
    _instrument, version = seed_instrument_draft
    project = seed_project

    item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "P1", "question_text": "Pregunta 1", "question_type": "NUMBER"},
        )
    ).json()
    survey = (
        await client.post(
            f"/api/v1/projects/{project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta telemetría con invitaciones",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{project.id}/studies",
            json={
                "survey_id": survey["id"],
                "name": "Estudio con invitaciones",
                "study_type": "CUSTOM",
                "requires_invitation": True,
            },
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")

    tokens = (
        await client.post(f"/api/v1/studies/{study['id']}/invitations", json={"count": 3})
    ).json()["tokens"]
    assert len(tokens) == 3

    # Sólo 2 de las 3 invitaciones se consumen; la tercera queda sin usar.
    for token in tokens[:2]:
        session = (
            await client.post(
                f"/api/v1/public/studies/{study['public_id']}/response-sessions",
                json={"invitation_token": token},
            )
        ).json()
        await client.put(
            f"/api/v1/response-sessions/{session['id']}/responses/{item['id']}",
            json={"numeric_value": 5},
        )
        await client.post(f"/api/v1/response-sessions/{session['id']}/complete")

    telemetry = (await client.get(f"/api/v1/studies/{study['id']}/telemetry")).json()

    assert telemetry["invited_count"] == 3
    assert telemetry["started_count"] == 2
    assert telemetry["not_responded_count"] == 1
    assert telemetry["response_rate"] == pytest.approx(2 / 3)
    assert telemetry["valid_count"] == 2
    assert telemetry["valid_rate"] == pytest.approx(2 / 3)
    assert telemetry["median_duration_seconds"] is not None


async def test_study_telemetry_funnel_is_none_without_invitations(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    """Estudios de enlace público (requires_invitation=False, el default) no
    tienen una población objetivo contable: el funnel debe quedar en None en
    vez de fabricar una tasa con un denominador incorrecto."""
    _instrument, version = seed_instrument_draft
    project = seed_project
    await client.post(
        f"/api/v1/instrument-versions/{version.id}/items",
        json={"code": "P1", "question_text": "Pregunta 1", "question_type": "NUMBER"},
    )
    survey = (
        await client.post(
            f"/api/v1/projects/{project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta enlace público",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio enlace público", "study_type": "CUSTOM"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")
    await client.post(f"/api/v1/public/studies/{study['public_id']}/response-sessions")

    telemetry = (await client.get(f"/api/v1/studies/{study['id']}/telemetry")).json()

    assert telemetry["invited_count"] is None
    assert telemetry["not_responded_count"] is None
    assert telemetry["response_rate"] is None
    assert telemetry["valid_rate"] is None
