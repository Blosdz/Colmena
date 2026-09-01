from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationDomainError
from app.schemas.questions import OptionSetCreate, OptionSetOptionInput, OptionSetRead
from app.services.question_service import QuestionService


def make_options(count: int) -> list[OptionSetOptionInput]:
    return [
        OptionSetOptionInput(
            raw_code=str(index),
            label=f"Opción {index}",
            numeric_value=index,
            sort_order=index - 1,
        )
        for index in range(1, count + 1)
    ]


def test_user_likert_metadata_is_part_of_the_api_contract() -> None:
    payload = OptionSetCreate(
        name="Acuerdo de cinco puntos",
        metadata={"kind": "LIKERT_USER", "points": 5, "editable": True},
        options=make_options(5),
    )

    assert payload.metadata["kind"] == "LIKERT_USER"
    assert payload.metadata["points"] == 5

    orm_scale = SimpleNamespace(
        id=1,
        public_id=uuid4(),
        owner_user_id=8,
        code=None,
        name=payload.name,
        description=None,
        metadata_=payload.metadata,
        options=[
            SimpleNamespace(id=index, **option.model_dump())
            for index, option in enumerate(payload.options, start=1)
        ],
    )
    response = OptionSetRead.model_validate(orm_scale)

    assert response.owner_user_id == 8
    assert response.metadata == payload.metadata


def test_likert_scale_is_limited_to_ten_points() -> None:
    with pytest.raises(ValidationDomainError, match="máximo diez"):
        QuestionService._validate_option_inputs(make_options(11))

