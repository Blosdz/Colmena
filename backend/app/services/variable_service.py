from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError, ValidationDomainError
from app.core.pagination import Page, PageParams, paginate
from app.models.variable import Variable
from app.models.option_set import OptionSet, OptionSetOption
from app.models.question import Question
from app.repositories.instruments import InstrumentRepository
from app.repositories.projects import ProjectRepository
from app.repositories.variables import VariableRepository
from app.schemas.variables import (
    VariableBatchUpdate,
    VariableCreate,
    ExogenousFieldCreate,
    VariableRead,
    VariableUpdate,
)
from app.services.audit_service import AuditService
from app.services.instrument_edit_policy import InstrumentEditPolicy

# Conversiones de data_type consideradas siempre seguras (no pierden
# información representable). Cualquier otra combinación se considera
# potencialmente destructiva (harness §8: "TEXT -> INTEGER debe validar
# primero todos los valores existentes").
_SAFE_CONVERSIONS: dict[str, set[str]] = {
    "INTEGER": {"DECIMAL", "TEXT"},
    "DECIMAL": {"TEXT"},
    "BOOLEAN": {"TEXT"},
    "DATE": {"DATETIME", "TEXT"},
    "DATETIME": {"TEXT"},
    "CATEGORY": {"TEXT"},
}


class VariableService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = VariableRepository(session)
        self.audit = AuditService(session)
        self.instrument_repo = InstrumentRepository(session)
        self.project_repo = ProjectRepository(session)

    @staticmethod
    def _question_type_for_data_type(data_type: str) -> str:
        return {
            "INTEGER": "NUMBER",
            "DECIMAL": "NUMBER",
            "TEXT": "TEXT",
            "BOOLEAN": "BOOLEAN",
            "DATE": "DATE",
            "DATETIME": "DATETIME",
            "CATEGORY": "SINGLE_CHOICE",
        }[data_type]

    async def create_exogenous_field(
        self, project_id: int, payload: ExogenousFieldCreate
    ) -> tuple[Variable, Question]:
        project = await self.project_repo.get(project_id)
        if project is None:
            raise NotFoundError(f"Proyecto {project_id} no encontrado")
        version = await self.instrument_repo.get_version_with_instrument(
            payload.instrument_version_id
        )
        if version is None:
            raise NotFoundError(
                f"Versión de instrumento {payload.instrument_version_id} no encontrada"
            )
        await InstrumentEditPolicy.can_edit_question(self.session, version.instrument, version)

        if payload.data_type == "CATEGORY":
            if payload.measurement_level not in ("NOMINAL", "ORDINAL"):
                raise ValidationDomainError(
                    "Una categoría exógena debe tener nivel de medición nominal u ordinal."
                )
            if len(payload.options) < 2:
                raise ValidationDomainError(
                    "Una categoría exógena requiere al menos dos opciones."
                )
            raw_codes = [option.raw_code for option in payload.options]
            if len(raw_codes) != len(set(raw_codes)):
                raise ValidationDomainError("Los códigos de opciones deben ser únicos.")
            if payload.measurement_level == "ORDINAL" and any(
                option.numeric_value is None for option in payload.options if option.is_active
            ):
                raise ValidationDomainError(
                    "Las opciones ordinales deben tener un valor numérico."
                )
        elif payload.options:
            raise ValidationDomainError(
                "Las opciones sólo se permiten en campos exógenos de tipo CATEGORY."
            )

        option_set = None
        if payload.options:
            option_set = OptionSet(
                instrument_version_id=payload.instrument_version_id,
                code=f"EXO_{payload.code}",
                name=f"Opciones de {payload.name}",
                options=[OptionSetOption(**option.model_dump()) for option in payload.options],
            )
            self.session.add(option_set)
            await self.session.flush()

        question = Question(
            instrument_version_id=payload.instrument_version_id,
            option_set_id=option_set.id if option_set else None,
            code=payload.code,
            question_text=payload.question_text,
            short_label=payload.name,
            question_type=self._question_type_for_data_type(payload.data_type),
            research_role="EXOGENOUS",
            category="Datos de perfil",
            is_scored=False,
            is_required_default=payload.is_required,
            sort_order=payload.sort_order,
            metadata_={**payload.metadata, "exogenous": True},
        )
        self.session.add(question)
        await self.session.flush()

        variable = Variable(
            project_id=project_id,
            instrument_version_id=payload.instrument_version_id,
            question_id=question.id,
            code=payload.code,
            name=payload.name,
            label=payload.question_text,
            variable_type="EXOGENOUS",
            data_type=payload.data_type,
            measurement_level=payload.measurement_level,
            role="EXOGENOUS",
            is_editable=True,
            metadata_={**payload.metadata, "research_role": "EXOGENOUS"},
        )
        self.session.add(variable)
        await self.session.flush()
        await self.audit.log(
            action="EXOGENOUS_FIELD_CREATED",
            entity_type="variable",
            entity_id=variable.id,
            project_id=project_id,
            after_data=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        await self.session.refresh(variable)
        await self.session.refresh(question)
        return variable, question

    async def list_exogenous_fields(self, project_id: int) -> list[tuple[Variable, Question]]:
        stmt = (
            select(Variable)
            .where(Variable.project_id == project_id, Variable.variable_type == "EXOGENOUS")
            .options(selectinload(Variable.question))
            .order_by(Variable.created_at, Variable.id)
        )
        variables = list((await self.session.execute(stmt)).scalars().all())
        return [(variable, variable.question) for variable in variables if variable.question]

    async def create(self, project_id: int, payload: VariableCreate) -> Variable:
        existing = await self.repo.get_by_project_and_code(project_id, payload.code)
        if existing is not None:
            raise ConflictError(
                f"Ya existe una variable con código '{payload.code}' en este proyecto."
            )
        variable = Variable(
            project_id=project_id,
            study_id=payload.study_id,
            instrument_version_id=payload.instrument_version_id,
            question_id=payload.question_id,
            construct_id=payload.construct_id,
            code=payload.code,
            name=payload.name,
            label=payload.label,
            variable_type=payload.variable_type,
            data_type=payload.data_type,
            measurement_level=payload.measurement_level,
            role=payload.role,
            is_editable=payload.is_editable,
            formula=payload.formula,
            metadata_=payload.metadata,
        )
        variable = await self.repo.create(variable)
        await self.audit.log(
            action="VARIABLE_CREATED",
            entity_type="variable",
            entity_id=variable.id,
            project_id=project_id,
            after_data=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return variable

    async def get(self, variable_id: int) -> Variable:
        variable = await self.repo.get(variable_id)
        if variable is None:
            raise NotFoundError(f"Variable {variable_id} no encontrada")
        return variable

    async def list_by_project(self, project_id: int, params: PageParams) -> Page[VariableRead]:
        items, total = await paginate(
            self.session, self.repo.list_by_project_stmt(project_id), params
        )
        return Page[VariableRead](
            items=[VariableRead.model_validate(item) for item in items],
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    def _validate_data_type_change(self, variable: Variable, new_data_type: str) -> None:
        """Bloquea cambios destructivos (harness §8).

        Nota: la verificación real requiere inspeccionar `responses`
        existentes (Fase 3). Mientras ese módulo no exista, se permite
        cualquier conversión declarada "segura"; las demás se rechazan de
        forma conservadora en lugar de aplicarlas ciegamente.
        """
        if new_data_type == variable.data_type:
            return
        if new_data_type in _SAFE_CONVERSIONS.get(variable.data_type, set()):
            return
        from app.core.exceptions import VariableConversionError

        raise VariableConversionError(
            f"Cambio de data_type {variable.data_type} -> {new_data_type} no permitido "
            "sin validar los valores existentes.",
            from_data_type=variable.data_type,
            to_data_type=new_data_type,
        )

    async def update(self, variable_id: int, payload: VariableUpdate) -> Variable:
        variable = await self.get(variable_id)
        data = payload.model_dump(exclude_unset=True)

        if "data_type" in data and data["data_type"] is not None:
            self._validate_data_type_change(variable, data["data_type"])

        if "metadata" in data:
            variable.metadata_ = data.pop("metadata")

        before = VariableRead.model_validate(variable).model_dump(mode="json")
        for field, value in data.items():
            setattr(variable, field, value)

        await self.session.flush()
        await self.audit.log(
            action="VARIABLE_UPDATED",
            entity_type="variable",
            entity_id=variable.id,
            project_id=variable.project_id,
            before_data=before,
            after_data=data,
        )
        await self.session.commit()
        await self.session.refresh(variable)
        return variable

    async def delete(self, variable_id: int) -> None:
        variable = await self.get(variable_id)
        await self.audit.log(
            action="VARIABLE_DELETED",
            entity_type="variable",
            entity_id=variable.id,
            project_id=variable.project_id,
        )
        await self.repo.delete(variable)
        await self.session.commit()

    async def batch_update(self, project_id: int, payload: VariableBatchUpdate) -> list[Variable]:
        """Edición batch transaccional (harness §43): si un elemento falla, rollback completo."""
        updated: list[Variable] = []
        try:
            for item in payload.items:
                variable = await self.repo.get(item.id)
                if variable is None or variable.project_id != project_id:
                    raise NotFoundError(f"Variable {item.id} no encontrada en el proyecto")

                data = item.patch.model_dump(exclude_unset=True)
                if "data_type" in data and data["data_type"] is not None:
                    self._validate_data_type_change(variable, data["data_type"])
                if "metadata" in data:
                    variable.metadata_ = data.pop("metadata")
                for field, value in data.items():
                    setattr(variable, field, value)
                updated.append(variable)

            await self.session.flush()
            await self.audit.log(
                action="VARIABLE_BATCH_UPDATED",
                entity_type="variable",
                entity_id=None,
                project_id=project_id,
                after_data={"ids": [v.id for v in updated]},
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        for variable in updated:
            await self.session.refresh(variable)
        return updated
