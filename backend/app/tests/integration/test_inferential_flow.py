"""Flujo Fase 7 (inferencial): chi-cuadrado, comparar grupos, correlación,
confiabilidad (harness §24-26, §47, §59)."""

from httpx import AsyncClient


async def _base_setup(client: AsyncClient, seed_user, seed_project, version):
    score_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "SCORE", "question_text": "Puntaje", "question_type": "NUMBER"},
        )
    ).json()
    group_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "GRUPO", "question_text": "Grupo", "question_type": "SINGLE_CHOICE"},
        )
    ).json()
    other_score_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "SCORE2", "question_text": "Puntaje 2", "question_type": "NUMBER"},
        )
    ).json()

    score_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "score",
                "name": "Puntaje",
                "variable_type": "QUESTION",
                "data_type": "INTEGER",
                "measurement_level": "SCALE",
                "question_id": score_item["id"],
            },
        )
    ).json()
    group_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "grupo",
                "name": "Grupo",
                "variable_type": "QUESTION",
                "data_type": "CATEGORY",
                "measurement_level": "NOMINAL",
                "question_id": group_item["id"],
            },
        )
    ).json()
    score2_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "score2",
                "name": "Puntaje 2",
                "variable_type": "QUESTION",
                "data_type": "INTEGER",
                "measurement_level": "SCALE",
                "question_id": other_score_item["id"],
            },
        )
    ).json()

    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta inferencial",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio inferencial", "study_type": "ACADEMIC"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")

    rows = [
        (10, "A", 15),
        (12, "A", 18),
        (11, "A", 17),
        (30, "B", 35),
        (32, "B", 38),
        (31, "B", 37),
    ]
    for score, group, score2 in rows:
        rs = (await client.post(f"/api/v1/studies/{study['id']}/response-sessions")).json()
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{score_item['id']}",
            json={"numeric_value": score},
        )
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{group_item['id']}",
            json={"raw_code": group},
        )
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{other_score_item['id']}",
            json={"numeric_value": score2},
        )
        await client.post(f"/api/v1/response-sessions/{rs['id']}/complete")

    return study, score_var, group_var, score2_var


async def test_compare_groups_two_groups_uses_mann_whitney(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, score_var, group_var, _score2_var = await _base_setup(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/compare-groups",
        json={"dependent_variable_id": score_var["id"], "group_variable_id": group_var["id"]},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()["results"][0]
    assert result["result_type"] == "MANN_WHITNEY"
    assert result["p_value"] is not None


async def test_correlation_spearman(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    study, score_var, _group_var, score2_var = await _base_setup(client, seed_user, seed_project, version)

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/correlation",
        json={"variable_x_id": score_var["id"], "variable_y_id": score2_var["id"]},
    )
    assert resp.status_code == 200, resp.text
    result = resp.json()["results"][0]
    assert result["result_type"] == "SPEARMAN"
    assert result["statistic_value"] > 0.9  # fuertemente correlacionados por diseño


async def test_correlation_insufficient_sample(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft

    item_x = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "X", "question_text": "X", "question_type": "NUMBER"},
        )
    ).json()
    item_y = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "Y", "question_text": "Y", "question_type": "NUMBER"},
        )
    ).json()
    var_x = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "x",
                "name": "X",
                "variable_type": "QUESTION",
                "data_type": "INTEGER",
                "measurement_level": "SCALE",
                "question_id": item_x["id"],
            },
        )
    ).json()
    var_y = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "y",
                "name": "Y",
                "variable_type": "QUESTION",
                "data_type": "INTEGER",
                "measurement_level": "SCALE",
                "question_id": item_y["id"],
            },
        )
    ).json()
    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta corta",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio corto", "study_type": "ACADEMIC"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")

    rs = (await client.post(f"/api/v1/studies/{study['id']}/response-sessions")).json()
    await client.put(f"/api/v1/response-sessions/{rs['id']}/responses/{item_x['id']}", json={"numeric_value": 1})
    await client.put(f"/api/v1/response-sessions/{rs['id']}/responses/{item_y['id']}", json={"numeric_value": 2})
    await client.post(f"/api/v1/response-sessions/{rs['id']}/complete")

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/correlation",
        json={"variable_x_id": var_x["id"], "variable_y_id": var_y["id"]},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "INSUFFICIENT_SAMPLE"


async def test_chi_square_via_generic_dispatch(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft

    sex_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "SEXO", "question_text": "Sexo", "question_type": "SINGLE_CHOICE"},
        )
    ).json()
    group_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "GRUPO", "question_text": "Grupo", "question_type": "SINGLE_CHOICE"},
        )
    ).json()
    sex_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "sexo",
                "name": "Sexo",
                "variable_type": "QUESTION",
                "data_type": "CATEGORY",
                "measurement_level": "NOMINAL",
                "question_id": sex_item["id"],
            },
        )
    ).json()
    group_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "grupo2",
                "name": "Grupo",
                "variable_type": "QUESTION",
                "data_type": "CATEGORY",
                "measurement_level": "NOMINAL",
                "question_id": group_item["id"],
            },
        )
    ).json()
    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta chi2",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio chi2", "study_type": "ACADEMIC"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")

    for sex, group in [("M", "A"), ("M", "B"), ("F", "A"), ("F", "A"), ("F", "B"), ("M", "A")]:
        rs = (await client.post(f"/api/v1/studies/{study['id']}/response-sessions")).json()
        await client.put(f"/api/v1/response-sessions/{rs['id']}/responses/{sex_item['id']}", json={"raw_code": sex})
        await client.put(f"/api/v1/response-sessions/{rs['id']}/responses/{group_item['id']}", json={"raw_code": group})
        await client.post(f"/api/v1/response-sessions/{rs['id']}/complete")

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analysis-runs",
        json={
            "analysis_type": "CHI_SQUARE",
            "parameters": {"row_variable_id": sex_var["id"], "column_variable_id": group_var["id"]},
        },
    )
    assert resp.status_code == 201, resp.text
    result = resp.json()["results"][0]
    assert result["result_type"] == "CHI_SQUARE"


async def test_reliability_cronbach_and_omega(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft

    items = []
    variable = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/structure-variables",
            json={"code": "VAR", "name": "Variable"},
        )
    ).json()
    for code in ["I1", "I2", "I3"]:
        item = (
            await client.post(
                f"/api/v1/instrument-versions/{version.id}/items",
                json={"code": code, "question_text": code, "question_type": "LIKERT"},
            )
        ).json()
        items.append(item)

    construct = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/constructs",
            json={"parent_id": variable["id"], "code": "D1", "name": "Constructo", "construct_type": "DIMENSION"},
        )
    ).json()
    for item in items:
        await client.post(
            f"/api/v1/constructs/{construct['id']}/items",
            json={"question_id": item["id"], "weight": 1},
        )

    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta confiabilidad",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio confiabilidad", "study_type": "ACADEMIC"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")

    respondent_values = [[1, 1, 2], [2, 2, 3], [3, 3, 4], [4, 5, 5], [5, 4, 5]]
    for values in respondent_values:
        rs = (await client.post(f"/api/v1/studies/{study['id']}/response-sessions")).json()
        for item, value in zip(items, values, strict=True):
            await client.put(
                f"/api/v1/response-sessions/{rs['id']}/responses/{item['id']}",
                json={"numeric_value": value},
            )
        await client.post(f"/api/v1/response-sessions/{rs['id']}/complete")

    resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/reliability",
        json={"construct_id": construct["id"], "methods": ["CRONBACH_ALPHA", "MCDONALD_OMEGA"]},
    )
    assert resp.status_code == 200, resp.text
    results = {r["result_type"]: r for r in resp.json()["results"]}
    assert "CRONBACH_ALPHA" in results
    assert "MCDONALD_OMEGA" in results
    assert results["CRONBACH_ALPHA"]["numeric_value"] is not None
