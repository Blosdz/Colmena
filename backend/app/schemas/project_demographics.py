from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectDemographicsBase(BaseModel):
    population_description: str | None = None
    sample_size_planned: int | None = Field(default=None, ge=0)
    sample_size_current: int | None = Field(default=None, ge=0)
    sampling_method: str | None = Field(default=None, max_length=100)
    inclusion_criteria: str | None = None
    exclusion_criteria: str | None = None

    @field_validator(
        "population_description",
        "sampling_method",
        "inclusion_criteria",
        "exclusion_criteria",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ProjectDemographicsInput(ProjectDemographicsBase):
    """Bloque de demografia enviado al crear/actualizar un proyecto."""


class ProjectDemographicsRead(ProjectDemographicsBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    sample_size_current: int
    created_at: datetime
    updated_at: datetime
