"""Flujo Fase 8 (exports): CSV, XLSX, JSON + descarga (harness §37)."""

import json

from httpx import AsyncClient


async def _setup_study_with_data(client: AsyncClient, seed_user, seed_project, version):
    item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "EDAD", "question_text": "Edad", "question_type": "NUMBER"},
        )
    ).json()
    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta export",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio export", "study_type": "ACADEMIC"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")

    sessions = []
    for age in (20, 25, 30):
        rs = (await client.post(f"/api/v1/studies/{study['id']}/response-sessions")).json()
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{item['id']}",
            json={"numeric_value": age},
        )
        await client.post(f"/api/v1/response-sessions/{rs['id']}/complete")
        sessions.append(rs)

    return study, sessions


async def test_csv_export_long_and_download(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, _sessions = await _setup_study_with_data(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/exports", json={"export_type": "CSV", "dataset_shape": "LONG"}
    )
    assert resp.status_code == 201, resp.text
    export = resp.json()
    assert export["status"] == "COMPLETED"
    assert export["row_count"] == 3

    download_resp = await client.get(f"/api/v1/exports/{export['id']}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"].startswith("text/csv")
    assert "case_id" in download_resp.text


async def test_xlsx_export_wide(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, _sessions = await _setup_study_with_data(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/exports", json={"export_type": "XLSX", "dataset_shape": "WIDE"}
    )
    assert resp.status_code == 201, resp.text
    export = resp.json()
    assert export["status"] == "COMPLETED"
    assert export["row_count"] == 3

    download_resp = await client.get(f"/api/v1/exports/{export['id']}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(download_resp.content) > 0


async def test_json_export_content(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, _sessions = await _setup_study_with_data(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/exports", json={"export_type": "JSON", "dataset_shape": "LONG"}
    )
    export = resp.json()

    download_resp = await client.get(f"/api/v1/exports/{export['id']}/download")
    data = json.loads(download_resp.text)
    assert len(data) == 3
    assert data[0]["variable_code"] is None or "numeric_value" in data[0]


async def test_unimplemented_export_type_fails_cleanly(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, _sessions = await _setup_study_with_data(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/exports", json={"export_type": "SPSS", "dataset_shape": "LONG"}
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "VALIDATION_ERROR"

    # El registro de exportación queda como FAILED, no se pierde.
    get_resp = await client.get(f"/api/v1/exports/1")
    assert get_resp.json()["status"] == "FAILED"


async def test_export_never_exposes_session_identifiers(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    """E-10: el CSV debe usar un `case_id` secuencial, nunca el `public_id`
    ni el `anonymous_token` de la sesión (identificadores estables que
    permitirían reidentificar por cruce con logs de invitación)."""
    _instrument, version = seed_instrument_draft
    study, sessions = await _setup_study_with_data(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/exports", json={"export_type": "CSV", "dataset_shape": "LONG"}
    )
    export = resp.json()
    download_resp = await client.get(f"/api/v1/exports/{export['id']}/download")

    for rs in sessions:
        assert rs["public_id"] not in download_resp.text
        assert rs["anonymous_token"] not in download_resp.text
