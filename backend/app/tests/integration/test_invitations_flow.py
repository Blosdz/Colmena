"""E-17: token de invitación de un solo uso, opt-in por estudio
(`Study.requires_invitation`)."""

from httpx import AsyncClient


async def _build_study(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft, *, requires_invitation: bool
) -> dict:
    _instrument, version = seed_instrument_draft
    await client.post(
        f"/api/v1/instrument-versions/{version.id}/items",
        json={"code": "P1", "question_text": "P1", "question_type": "NUMBER"},
    )
    survey = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/surveys/from-instrument",
            json={
                "created_by_user_id": seed_user.id,
                "instrument_version_id": version.id,
                "name": "Encuesta invitaciones",
            },
        )
    ).json()
    study = (
        await client.post(
            f"/api/v1/projects/{seed_project.id}/studies",
            json={
                "survey_id": survey["id"],
                "name": "Estudio invitaciones",
                "study_type": "CUSTOM",
                "requires_invitation": requires_invitation,
            },
        )
    ).json()
    assert study["requires_invitation"] is requires_invitation
    await client.post(f"/api/v1/studies/{study['id']}/open")
    return study


async def test_public_session_requires_invitation_when_enabled(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    study = await _build_study(
        client, seed_user, seed_project, seed_instrument_draft, requires_invitation=True
    )

    no_token_resp = await client.post(
        f"/api/v1/public/studies/{study['public_id']}/response-sessions"
    )
    assert no_token_resp.status_code == 404, no_token_resp.text
    assert no_token_resp.json()["error_code"] == "PUBLIC_RESOURCE_UNAVAILABLE"

    issue_resp = await client.post(
        f"/api/v1/studies/{study['id']}/invitations", json={"count": 1}
    )
    assert issue_resp.status_code == 201, issue_resp.text
    tokens = issue_resp.json()["tokens"]
    assert len(tokens) == 1
    token = tokens[0]

    summary_resp = await client.get(f"/api/v1/studies/{study['id']}/invitations")
    assert summary_resp.json() == {"total": 1, "pending": 1, "consumed": 0, "expired": 0}

    ok_resp = await client.post(
        f"/api/v1/public/studies/{study['public_id']}/response-sessions",
        json={"invitation_token": token},
    )
    assert ok_resp.status_code == 201, ok_resp.text

    summary_after_resp = await client.get(f"/api/v1/studies/{study['id']}/invitations")
    assert summary_after_resp.json() == {"total": 1, "pending": 0, "consumed": 1, "expired": 0}

    reuse_resp = await client.post(
        f"/api/v1/public/studies/{study['public_id']}/response-sessions",
        json={"invitation_token": token},
    )
    assert reuse_resp.status_code == 404, reuse_resp.text
    assert reuse_resp.json()["error_code"] == "PUBLIC_RESOURCE_UNAVAILABLE"


async def test_public_session_ignores_invitation_when_not_required(
    client: AsyncClient, seed_user, seed_project, seed_instrument_draft
) -> None:
    study = await _build_study(
        client, seed_user, seed_project, seed_instrument_draft, requires_invitation=False
    )

    resp = await client.post(f"/api/v1/public/studies/{study['public_id']}/response-sessions")
    assert resp.status_code == 201, resp.text
