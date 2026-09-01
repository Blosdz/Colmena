from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationDomainError
from app.models.option_set import OptionSet, OptionSetOption
from app.models.question import Question
from app.repositories.instruments import InstrumentRepository
from app.repositories.questions import QuestionRepository
from app.schemas.questions import (
    OptionSetCreate,
    OptionSetUpdate,
    QuestionBatchUpdate,
    QuestionCreate,
    QuestionRead,
    QuestionUpdate,
)
from app.services.audit_service import AuditService
from app.services.instrument_edit_policy import InstrumentEditPolicy


class QuestionService:
    """Editor de ítems (harness §11) — CRUD, opciones y edición batch (§43)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = QuestionRepository(session)
        self.instrument_repo = InstrumentRepository(session)
        self.audit = AuditService(session)

    async def _load_version_for_policy(self, instrument_version_id: int):
        version = await self.instrument_repo.get_version_with_instrument(instrument_version_id)
        if version is None:
            raise NotFoundError(f"Versión de instrumento {instrument_version_id} no encontrada")
        return version

    async def list_by_version(self, instrument_version_id: int) -> list[Question]:
        await self._load_version_for_policy(instrument_version_id)
        return await self.repo.list_by_version(instrument_version_id)

    async def get(self, question_id: int) -> Question:
        question = await self.repo.get(question_id)
        if question is None:
            raise NotFoundError(f"Ítem {question_id} no encontrado")
        return question

    @staticmethod
    def _validate_option_inputs(options) -> None:
        if len(options) < 2:
            raise ValidationDomainError("Una escala Likert requiere al menos dos opciones.")
        if len(options) > 10:
            raise ValidationDomainError("Una escala Likert admite como máximo diez opciones.")
        raw_codes = [option.raw_code for option in options]
        if len(raw_codes) != len(set(raw_codes)):
            raise ValidationDomainError("Los códigos de las opciones de una escala deben ser únicos.")
        active_values = [option.numeric_value for option in options if option.is_active]
        if len(active_values) < 2 or any(value is None for value in active_values):
            raise ValidationDomainError(
                "Todas las opciones activas de una escala Likert deben tener valor numérico."
            )
        if len(active_values) != len(set(active_values)):
            raise ValidationDomainError("Los valores numéricos activos de la escala deben ser únicos.")

    async def _validate_scored_question(
        self, question_type: str, is_scored: bool, option_set_id: int | None
    ) -> None:
        if not is_scored:
            return
        if question_type != "LIKERT":
            raise ValidationDomainError(
                "Los ítems puntuables (is_scored=true) deben resolverse con una escala Likert."
            )
        if option_set_id is None:
            raise ValidationDomainError("Un ítem Likert puntuable requiere una escala de respuestas.")
        option_set = await self.repo.get_option_set(option_set_id)
        if option_set is None:
            raise NotFoundError(f"Escala Likert {option_set_id} no encontrada")
        self._validate_option_inputs(option_set.options)

    async def list_likert_scales(self, instrument_version_id: int) -> list[OptionSet]:
        await self._load_version_for_policy(instrument_version_id)
        return await self.repo.list_option_sets(instrument_version_id)

    async def create_likert_scale(
        self, instrument_version_id: int, payload: OptionSetCreate
    ) -> OptionSet:
        version = await self._load_version_for_policy(instrument_version_id)
        await InstrumentEditPolicy.can_edit_question(self.session, version.instrument, version)
        self._validate_option_inputs(payload.options)
        option_set = OptionSet(
            instrument_version_id=instrument_version_id,
            owner_user_id=version.instrument.owner_user_id,
            code=payload.code,
            name=payload.name,
            description=payload.description,
            metadata_=payload.metadata,
            options=[OptionSetOption(**option.model_dump()) for option in payload.options],
        )
        option_set = await self.repo.create_option_set(option_set)
        await self.audit.log(
            action="LIKERT_SCALE_CREATED",
            entity_type="option_set",
            entity_id=option_set.id,
            after_data=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return await self.repo.get_option_set(option_set.id)

    async def update_likert_scale(
        self, option_set_id: int, payload: OptionSetUpdate
    ) -> OptionSet:
        option_set = await self.repo.get_option_set(option_set_id)
        if option_set is None:
            raise NotFoundError(f"Escala Likert {option_set_id} no encontrada")
        version = await self._load_version_for_policy(option_set.instrument_version_id)
        await InstrumentEditPolicy.can_edit_question(self.session, version.instrument, version)

        data = payload.model_dump(exclude_unset=True)
        data.pop("options", None)
        if "metadata" in data:
            option_set.metadata_ = data.pop("metadata")
        if payload.options is not None:
            self._validate_option_inputs(payload.options)
            for existing_option in list(option_set.options):
                await self.session.delete(existing_option)
            await self.session.flush()
            option_set.options = [
                OptionSetOption(**option.model_dump()) for option in payload.options
            ]
        for field, value in data.items():
            setattr(option_set, field, value)
        await self.audit.log(
            action="LIKERT_SCALE_UPDATED",
            entity_type="option_set",
            entity_id=option_set.id,
            after_data=payload.model_dump(mode="json", exclude_unset=True),
        )
        await self.session.commit()
        return await self.repo.get_option_set(option_set.id)

    async def create(self, instrument_version_id: int, payload: QuestionCreate) -> Question:
        version = await self._load_version_for_policy(instrument_version_id)
        await InstrumentEditPolicy.can_edit_question(self.session, version.instrument, version)

        option_set_id = payload.option_set_id
        if payload.option_set is not None:
            if payload.question_type == "LIKERT":
                self._validate_option_inputs(payload.option_set.options)
            option_set = OptionSet(
                instrument_version_id=instrument_version_id,
                owner_user_id=version.instrument.owner_user_id,
                code=payload.option_set.code,
                name=payload.option_set.name,
                description=payload.option_set.description,
                metadata_=payload.option_set.metadata,
                options=[
                    OptionSetOption(**option.model_dump()) for option in payload.option_set.options
                ],
            )
            option_set = await self.repo.create_option_set(option_set)
            option_set_id = option_set.id

        # Compatibilidad con clientes anteriores: un LIKERT sin escala nunca
        # queda inválido ni irresoluble; se le asigna una escala genérica 1..5.
        if payload.question_type == "LIKERT" and option_set_id is None:
            default_labels = (
                "Totalmente en desacuerdo",
                "En desacuerdo",
                "Ni de acuerdo ni en desacuerdo",
                "De acuerdo",
                "Totalmente de acuerdo",
            )
            option_set = OptionSet(
                instrument_version_id=instrument_version_id,
                owner_user_id=version.instrument.owner_user_id,
                code=f"AUTO_LIKERT_{payload.code or 'ITEM'}",
                name=f"Escala automática — {payload.short_label or payload.code or 'ítem'}",
                description="Escala Likert 1 a 5 creada automáticamente por compatibilidad.",
                metadata_={
                    "kind": "LIKERT_SYSTEM_DEFAULT",
                    "points": 5,
                    "preset": "AGREEMENT_5",
                    "editable": True,
                },
                options=[
                    OptionSetOption(
                        raw_code=str(index),
                        label=label,
                        numeric_value=index,
                        sort_order=index - 1,
                    )
                    for index, label in enumerate(default_labels, start=1)
                ],
            )
            option_set = await self.repo.create_option_set(option_set)
            option_set_id = option_set.id

        # Compatibilidad: si el cliente no indica is_scored explícitamente,
        # un ítem LIKERT recién creado se asume puntuable por defecto (puede
        # desmarcarse pasando is_scored=false explícito).
        is_scored = payload.is_scored
        if "is_scored" not in payload.model_fields_set and payload.question_type == "LIKERT":
            is_scored = True
        await self._validate_scored_question(payload.question_type, is_scored, option_set_id)

        question = Question(
            instrument_version_id=instrument_version_id,
            option_set_id=option_set_id,
            code=payload.code,
            source_code=payload.source_code,
            question_text=payload.question_text,
            short_label=payload.short_label,
            question_type=payload.question_type,
            research_role=payload.research_role,
            category=payload.category,
            is_scored=is_scored,
            is_required_default=payload.is_required_default,
            sort_order=payload.sort_order,
            validation_rules=payload.validation_rules,
            metadata_=payload.metadata,
        )
        question = await self.repo.create(question)
        await self.audit.log(
            action="ITEM_CREATED",
            entity_type="question",
            entity_id=question.id,
            after_data=payload.model_dump(mode="json", exclude={"option_set"}),
        )
        await self.session.commit()
        return question

    async def update(self, question_id: int, payload: QuestionUpdate) -> Question:
        question = await self.get(question_id)
        version = await self._load_version_for_policy(question.instrument_version_id)
        await InstrumentEditPolicy.can_edit_question(self.session, version.instrument, version)

        before = QuestionRead.model_validate(question).model_dump(mode="json")
        data = payload.model_dump(exclude_unset=True)
        await self._validate_scored_question(
            data.get("question_type", question.question_type),
            data.get("is_scored", question.is_scored),
            data.get("option_set_id", question.option_set_id),
        )
        if "metadata" in data:
            question.metadata_ = data.pop("metadata")
        for field, value in data.items():
            setattr(question, field, value)

        await self.session.flush()
        await self.audit.log(
            action="ITEM_UPDATED",
            entity_type="question",
            entity_id=question.id,
            before_data=before,
            after_data=data,
        )
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def delete(self, question_id: int) -> None:
        question = await self.get(question_id)
        version = await self._load_version_for_policy(question.instrument_version_id)
        await InstrumentEditPolicy.can_edit_question(self.session, version.instrument, version)

        await self.audit.log(
            action="ITEM_DELETED", entity_type="question", entity_id=question.id
        )
        await self.repo.delete(question)
        await self.session.commit()

    async def batch_update(
        self, instrument_version_id: int, payload: QuestionBatchUpdate
    ) -> list[Question]:
        version = await self._load_version_for_policy(instrument_version_id)
        await InstrumentEditPolicy.can_edit_question(self.session, version.instrument, version)

        updated: list[Question] = []
        try:
            for item in payload.items:
                question = await self.repo.get(item.id)
                if question is None or question.instrument_version_id != instrument_version_id:
                    raise NotFoundError(f"Ítem {item.id} no encontrado en esta versión")
                data = item.patch.model_dump(exclude_unset=True)
                await self._validate_scored_question(
                    data.get("question_type", question.question_type),
                    data.get("is_scored", question.is_scored),
                    data.get("option_set_id", question.option_set_id),
                )
                if "metadata" in data:
                    question.metadata_ = data.pop("metadata")
                for field, value in data.items():
                    setattr(question, field, value)
                updated.append(question)

            await self.session.flush()
            await self.audit.log(
                action="ITEM_BATCH_UPDATED",
                entity_type="question",
                entity_id=None,
                after_data={"ids": [q.id for q in updated]},
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        for question in updated:
            await self.session.refresh(question)
        return updated
