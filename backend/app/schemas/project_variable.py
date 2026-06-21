from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectVariableBase(BaseModel):
    code: str | None = Field(default=None, max_length=100)
    description: str | None = None
    variable_role: str = Field(default="main", max_length=50)
    measurement_level: str = Field(default="ordinal", max_length=50)
    data_type: str = Field(default="numeric", max_length=50)
    is_required_for_analysis: bool = False
    notes: str | None = None

    @field_validator("code", "description", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("variable_role", "measurement_level", "data_type")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must not be empty")
        return cleaned


class ProjectVariableCreate(ProjectVariableBase):
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class ProjectVariableUpdate(ProjectVariableBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class ProjectVariableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    code: str | None
    description: str | None
    variable_role: str
    measurement_level: str
    data_type: str
    is_required_for_analysis: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ProjectVariableListResponse(BaseModel):
    items: list[ProjectVariableRead]
    total: int
