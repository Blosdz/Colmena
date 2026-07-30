import time

from fastapi.testclient import TestClient

from app.core.realtime import broker

from tests.test_public_forms import (
    create_basic_public_question,
    create_form,
    create_project,
    publish_form,
)


def _setup_published_form(client: TestClient) -> tuple[dict, dict, dict]:
    project = create_project(client)
    form = create_form(client, project["id"], "Formulario telemetria")
    question, option = create_basic_public_question(client, form["id"])
    publish_form(client, form["id"])
    link = client.get(f"/api/v1/forms/{form['id']}/public-link")
    assert link.status_code == 200
    return form, question, {"option": option, "slug": link.json()["public_slug"]}


def test_websocket_receives_event_on_public_submission(client: TestClient):
    form, question, extra = _setup_published_form(client)

    with client.websocket_connect(f"/api/ws/telemetry/{form['id']}") as websocket:
        hello = websocket.receive_json()
        assert hello["type"] == "connected"
        assert hello["form_id"] == form["id"]
        assert hello["mode"] in {"redis", "local"}

        # Da tiempo a que la tarea de forwarding registre la suscripción.
        time.sleep(0.3)

        submission = client.post(
            f"/api/public/forms/{extra['slug']}/responses",
            json={
                "respondent_code": "R-001",
                "answers": [
                    {"question_id": question["id"], "option_id": extra["option"]["id"]}
                ],
            },
        )
        assert submission.status_code == 201
        response_id = submission.json()["response_id"]

        event = websocket.receive_json()
        assert event["type"] == "response.submitted"
        assert event["form_id"] == form["id"]
        assert event["response_id"] == response_id
        assert event["status"] == "complete"
        assert event["source"] == "public_link"
        assert event["submitted_at"]


def test_websocket_does_not_receive_events_from_other_forms(client: TestClient):
    form_a, question_a, extra_a = _setup_published_form(client)
    form_b, _, _ = _setup_published_form(client)

    with client.websocket_connect(f"/api/ws/telemetry/{form_b['id']}") as websocket:
        assert websocket.receive_json()["type"] == "connected"
        time.sleep(0.3)

        submission = client.post(
            f"/api/public/forms/{extra_a['slug']}/responses",
            json={
                "respondent_code": "R-002",
                "answers": [
                    {"question_id": question_a["id"], "option_id": extra_a["option"]["id"]}
                ],
            },
        )
        assert submission.status_code == 201

        # Publica directo al canal de B para verificar que solo llega lo suyo.
        broker.publish(form_b["id"], {"type": "response.submitted", "form_id": form_b["id"]})
        event = websocket.receive_json()
        assert event["form_id"] == form_b["id"]
