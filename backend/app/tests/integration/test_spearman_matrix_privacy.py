"""E-09: `include_points` en spearman-matrix nunca debe exponer coordenadas
individuales a un caller anónimo o sin rol elevado sobre el proyecto, y los
puntos (aunque agregados en bins) nunca deben persistirse ni aparecer en
`GET /analysis-runs/{id}` ni en un reporte descargable."""

import json

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User


async def _setup_scored_study(client: AsyncClient, seed_user, seed_project, version) -> tuple[dict, dict, dict]:
    variable = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/structure-variables",
            json={"code": "VAR", "name": "Variable"},
        )
    ).json()
    likert_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "L1", "question_text": "Ítem Likert", "question_type": "LIKERT"},
        )
    ).json()
    x1_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "X1", "question_text": "Exógena 1", "question_type": "NUMBER"},
        )
    ).json()
    x2_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "X2", "question_text": "Exógena 2", "question_type": "NUMBER"},
        )
    ).json()

    construct = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/constructs",
            json={"parent_id": variable["id"], "code": "D1", "name": "Dimensión", "construct_type": "DIMENSION"},
        )
    ).json()
    await client.post(
        f"/api/v1/constructs/{construct['id']}/items",
        json={"question_id": likert_item["id"], "weight": 1},
    )

    x1_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "x1",
                "name": "Exógena 1",
                "variable_type": "EXOGENOUS",
                "data_type": "INTEGER",
                "measurement_level": "SCALE",
                "role": "EXOGENOUS",
                "question_id": x1_item["id"],
            },
        )
    ).json()
    x2_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "x2",
                "name": "Exógena 2",
                "variable_type": "EXOGENOUS",
                "data_type": "INTEGER",
                "measurement_level": "SCALE",
                "role": "EXOGENOUS",
                "question_id": x2_item["id"],
            },
        )
    ).json()

    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta spearman",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio spearman", "study_type": "ACADEMIC"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")

    rows = [("1", 10, 12), ("2", 12, 15), ("3", 20, 22), ("4", 28, 30), ("5", 35, 40), ("3", 18, 21)]
    for raw_code, x1_value, x2_value in rows:
        rs = (await client.post(f"/api/v1/studies/{study['id']}/response-sessions")).json()
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{likert_item['id']}",
            json={"raw_code": raw_code},
        )
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{x1_item['id']}",
            json={"numeric_value": x1_value},
        )
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{x2_item['id']}",
            json={"numeric_value": x2_value},
        )
        await client.post(f"/api/v1/response-sessions/{rs['id']}/complete")

    scoring_resp = await client.post(f"/api/v1/studies/{study['id']}/scoring")
    assert scoring_resp.status_code == 200, scoring_resp.text

    return study, x1_var, x2_var


async def test_include_points_false_by_default(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, x1_var, x2_var = await _setup_scored_study(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/spearman-matrix",
        json={"exogenous_variable_ids": [x1_var["id"], x2_var["id"]]},
    )
    assert resp.status_code == 200, resp.text
    for cell in resp.json()["cells"]:
        assert cell["points_binned"] == []


async def test_include_points_requires_authentication(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, x1_var, x2_var = await _setup_scored_study(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/spearman-matrix",
        json={"exogenous_variable_ids": [x1_var["id"], x2_var["id"]], "include_points": True},
    )
    assert resp.status_code == 401, resp.text


async def test_include_points_requires_elevated_role(
    client: AsyncClient, session: AsyncSession, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, x1_var, x2_var = await _setup_scored_study(client, seed_user, seed_project, version)

    outsider = User(email="outsider@colmena.dev", username="outsider", status="ACTIVE")
    session.add(outsider)
    await session.commit()
    await session.refresh(outsider)
    token = create_access_token(outsider.id)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/spearman-matrix",
        json={"exogenous_variable_ids": [x1_var["id"], x2_var["id"]], "include_points": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403, resp.text


async def test_include_points_returns_bins_for_project_owner(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, x1_var, x2_var = await _setup_scored_study(client, seed_user, seed_project, version)
    token = create_access_token(seed_user.id)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/spearman-matrix",
        json={"exogenous_variable_ids": [x1_var["id"], x2_var["id"]], "include_points": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "points" not in json.dumps(body).replace("points_binned", "")
    x1_x2_cell = next(
        c for c in body["cells"] if {c["x_key"], c["y_key"]} == {f"variable:{x1_var['id']}", f"variable:{x2_var['id']}"}
    )
    assert x1_x2_cell["points_binned"] != []
    for bucket in x1_x2_cell["points_binned"]:
        assert set(bucket) == {"x_bin_center", "y_bin_center", "n"}


async def test_report_bundle_excludes_points_even_for_owner(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, x1_var, x2_var = await _setup_scored_study(client, seed_user, seed_project, version)
    token = create_access_token(seed_user.id)

    spearman_resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/spearman-matrix",
        json={"exogenous_variable_ids": [x1_var["id"], x2_var["id"]], "include_points": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert spearman_resp.status_code == 200, spearman_resp.text

    # output_format=JSON a propósito: la supresión pasa en _build_bundle /
    # _serialize_result (report_service.py), antes de cualquier renderizado
    # de formato — pedir JSON deja verificar el texto serializado directo,
    # en vez de decodificar el binario DOCX (el default nuevo).
    report_resp = await client.post(
        f"/api/v1/studies/{study['id']}/reports", json={"output_format": "JSON"}
    )
    assert report_resp.status_code == 201, report_resp.text
    report = report_resp.json()

    download_resp = await client.get(f"/api/v1/reports/{report['id']}/download")
    assert download_resp.status_code == 200
    assert "points_binned" not in download_resp.text
    assert '"points"' not in download_resp.text


async def test_get_analysis_run_never_exposes_points(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, x1_var, x2_var = await _setup_scored_study(client, seed_user, seed_project, version)
    token = create_access_token(seed_user.id)

    spearman_resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/spearman-matrix",
        json={"exogenous_variable_ids": [x1_var["id"], x2_var["id"]], "include_points": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    run_id = spearman_resp.json()["analysis_run_id"]

    # Sin autenticación, y aun así intencionalmente: el punto es que el
    # backend nunca persiste points_binned, así que ni siquiera hace falta
    # un control de rol en este endpoint para estar a salvo.
    run_resp = await client.get(f"/api/v1/analysis-runs/{run_id}")
    assert run_resp.status_code == 200
    for result in run_resp.json()["results"]:
        assert "points_binned" not in result["result_data"]
        assert "points" not in result["result_data"]
