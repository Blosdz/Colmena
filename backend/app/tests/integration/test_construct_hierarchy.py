"""Jerarquía dimensión/subdimensión (harness §9-10, §54)."""

from httpx import AsyncClient


async def _create_variable(client: AsyncClient, version_id: int) -> dict:
    response = await client.post(
        f"/api/v1/instrument-versions/{version_id}/structure-variables",
        json={"code": "VAR", "name": "Variable"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_subdimension_nests_under_dimension_in_tree(
    client: AsyncClient, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    variable = await _create_variable(client, version.id)

    dimension_resp = await client.post(
        f"/api/v1/instrument-versions/{version.id}/constructs",
        json={
            "parent_id": variable["id"],
            "code": "D1",
            "name": "Exigencias psicológicas",
            "construct_type": "DIMENSION",
        },
    )
    assert dimension_resp.status_code == 201
    dimension = dimension_resp.json()

    subdimension_resp = await client.post(
        f"/api/v1/instrument-versions/{version.id}/constructs",
        json={
            "code": "S1",
            "name": "Exigencias cuantitativas",
            "construct_type": "SUBDIMENSION",
            "parent_id": dimension["id"],
        },
    )
    assert subdimension_resp.status_code == 201
    subdimension = subdimension_resp.json()
    assert subdimension["parent_id"] == dimension["id"]

    tree_resp = await client.get(f"/api/v1/instrument-versions/{version.id}/tree")
    tree = tree_resp.json()
    assert len(tree["variables"]) == 1
    root = tree["variables"][0]["dimensions"][0]
    assert root["code"] == "D1"
    assert len(root["subdimensions"]) == 1
    assert root["subdimensions"][0]["code"] == "S1"


async def test_dimension_cannot_exist_outside_a_variable(
    client: AsyncClient, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    orphan_response = await client.post(
        f"/api/v1/instrument-versions/{version.id}/constructs",
        json={"code": "D1", "name": "Huérfana", "construct_type": "DIMENSION"},
    )
    assert orphan_response.status_code == 422

    variable = await _create_variable(client, version.id)
    dimension = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/constructs",
            json={
                "parent_id": variable["id"],
                "code": "D1",
                "name": "Dimensión",
                "construct_type": "DIMENSION",
            },
        )
    ).json()
    detach_response = await client.patch(
        f"/api/v1/constructs/{dimension['id']}", json={"parent_id": None}
    )
    assert detach_response.status_code == 422


async def test_construct_batch_update_is_transactional(
    client: AsyncClient, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    variable = await _create_variable(client, version.id)

    d1 = (
        await client.post(
            f"/api/v1/instrument-versions/{version.id}/constructs",
            json={
                "parent_id": variable["id"],
                "code": "D1",
                "name": "D1",
                "construct_type": "DIMENSION",
            },
        )
    ).json()
    # Un id inexistente en el batch debe hacer fallar todo el lote (rollback).
    batch_resp = await client.patch(
        f"/api/v1/instrument-versions/{version.id}/constructs/batch",
        json={
            "items": [
                {"id": d1["id"], "patch": {"name": "D1 renombrada"}},
                {"id": 999999, "patch": {"name": "no existe"}},
            ]
        },
    )
    assert batch_resp.status_code == 404

    get_resp = await client.get(f"/api/v1/constructs/{d1['id']}")
    assert get_resp.json()["name"] == "D1"  # no se aplicó el rename parcial
