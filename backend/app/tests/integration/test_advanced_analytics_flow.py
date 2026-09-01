"""Flujo Fase 9 (avanzado): regresión logística y k-means."""

from httpx import AsyncClient


async def test_logistic_regression_and_kmeans(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft

    predictor_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "PRED", "question_text": "Predictor", "question_type": "NUMBER"},
        )
    ).json()
    outcome_item = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/items",
            json={"code": "OUT", "question_text": "Resultado", "question_type": "SINGLE_CHOICE"},
        )
    ).json()

    predictor_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "pred",
                "name": "Predictor",
                "variable_type": "QUESTION",
                "data_type": "INTEGER",
                "measurement_level": "SCALE",
                "question_id": predictor_item["id"],
            },
        )
    ).json()
    outcome_var = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/variables",
            json={
                "code": "out",
                "name": "Resultado",
                "variable_type": "QUESTION",
                "data_type": "CATEGORY",
                "measurement_level": "BINARY",
                "question_id": outcome_item["id"],
            },
        )
    ).json()

    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta avanzada",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={"survey_id": survey["id"], "name": "Estudio avanzado", "study_type": "ACADEMIC"},
        )
    ).json()
    await client.post(f"/api/v1/studies/{study['id']}/open")

    rows = [(1, "NO"), (2, "NO"), (3, "NO"), (4, "NO"), (5, "NO"),
            (10, "SI"), (11, "SI"), (12, "SI"), (13, "SI"), (14, "SI")]
    for pred, out in rows:
        rs = (await client.post(f"/api/v1/studies/{study['id']}/response-sessions")).json()
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{predictor_item['id']}",
            json={"numeric_value": pred},
        )
        await client.put(
            f"/api/v1/response-sessions/{rs['id']}/responses/{outcome_item['id']}",
            json={"raw_code": out},
        )
        await client.post(f"/api/v1/response-sessions/{rs['id']}/complete")

    regression_resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/logistic-regression",
        json={"outcome_variable_id": outcome_var["id"], "predictor_variable_ids": [predictor_var["id"]]},
    )
    assert regression_resp.status_code == 200, regression_resp.text
    reg_result = regression_resp.json()["results"][0]
    assert reg_result["result_type"] == "LOGISTIC_REGRESSION"
    assert reg_result["n_valid"] == 10
    assert reg_result["result_data"]["accuracy"] == 1.0

    kmeans_resp = await client.post(
        f"/api/v1/studies/{study['id']}/analytics/kmeans",
        json={"variable_ids": [predictor_var["id"]], "k": 2},
    )
    assert kmeans_resp.status_code == 200, kmeans_resp.text
    kmeans_result = kmeans_resp.json()["results"][0]
    assert kmeans_result["result_type"] == "KMEANS"
    assert kmeans_result["n_valid"] == 10
    assert kmeans_result["result_data"]["cluster_sizes"] == [5, 5]
