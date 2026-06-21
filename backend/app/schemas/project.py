from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectBase(BaseModel):
    subtitle: str | None = Field(default=None, max_length=255)
    research_type: str | None = Field(default=None, max_length=100)
    design_type: str | None = Field(default=None, max_length=150)
    approach: str | None = Field(default=None, max_length=100)
    institution: str | None = Field(default=None, max_length=255)
    faculty: str | None = Field(default=None, max_length=255)
    career: str | None = Field(default=None, max_length=255)
    advisor_name: str | None = Field(default=None, max_length=255)
    population_description: str | None = None
    sample_size_planned: int | None = Field(default=None, ge=0)
    notes: str | None = None

    @field_validator(
        "subtitle",
        "research_type",
        "design_type",
        "approach",
        "institution",
        "faculty",
        "career",
        "advisor_name",
        "population_description",
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
    sample_size_current: int | None = Field(default=None, ge=0)
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

    @field_validator(
        "subtitle",
        "research_type",
        "design_type",
        "approach",
        "institution",
        "faculty",
        "career",
        "advisor_name",
        "population_description",
        "status",
        "notes",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    subtitle: str | None
    research_type: str | None
    design_type: str | None
    approach: str | None
    institution: str | None
    faculty: str | None
    career: str | None
    advisor_name: str | None
    population_description: str | None
    sample_size_planned: int | None
    sample_size_current: int
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectRead]
    total: int
