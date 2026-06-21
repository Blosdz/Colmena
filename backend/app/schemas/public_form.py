from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PublicFormLinkRead(BaseModel):
    form_id: str
    status: str
    public_slug: str | None
    public_url: str | None
    api_url: str | None


class PublicFormOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    value: str
    sort_order: int


class PublicFormQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    section_id: str | None
    instrument_id: str | None
    dimension_id: str | None
    project_variable_id: str | None
    code: str | None
    label: str
    help_text: str | None
    question_type: str
    question_role: str
    measurement_level: str
    data_type: str
    is_required: bool
    is_scored: bool
    is_reverse_scored: bool
    min_value: float | None
    max_value: float | None
    sort_order: int
    options: list[PublicFormOptionRead]


class PublicFormDimensionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str | None
    sort_order: int


class PublicFormInstrumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    acronym: str | None
    dimensions: list[PublicFormDimensionRead]


class PublicFormSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    sort_order: int


class PublicFormRead(BaseModel):
    id: str
    project_id: str
    title: str
    description: str | None
    instructions: str | None
    status: str
    sections: list[PublicFormSectionRead]
    instruments: list[PublicFormInstrumentRead]
    questions: list[PublicFormQuestionRead]
    thank_you_message: str | None
    metadata_json: str | None = None


class PublicAnswerCreate(BaseModel):
    question_id: str
    option_id: str | None = None
    value_text: str | None = None
    value_number: float | None = None
    value_date: datetime | None = None
    value_json: list[str] | list[dict] | dict | None = None

    @field_validator("value_text")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class PublicFormResponseCreate(BaseModel):
    respondent_code: str | None = Field(default=None, max_length=100)
    answers: list[PublicAnswerCreate] = Field(default_factory=list)
    metadata_json: dict | list | None = None

    @field_validator("respondent_code")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class PublicFormResponseRead(BaseModel):
    status: str
    response_id: str
    form_id: str
    submitted_at: datetime
