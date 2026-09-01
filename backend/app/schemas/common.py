from pydantic import AliasChoices, Field


def metadata_field(default: dict | None = None):
    """Campo `metadata` que lee del atributo ORM `metadata_` (ver projects.py)."""
    return Field(
        default_factory=dict if default is None else (lambda: default),
        validation_alias=AliasChoices("metadata_", "metadata"),
    )
