import pytest
from pydantic import ValidationError

from app.schemas.responses import ResponseUpsert


def test_response_requires_exactly_one_typed_value() -> None:
    with pytest.raises(ValidationError):
        ResponseUpsert(raw_code="1", text_value="x")


def test_raw_code_and_numeric_value_together_is_valid_at_schema_level() -> None:
    """E-03: raw_code + numeric_value cuentan como un solo slot combinado;
    la consistencia real contra el catálogo se valida en el servicio."""
    payload = ResponseUpsert(raw_code="1", numeric_value=1)
    assert payload.raw_code == "1"
    assert payload.numeric_value == 1


def test_missing_response_rejects_typed_value() -> None:
    with pytest.raises(ValidationError):
        ResponseUpsert(is_missing=True, text_value="no debe persistirse")


def test_multiple_choice_rejects_empty_selection() -> None:
    with pytest.raises(ValidationError):
        ResponseUpsert(selected_option_ids=[])


def test_multiple_choice_accepts_selected_options() -> None:
    payload = ResponseUpsert(selected_option_ids=[1, 2])
    assert payload.selected_option_ids == [1, 2]
