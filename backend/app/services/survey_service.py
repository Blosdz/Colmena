from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationDomainError
from app.core.pagination import Page, PageParams, paginate
from app.models.survey import Survey, SurveyQuestion, SurveySection
from app.repositories.instruments import InstrumentRepository
from app.repositories.questions import QuestionRepository
from app.repositories.surveys import SurveyRepository
from app.schemas.surveys import (
    SurveyCreate,
    SurveyFromInstrumentCreate,
    SurveyRead,
    SurveyUpdate,
)
from app.services.audit_service import AuditService


class SurveyService:
    """CRUD de surveys + creación desde instrumento (harness §14)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SurveyRepository(session)
        self.instrument_repo = InstrumentRepository(session)
        self.question_repo = QuestionRepository(session)
        self.audit = AuditService(session)

    async def create(self, project_id: int, payload: SurveyCreate) -> Survey:
        survey = Survey(
            project_id=project_id,
            created_by_user_id=payload.created_by_user_id,
            name=payload.name,
            description=payload.description,
            survey_type=payload.survey_type,
            settings=payload.settings,
        )
        survey = await self.repo.create(survey)
        await self.audit.log(
            action="SURVEY_CREATED", entity_type="survey", entity_id=survey.id, project_id=project_id
        )
        await self.session.commit()
        return survey

    async def create_from_instrument(
        self, project_id: int, payload: SurveyFromInstrumentCreate
    ) -> Survey:
        """No duplica los ítems del instrumento: crea `survey_questions` apuntando
        a las `questions` existentes de la versión (harness §14)."""
        version = await self.instrument_repo.get_version_with_instrument(
            payload.instrument_version_id
        )
        if version is None:
            raise NotFoundError(f"Versión de instrumento {payload.instrument_version_id} no encontrada")
        if version.instrument.project_id not in (None, project_id):
            raise ValidationDomainError(
                "La versión de instrumento no pertenece a este proyecto."
            )

        questions = await self.question_repo.list_by_version(payload.instrument_version_id)
        if not questions:
            raise ValidationDomainError(
                "La versión de instrumento no tiene ítems; no se puede crear el survey."
            )

        survey = Survey(
            project_id=project_id,
            instrument_version_id=payload.instrument_version_id,
            created_by_user_id=payload.created_by_user_id,
            name=payload.name,
            description=payload.description,
            survey_type=payload.survey_type,
        )
        survey = await self.repo.create(survey)

        exogenous_section = None
        instrument_section = None
        if any(question.research_role == "EXOGENOUS" for question in questions):
            exogenous_section = SurveySection(
                survey_id=survey.id,
                title="Datos de perfil",
                description="Información exógena para segmentar resultados; no forma parte del puntaje.",
                section_kind="EXOGENOUS",
                sort_order=0,
            )
            self.session.add(exogenous_section)
        if any(question.research_role != "EXOGENOUS" for question in questions):
            instrument_section = SurveySection(
                survey_id=survey.id,
                title="Instrumento",
                description="Ítems del instrumento de medición.",
                section_kind="INSTRUMENT",
                sort_order=1,
            )
            self.session.add(instrument_section)
        await self.session.flush()

        ordered_questions = sorted(
            questions,
            key=lambda question: (
                0 if question.research_role == "EXOGENOUS" else 1,
                question.sort_order if question.sort_order is not None else question.id,
            ),
        )
        for index, question in enumerate(ordered_questions):
            section = exogenous_section if question.research_role == "EXOGENOUS" else instrument_section
            link = SurveyQuestion(
                survey_id=survey.id,
                question_id=question.id,
                section_id=section.id if section else None,
                sort_order=index,
                is_required=question.is_required_default,
            )
            await self.repo.add_question(link)

        await self.audit.log(
            action="SURVEY_CREATED_FROM_INSTRUMENT",
            entity_type="survey",
            entity_id=survey.id,
            project_id=project_id,
            after_data={"instrument_version_id": payload.instrument_version_id},
        )
        await self.session.commit()
        return survey

    async def get(self, survey_id: int) -> Survey:
        survey = await self.repo.get(survey_id)
        if survey is None:
            raise NotFoundError(f"Survey {survey_id} no encontrado")
        return survey

    async def list_by_project(self, project_id: int, params: PageParams) -> Page[SurveyRead]:
        items, total = await paginate(self.session, self.repo.list_by_project_stmt(project_id), params)
        return Page[SurveyRead](
            items=[SurveyRead.model_validate(item) for item in items],
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    async def update(self, survey_id: int, payload: SurveyUpdate) -> Survey:
        survey = await self.get(survey_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(survey, field, value)
        await self.session.commit()
        await self.session.refresh(survey)
        return survey

    async def delete(self, survey_id: int) -> None:
        survey = await self.get(survey_id)
        await self.repo.delete(survey)
        await self.session.commit()
