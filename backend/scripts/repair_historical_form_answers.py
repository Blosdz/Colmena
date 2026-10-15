from __future__ import annotations

import argparse
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.form_answer import FormAnswer
from app.models.form_question import FormQuestion


def backup_database(source: Path) -> Path:
    backup_dir = source.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"{source.stem}-before-answer-repair-{timestamp}{source.suffix}"
    with sqlite3.connect(source) as source_connection:
        with sqlite3.connect(destination) as destination_connection:
            source_connection.backup(destination_connection)
    return destination


def repair(*, apply_changes: bool) -> tuple[Counter, Path | None]:
    settings = get_settings()
    backup_path = backup_database(settings.database_file) if apply_changes else None
    stats: Counter = Counter()

    with SessionLocal() as db:
        questions = list(
            db.scalars(
                select(FormQuestion).options(selectinload(FormQuestion.options))
            ).all()
        )
        active_by_form_code: dict[tuple[str, str], list[FormQuestion]] = defaultdict(list)
        questions_by_id = {question.id: question for question in questions}
        for question in questions:
            if question.deleted_at is None and question.code:
                active_by_form_code[(question.form_id, question.code)].append(question)

        answers = list(db.scalars(select(FormAnswer)).all())
        occupied = {(answer.response_id, answer.question_id) for answer in answers}

        for answer in answers:
            source_question = questions_by_id.get(answer.question_id)
            if source_question is None or source_question.deleted_at is None:
                continue
            stats["historical_answers"] += 1

            if not source_question.code:
                stats["skipped_without_code"] += 1
                continue
            candidates = active_by_form_code.get(
                (source_question.form_id, source_question.code), []
            )
            candidates = [
                candidate
                for candidate in candidates
                if candidate.question_type == source_question.question_type
            ]
            if len(candidates) != 1:
                stats["skipped_ambiguous_question"] += 1
                continue
            target_question = candidates[0]
            if (answer.response_id, target_question.id) in occupied:
                stats["skipped_duplicate_answer"] += 1
                continue

            source_options = {option.id: option for option in source_question.options}
            target_options_by_value: dict[str, list] = defaultdict(list)
            target_option_ids = set()
            for option in target_question.options:
                if option.deleted_at is None:
                    target_option_ids.add(option.id)
                    target_options_by_value[option.value].append(option)

            target_option_id = answer.option_id
            if answer.option_id is not None and answer.option_id not in target_option_ids:
                source_option = source_options.get(answer.option_id)
                option_candidates = (
                    target_options_by_value.get(source_option.value, [])
                    if source_option is not None
                    else []
                )
                if len(option_candidates) != 1:
                    stats["skipped_ambiguous_option"] += 1
                    continue
                target_option_id = option_candidates[0].id

            target_value_json = answer.value_json
            if isinstance(answer.value_json, list):
                target_value_json = []
                invalid_reference = False
                for raw_value in answer.value_json:
                    if not isinstance(raw_value, str) or raw_value in target_option_ids:
                        target_value_json.append(raw_value)
                        continue
                    source_option = source_options.get(raw_value)
                    option_candidates = (
                        target_options_by_value.get(source_option.value, [])
                        if source_option is not None
                        else []
                    )
                    if len(option_candidates) != 1:
                        invalid_reference = True
                        break
                    target_value_json.append(option_candidates[0].id)
                if invalid_reference:
                    stats["skipped_ambiguous_multiple_choice"] += 1
                    continue

            stats["repairable_answers"] += 1
            if apply_changes:
                occupied.discard((answer.response_id, answer.question_id))
                answer.question_id = target_question.id
                answer.option_id = target_option_id
                answer.value_json = target_value_json
                occupied.add((answer.response_id, target_question.id))

        if apply_changes:
            db.commit()

    return stats, backup_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reasocia respuestas de preguntas reemplazadas usando código y valor estables."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Crea un respaldo y aplica la reparación. Sin esta opción sólo informa.",
    )
    args = parser.parse_args()

    stats, backup_path = repair(apply_changes=args.apply)
    print("mode=apply" if args.apply else "mode=dry-run")
    for key in sorted(stats):
        print(f"{key}={stats[key]}")
    if backup_path is not None:
        print(f"backup={backup_path}")


if __name__ == "__main__":
    main()
