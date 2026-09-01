"""Asignación ítem <-> constructo: weight, scoring_direction, sort_order (harness §10)."""

from httpx import AsyncClient


async def _create_variable(client: AsyncClient, version_id: int) -> dict:
    return (
        await client.post(
            f"/api/v1/instrument-versions/{version_id}/structure-variables",
            json={"code": "VAR", "name": "Variable"},
        )
    ).json()


async def test_assign_update_and_remove_item(
    client: AsyncClient, seed_instrument_draft
) -> None:
    _instrument, version = seed_instrument_draft
    variable = await _create_variable(client, version.id)

    item_resp = await client.post(
        f"/api/v1/instrument-versions/{version.id}/items",
        json={"code": "P1", "question_text": "Pregunta 1", "question_type": "LIKERT"},
    )
    item = item_resp.json()

    construct_resp = await client.post(
        f"/api/v1/instrument-versions/{version.id}/constructs",
        json={"parent_id": variable["id"], "code": "D1", "name": "D1", "construct_type": "DIMENSION"},
    )
    construct = construct_resp.json()

    assign_resp = await client.post(
        f"/api/v1/constructs/{construct['id']}/items",
        json={"question_id": item["id"], "weight": 1, "scoring_direction": "DIRECT"},
    )
    assert assign_resp.status_code == 201
    assert assign_resp.json()["weight"] == 1

    update_resp = await client.patch(
        f"/api/v1/constructs/{construct['id']}/items/{item['id']}",
        json={"weight": 2.5, "scoring_direction": "REVERSE", "sort_order": 3},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["weight"] == 2.5
    assert updated["scoring_direction"] == "REVERSE"
    assert updated["sort_order"] == 3

    remove_resp = await client.delete(
        f"/api/v1/constructs/{construct['id']}/items/{item['id']}"
    )
    assert remove_resp.status_code == 204

    tree_resp = await client.get(f"/api/v1/instrument-versions/{version.id}/tree")
    tree = tree_resp.json()
    assert tree["variables"][0]["dimensions"][0]["items"] == []


async def test_cannot_assign_item_from_another_version(
    client: AsyncClient, session, seed_instrument_draft
) -> None:
    from app.models.instrument import Instrument, InstrumentVersion
    from app.models.question import Question

    instrument, version = seed_instrument_draft
    variable = await _create_variable(client, version.id)

    other_instrument = Instrument(name="Otro instrumento", is_system=False, status="DRAFT")
    session.add(other_instrument)
    await session.flush()
    other_version = InstrumentVersion(
        instrument_id=other_instrument.id, version_code="V1", status="DRAFT"
    )
    session.add(other_version)
    await session.flush()
    other_question = Question(
        instrument_version_id=other_version.id,
        question_text="Pregunta de otro instrumento",
        question_type="TEXT",
    )
    session.add(other_question)
    await session.commit()
    await session.refresh(other_question)

    construct_resp = await client.post(
        f"/api/v1/instrument-versions/{version.id}/constructs",
        json={"parent_id": variable["id"], "code": "D1", "name": "D1", "construct_type": "DIMENSION"},
    )
    construct = construct_resp.json()

    assign_resp = await client.post(
        f"/api/v1/constructs/{construct['id']}/items",
        json={"question_id": other_question.id, "weight": 1},
    )
    assert assign_resp.status_code == 404
