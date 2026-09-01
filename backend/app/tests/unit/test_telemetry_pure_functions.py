from types import SimpleNamespace

import pytest

from app.services.telemetry_service import TelemetryService


def test_questions_are_grouped_under_their_root_variable() -> None:
    constructs = [
        SimpleNamespace(id=1, parent_id=None),
        SimpleNamespace(id=2, parent_id=1),
        SimpleNamespace(id=3, parent_id=2),
    ]
    links = [
        SimpleNamespace(construct_id=1, question_id=10, item_role="SCORED"),
        SimpleNamespace(construct_id=3, question_id=11, item_role="SCORED"),
        SimpleNamespace(construct_id=2, question_id=12, item_role="EXCLUDED"),
    ]

    grouped = TelemetryService._question_ids_by_root(constructs, links)

    assert grouped == {1: {10, 11}}


def test_variable_coverage_uses_all_sessions_as_denominator() -> None:
    answered, completed, rate, average = TelemetryService._variable_coverage(
        session_ids=[1, 2, 3],
        answered_by_session={1: {10, 11}, 2: {10}, 3: set()},
        question_ids={10, 11},
    )

    assert answered == 2
    assert completed == 1
    assert rate == pytest.approx(1 / 3)
    assert average == pytest.approx(50)
