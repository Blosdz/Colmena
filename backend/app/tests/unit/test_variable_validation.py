import pytest

from app.core.exceptions import VariableConversionError
from app.models.variable import Variable
from app.services.variable_service import VariableService


def _variable(data_type: str) -> Variable:
    return Variable(
        project_id=1,
        code="edad",
        name="Edad",
        variable_type="QUESTION",
        data_type=data_type,
        measurement_level="SCALE",
    )


@pytest.mark.parametrize(
    ("from_type", "to_type"),
    [("INTEGER", "DECIMAL"), ("INTEGER", "TEXT"), ("DATE", "DATETIME")],
)
def test_safe_conversion_allowed(from_type: str, to_type: str) -> None:
    service = VariableService.__new__(VariableService)  # no requiere sesión real
    variable = _variable(from_type)
    service._validate_data_type_change(variable, to_type)  # no debe lanzar


def test_same_type_is_noop() -> None:
    service = VariableService.__new__(VariableService)
    variable = _variable("TEXT")
    service._validate_data_type_change(variable, "TEXT")


def test_destructive_conversion_rejected() -> None:
    service = VariableService.__new__(VariableService)
    variable = _variable("TEXT")
    with pytest.raises(VariableConversionError):
        service._validate_data_type_change(variable, "INTEGER")
