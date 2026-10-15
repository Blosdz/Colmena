from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.form_answer import FormAnswer
from app.models.form_response import FormResponse


def request_json(url: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    with urlopen(request, timeout=30) as response:
        if response.status not in {200, 201}:
            raise RuntimeError(f"Unexpected HTTP status {response.status}")
        return json.loads(response.read().decode("utf-8"))


def build_answer(question: dict) -> dict:
    answer = {"question_id": question["id"]}
    question_type = question["question_type"]
    if question_type in {"single_choice", "dropdown", "likert", "boolean"}:
        answer["option_id"] = question["options"][0]["id"]
    elif question_type == "multiple_choice":
        answer["value_json"] = [question["options"][0]["id"]]
    elif question_type == "number":
        answer["value_number"] = question.get("min_value") or 1
    elif question_type in {"text_short", "text_long"}:
        answer["value_text"] = "Prueba automatizada de despliegue"
    elif question_type == "date":
        answer["value_date"] = datetime.now(timezone.utc).isoformat()
    else:
        raise RuntimeError(f"Unsupported smoke-test question type: {question_type}")
    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba y elimina un envío público real.")
    parser.add_argument("api_url")
    args = parser.parse_args()

    form = request_json(args.api_url)
    payload = {
        "snapshot_id": form["snapshot_id"],
        "answers": [build_answer(question) for question in form["questions"]],
        "metadata_json": {"source": "deployment-smoke-test"},
    }
    submitted = request_json(f"{args.api_url}/responses", method="POST", payload=payload)
    response_id = submitted["response_id"]

    try:
        with SessionLocal() as db:
            response = db.get(FormResponse, response_id)
            if response is None:
                raise RuntimeError("Submitted response was not persisted")
            answer_count = int(
                db.scalar(
                    select(func.count())
                    .select_from(FormAnswer)
                    .where(FormAnswer.response_id == response_id)
                )
                or 0
            )
            if answer_count != len(form["questions"]):
                raise RuntimeError(
                    f"Expected {len(form['questions'])} answers, found {answer_count}"
                )
            print(f"submit_status={submitted['status']}")
            print(f"answers_verified={answer_count}")
    finally:
        with SessionLocal() as db:
            db.execute(delete(FormAnswer).where(FormAnswer.response_id == response_id))
            response = db.get(FormResponse, response_id)
            if response is not None:
                db.delete(response)
            db.commit()
        print("test_response_removed=true")


if __name__ == "__main__":
    main()
