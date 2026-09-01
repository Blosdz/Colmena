from __future__ import annotations

from pydantic import BaseModel


class DataDictionaryEntry(BaseModel):
    """Una fila del diccionario de variables (harness §45)."""

    variable_code: str
    label: str | None
    data_type: str
    measurement_level: str
    role: str
    categories: list[dict] | None = None
    source: str
    question_code: str | None = None
    question_text: str | None = None
    constructs: list[str] = []
    missing_rule: dict | None = None


class DataDictionary(BaseModel):
    study_id: int
    entries: list[DataDictionaryEntry]


class LongDatasetRow(BaseModel):
    case_id: int
    question_code: str | None
    variable_code: str | None
    raw_code: str | None
    numeric_value: float | None
    text_value: str | None
    is_missing: bool


class LongDataset(BaseModel):
    study_id: int
    rows: list[LongDatasetRow]


class WideDataset(BaseModel):
    study_id: int
    columns: list[str]
    rows: list[dict]
