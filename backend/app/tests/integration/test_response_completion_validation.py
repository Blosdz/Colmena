"""E-04: `complete_session` ya no acepta sesiones vacías como VALID/PENDING.

`validation_status` combina un umbral de completitud (60% por defecto) con un
mínimo absoluto explícito de ítems respondidos, acotado por el total de
ítems del instrumento (para que un instrumento corto pueda alcanzar VALID
al 100%). Ambos criterios son configurables vía
`study.settings.response_validation`.
"""

from httpx import AsyncClient


async def _create_survey_and_open_study(
    client: AsyncClient, seed_user, seed_project, version, item_count: int, *, settings: dict | None = None
) -> tuple[dict, list[dict]]:
    items = []
    for index in range(item_count):
        item = (
            await client.post(
                f"/api/v1/instrument-versions/{version.id}/items",
                json={
                    "code": f"P{index + 1}",
                    "question_text": f"Pregunta {index + 1}",
                    "question_type": "NUMBER",
                },
            )
        ).json()
        items.append(item)

    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": f"Encuesta {item_count} ítems",
            },
        )
    ).json()

    study_payload = {
        "survey_id": survey["id"],
        "name": f"Estudio {item_count} ítems",
        "study_type": "CUSTOM",
    }
    if settings is not None:
        study_payload["settings"] = settings
    study = (
        await client.post(f"/api/v1/projects/{seed_project.id}/studies", json=study_payload)
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")
    return study, items


async def _answer(client: AsyncClient, session_id: int, items: list[dict], count: int) -> None:
    for item in items[:count]:
        resp = await client.put(
            f"/api/v1/response-sessions/{session_id}/responses/{item['id']}",
            json={"numeric_value": 1},
        )
        assert resp.status_code == 200, resp.text


async def test_complete_session_with_zero_responses_is_excluded(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, _items = await _create_survey_and_open_study(client, seed_user, seed_project, version, 3)

    response_session = (
        await client.post(f"/api/v1/studies/{study['id']}/response-sessions")
    ).json()
    completed = (
        await client.post(f"/api/v1/response-sessions/{response_session['id']}/complete")
    ).json()

    assert completed["status"] == "COMPLETED"
    assert completed["validation_status"] == "EXCLUDED"
    assert "sin respuestas" in completed["exclusion_reason"]


async def test_complete_session_below_min_answered_count_is_excluded(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    """6 ítems, 4 respondidas = 66.7% (>=60%) pero 4 < floor(min(5,6)=5)."""
    _instrument, version = seed_instrument_draft
    study, items = await _create_survey_and_open_study(client, seed_user, seed_project, version, 6)

    response_session = (
        await client.post(f"/api/v1/studies/{study['id']}/response-sessions")
    ).json()
    await _answer(client, response_session["id"], items, 4)
    completed = (
        await client.post(f"/api/v1/response-sessions/{response_session['id']}/complete")
    ).json()

    assert completed["completion_pct"] > 60.0
    assert completed["validation_status"] == "EXCLUDED"
    assert "se requieren al menos" in completed["exclusion_reason"]


async def test_complete_session_review_when_below_percent_but_above_count(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    """10 ítems, 5 respondidas = 50% (<60%) pero 5 >= floor(min(5,10)=5)."""
    _instrument, version = seed_instrument_draft
    study, items = await _create_survey_and_open_study(client, seed_user, seed_project, version, 10)

    response_session = (
        await client.post(f"/api/v1/studies/{study['id']}/response-sessions")
    ).json()
    await _answer(client, response_session["id"], items, 5)
    completed = (
        await client.post(f"/api/v1/response-sessions/{response_session['id']}/complete")
    ).json()

    assert completed["completion_pct"] == 50.0
    assert completed["validation_status"] == "REVIEW"


async def test_complete_session_valid_when_above_threshold(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, items = await _create_survey_and_open_study(client, seed_user, seed_project, version, 10)

    response_session = (
        await client.post(f"/api/v1/studies/{study['id']}/response-sessions")
    ).json()
    await _answer(client, response_session["id"], items, 7)
    completed = (
        await client.post(f"/api/v1/response-sessions/{response_session['id']}/complete")
    ).json()

    assert completed["completion_pct"] == 70.0
    assert completed["validation_status"] == "VALID"


async def test_complete_session_respects_configurable_thresholds(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    """Con los defaults, 2/4 (50%) queda EXCLUDED (floor min(5,4)=4 > 2).

    Con `settings.response_validation` override (min_answered_count=1,
    min_completion_percent=50), la misma sesión pasa a VALID.
    """
    _instrument, version = seed_instrument_draft
    study, items = await _create_survey_and_open_study(
        client,
        seed_user,
        seed_project,
        version,
        4,
        settings={"response_validation": {"min_answered_count": 1, "min_completion_percent": 50}},
    )

    response_session = (
        await client.post(f"/api/v1/studies/{study['id']}/response-sessions")
    ).json()
    await _answer(client, response_session["id"], items, 2)
    completed = (
        await client.post(f"/api/v1/response-sessions/{response_session['id']}/complete")
    ).json()

    assert completed["completion_pct"] == 50.0
    assert completed["validation_status"] == "VALID"
