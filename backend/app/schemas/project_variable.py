from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def derive_measurement_level(measurement_mode: str, data_type: str) -> str:
    """Deriva el nivel de medición a partir de cómo se mide la variable.

    El usuario nunca elige el nivel: el sistema lo deduce. Un instrumento tipo
    cuestionario (ítems Likert que se suman) es ordinal; un dato directo numérico
    es de razón; una categoría/booleano es nominal.
    """
    if measurement_mode == "instrument":
        return "ordinal"
    if data_type == "numeric":
        return "ratio"
    if data_type == "date":
        return "interval"
    # categorical, boolean, text → nominal
    return "nominal"


VALID_VARIABLE_ROLES = {"main", "intervening"}
VALID_VARIABLE_CLASSIFICATIONS = {"independent", "dependent", "segment"}

# Roles legacy que aún pueden llegar de clientes viejos; se normalizan al vocabulario nuevo.
LEGACY_ROLE_MAP = {
    "demographic": "intervening",
    "independent": "main",
    "dependent": "main",
    "control": "main",
    "covariate": "main",
    "moderator": "main",
    "mediator": "main",
    # Vocabulario en español del wizard legacy (FormWizard).
    "interviniente": "intervening",
    "sociodemografica": "intervening",
    "agrupacion": "intervening",
    "independiente": "main",
    "dependiente": "main",
    "resultado": "main",
}


class ProjectVariableBase(BaseModel):
    code: str | None = Field(default=None, max_length=100)
    description: str | None = None
    variable_role: str = Field(default="main", max_length=50)
    variable_classification: str | None = Field(default=None, max_length=50)
    measurement_mode: str = Field(default="instrument", max_length=50)
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

    @field_validator("variable_role", "measurement_mode", "measurement_level", "data_type")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must not be empty")
        return cleaned

    @field_validator("measurement_mode")
    @classmethod
    def validate_measurement_mode(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in {"instrument", "direct"}:
            raise ValueError("measurement_mode must be 'instrument' or 'direct'")
        return cleaned

    @field_validator("variable_role")
    @classmethod
    def validate_variable_role(cls, value: str) -> str:
        cleaned = LEGACY_ROLE_MAP.get(value.strip(), value.strip())
        if cleaned not in VALID_VARIABLE_ROLES:
            raise ValueError("variable_role must be 'main' or 'intervening'")
        return cleaned

    @field_validator("variable_classification")
    @classmethod
    def validate_variable_classification(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned not in VALID_VARIABLE_CLASSIFICATIONS:
            raise ValueError(
                "variable_classification must be 'independent', 'dependent' or 'segment'"
            )
        return cleaned

    @model_validator(mode="after")
    def inherit_measurement_level(self) -> "ProjectVariableBase":
        """El backend no confía en el nivel que envíe el cliente: lo hereda.

        Solo se recalcula cuando el cliente tocó `measurement_mode` o `data_type`,
        para que los updates parciales (PATCH con exclude_unset) sigan funcionando.
        """
        if "measurement_mode" in self.model_fields_set or "data_type" in self.model_fields_set:
            self.measurement_level = derive_measurement_level(self.measurement_mode, self.data_type)
            self.__pydantic_fields_set__.add("measurement_level")
        return self


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
    variable_classification: str | None
    measurement_mode: str
    measurement_level: str
    data_type: str
    is_required_for_analysis: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ProjectVariableListResponse(BaseModel):
    items: list[ProjectVariableRead]
    total: int
