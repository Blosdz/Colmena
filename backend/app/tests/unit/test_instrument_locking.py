import pytest

from app.core.exceptions import InstrumentLockedError
from app.models.instrument import Instrument, InstrumentVersion
from app.services.instrument_edit_policy import InstrumentEditPolicy


def _pair(*, is_system: bool, version_status: str) -> tuple[Instrument, InstrumentVersion]:
    instrument = Instrument(name="x", is_system=is_system)
    version = InstrumentVersion(version_code="V1", status=version_status)
    return instrument, version


@pytest.mark.parametrize("status", ["DRAFT", "TEST", "ACTIVE"])
def test_custom_instrument_editable_states(status: str) -> None:
    instrument, version = _pair(is_system=False, version_status=status)
    result = InstrumentEditPolicy.evaluate(instrument, version)
    assert result.editable is True


@pytest.mark.parametrize("status", ["USED", "CLOSED", "LOCKED"])
def test_custom_instrument_locked_states(status: str) -> None:
    instrument, version = _pair(is_system=False, version_status=status)
    result = InstrumentEditPolicy.evaluate(instrument, version)
    assert result.editable is False
    assert result.reason == "VERSION_LOCKED_CREATE_NEW_VERSION"


@pytest.mark.parametrize("status", ["DRAFT", "TEST"])
def test_system_instrument_editable_in_draft_or_test(status: str) -> None:
    instrument, version = _pair(is_system=True, version_status=status)
    result = InstrumentEditPolicy.evaluate(instrument, version)
    assert result.editable is True


@pytest.mark.parametrize("status", ["ACTIVE", "USED", "CLOSED"])
def test_system_instrument_locked_outside_draft_test(status: str) -> None:
    instrument, version = _pair(is_system=True, version_status=status)
    result = InstrumentEditPolicy.evaluate(instrument, version)
    assert result.editable is False
    assert result.reason in {"SYSTEM_INSTRUMENT_LOCKED", "VERSION_LOCKED_CREATE_NEW_VERSION"}


def test_require_editable_raises_for_locked_censopas() -> None:
    instrument, version = _pair(is_system=True, version_status="ACTIVE")
    with pytest.raises(InstrumentLockedError) as exc_info:
        InstrumentEditPolicy.require_editable(instrument, version)
    assert exc_info.value.extra["reason"] == "SYSTEM_INSTRUMENT_LOCKED"


@pytest.mark.parametrize("status", ["DRAFT", "TEST", "ACTIVE"])
def test_editable_states_locked_when_open_study_exists(status: str) -> None:
    """E-06: el bloqueo estructural aplica también con la versión en
    DRAFT/TEST, no sólo ACTIVE — antes un estudio OPEN sobre una versión
    DRAFT dejaba el instrumento editable sin ninguna restricción."""
    instrument, version = _pair(is_system=False, version_status=status)
    result = InstrumentEditPolicy.evaluate(instrument, version, open_study_exists=True)
    assert result.editable is False
    assert result.reason == "STUDY_OPEN_STRUCTURAL_LOCK"
