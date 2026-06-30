from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.project_demographics import (
    ProjectDemographicsInput,
    ProjectDemographicsRead,
)


class ProjectBase(BaseModel):
    subtitle: str | None = Field(default=None, max_length=255)
    type_research_id: str | None = Field(default=None, max_length=36)
    design_type_id: str | None = Field(default=None, max_length=36)
    approach_id: str | None = Field(default=None, max_length=36)
    institution: str | None = Field(default=None, max_length=255)
    faculty: str | None = Field(default=None, max_length=255)
    career: str | None = Field(default=None, max_length=255)
    advisor_name: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    demographics: ProjectDemographicsInput | None = None

    @field_validator(
        "subtitle",
        "type_research_id",
        "design_type_id",
        "approach_id",
        "institution",
        "faculty",
        "career",
        "advisor_name",
        "notes",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ProjectCreate(ProjectBase):
    title: str = Field(..., min_length=1, max_length=255)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned


class ProjectUpdate(ProjectBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, max_length=50)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned

    @field_validator("status")
    @classmethod
    def normalize_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CatalogRef(BaseModel):
    """Referencia ligera a un item de catalogo para mostrar nombre."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    subtitle: str | None
    type_research_id: str | None
    design_type_id: str | None
    approach_id: str | None
    type_research: CatalogRef | None = None
    design_type: CatalogRef | None = None
    approach: CatalogRef | None = None
    institution: str | None
    faculty: str | None
    career: str | None
    advisor_name: str | None
    status: str
    notes: str | None
    demographics: ProjectDemographicsRead | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectRead]
    total: int
