from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.form import Form
from app.models.form_answer import FormAnswer
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.models.form_response import FormResponse
from app.models.form_section import FormSection
from app.schemas.public_form import (
    PublicFormLinkRead,
    PublicFormOptionRead,
    PublicFormQuestionRead,
    PublicFormRead,
    PublicFormInstrumentRead,
    PublicFormDimensionRead,
    PublicFormSectionRead,
    PublicFormResponseCreate,
    PublicFormResponseRead,
)
from app.utils.scoring import calculate_multiple_choice_score, calculate_option_score
from app.utils.slug import generate_public_slug


class PublicFormService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def _build_public_urls(self, form: Form) -> PublicFormLinkRead:
        public_url = None
        api_url = None
        if form.public_slug:
            base_url = self.settings.public_base_url.rstrip("/")
            public_url = f"{base_url}/public/forms/{form.public_slug}"
            api_url = f"{base_url}/api/public/forms/{form.public_slug}"
        return PublicFormLinkRead(
            form_id=form.id,
            status=form.status,
            public_slug=form.public_slug,
            public_url=public_url,
            api_url=api_url,
        )

    def _get_form(self, form_id: str) -> Form:
        form = self.db.scalar(
            select(Form)
            .options(
                selectinload(Form.sections),
                selectinload(Form.instruments).selectinload(FormInstrument.dimensions),
                selectinload(Form.questions).selectinload(FormQuestion.options),
            )
            .where(Form.id == form_id, Form.deleted_at.is_(None))
        )
        if form is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
        return form

    def _get_public_form_row(self, public_slug: str) -> Form:
        form = self.db.scalar(
            select(Form)
            .options(
                selectinload(Form.sections),
                selectinload(Form.instruments).selectinload(FormInstrument.dimensions),
                selectinload(Form.questions).selectinload(FormQuestion.options),
            )
            .where(
                Form.public_slug == public_slug,
                Form.deleted_at.is_(None),
            )
        )
        if form is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public form not found")
        return form

    def _get_public_form(self, public_slug: str) -> Form:
        form = self._get_public_form_row(public_slug)
        if form.status != "published":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public form not found")
        return form

    def _active_questions_count(self, form_id: str) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(FormQuestion)
                .where(FormQuestion.form_id == form_id, FormQuestion.deleted_at.is_(None))
            )
            or 0
        )

    def _slug_exists(self, public_slug: str, form_id: str | None = None) -> bool:
        statement = select(Form.id).where(Form.public_slug == public_slug)
        if form_id is not None:
            statement = statement.where(Form.id != form_id)
        return self.db.scalar(statement) is not None

    def _ensure_public_slug(self, form: Form) -> str:
        if form.public_slug and not self._slug_exists(form.public_slug, form.id):
            return form.public_slug
        while True:
            candidate = generate_public_slug(form.title)
            if not self._slug_exists(candidate, form.id):
                form.public_slug = candidate
                return candidate

    def _active_questions_map(self, form: Form) -> dict[str, FormQuestion]:
        return {question.id: question for question in form.questions if question.deleted_at is None}

    def _active_options_map(self, question: FormQuestion) -> dict[str, FormQuestionOption]:
        return {option.id: option for option in question.options if option.deleted_at is None}

    def _serialize_public_form(self, form: Form) -> PublicFormRead:
        sections = [
            PublicFormSectionRead.model_validate(section)
            for section in sorted(
                (section for section in form.sections if section.deleted_at is None),
                key=lambda item: (item.sort_order, item.created_at),
            )
        ]
        instruments = [
            PublicFormInstrumentRead(
                id=instrument.id,
                name=instrument.name,
                acronym=instrument.acronym,
                dimensions=[
                    PublicFormDimensionRead.model_validate(dimension)
                    for dimension in sorted(
                        (dimension for dimension in instrument.dimensions if dimension.deleted_at is None),
                        key=lambda item: (item.sort_order, item.created_at),
                    )
                ],
            )
            for instrument in sorted(
                (instrument for instrument in form.instruments if instrument.deleted_at is None),
                key=lambda item: (item.sort_order, item.created_at),
            )
        ]
        questions = []
        for question in sorted(
            (question for question in form.questions if question.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        ):
            questions.append(
                PublicFormQuestionRead(
                    id=question.id,
                    section_id=question.section_id,
                    instrument_id=question.instrument_id,
                    dimension_id=question.dimension_id,
                    project_variable_id=question.project_variable_id,
                    code=question.code,
                    label=question.label,
                    help_text=question.help_text,
                    question_type=question.question_type,
                    question_role=question.question_role,
                    measurement_level=question.measurement_level,
                    data_type=question.data_type,
                    is_required=question.is_required,
                    is_scored=question.is_scored,
                    is_reverse_scored=question.is_reverse_scored,
                    min_value=question.min_value,
                    max_value=question.max_value,
                    sort_order=question.sort_order,
                    options=[
                        PublicFormOptionRead.model_validate(option)
                        for option in sorted(
                            (option for option in question.options if option.deleted_at is None),
                            key=lambda item: (item.sort_order, item.created_at),
                        )
                    ],
                )
            )
        return PublicFormRead(
            id=form.id,
            project_id=form.project_id,
            title=form.title,
            description=form.description,
            instructions=form.instructions,
            status=form.status,
            sections=sections,
            instruments=instruments,
            questions=questions,
            thank_you_message=form.thank_you_message,
            metadata_json=form.metadata_json,
        )

    def publish_form(self, form_id: str) -> tuple[Form, PublicFormLinkRead]:
        form = self._get_form(form_id)
        if self._active_questions_count(form.id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a form without active questions",
            )
        self._ensure_public_slug(form)
        form.status = "published"
        if form.collect_started_at is None:
            form.collect_started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(form)
        return form, self._build_public_urls(form)

    def close_form(self, form_id: str) -> Form:
        form = self._get_form(form_id)
        form.status = "closed"
        form.collect_closed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(form)
        return form

    def reopen_form(self, form_id: str) -> Form:
        form = self._get_form(form_id)
        if self._active_questions_count(form.id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reopen a form without active questions",
            )
        self._ensure_public_slug(form)
        form.status = "published"
        if form.collect_started_at is None:
            form.collect_started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(form)
        return form

    def get_public_link(self, form_id: str) -> PublicFormLinkRead:
        form = self._get_form(form_id)
        return self._build_public_urls(form)

    def get_public_form_by_slug(self, public_slug: str) -> PublicFormRead:
        form = self._get_public_form(public_slug)
        return self._serialize_public_form(form)

    def calculate_score_value(
        self,
        question: FormQuestion,
        *,
        option: FormQuestionOption | None = None,
        value_number: float | None = None,
        selected_options: list[FormQuestionOption] | None = None,
    ) -> float | None:
        if option is not None:
            return calculate_option_score(question, option)
        if selected_options:
            return calculate_multiple_choice_score(question, selected_options)
        if question.question_type == "number" and question.is_scored and value_number is not None:
            return value_number
        return None

    def validate_public_response(self, form: Form, payload: PublicFormResponseCreate) -> tuple[str, list[FormAnswer]]:
        active_questions = self._active_questions_map(form)
        provided_answers = {answer.question_id: answer for answer in payload.answers}

        for question in active_questions.values():
            if question.is_required and question.id not in provided_answers:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Missing required answer for question {question.id}",
                )

        answer_models: list[FormAnswer] = []

        for answer_payload in payload.answers:
            question = active_questions.get(answer_payload.question_id)
            if question is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Answer references an invalid or inactive question",
                )

            active_options = self._active_options_map(question)
            option = None
            score_value = None
            value_text = answer_payload.value_text
            value_number = answer_payload.value_number
            value_date = answer_payload.value_date
            value_json = answer_payload.value_json

            if question.question_type in {"single_choice", "dropdown", "likert", "boolean"}:
                if answer_payload.option_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=f"Question {question.id} requires a valid option_id",
                    )
                option = active_options.get(answer_payload.option_id)
                if option is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Option does not belong to question {question.id}",
                    )
                score_value = self.calculate_score_value(question, option=option)
            elif question.question_type == "multiple_choice":
                if not isinstance(value_json, list) or not value_json:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail=f"Question {question.id} requires value_json as a non-empty list",
                        )
                selected_options: list[FormQuestionOption] = []
                resolved_ids: list[str] = []
                for raw_item in value_json:
                    if not isinstance(raw_item, str):
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail=f"Question {question.id} expects option ids as strings",
                        )
                    current_option = active_options.get(raw_item)
                    if current_option is not None:
                        selected_options.append(current_option)
                        resolved_ids.append(current_option.id)
                        continue
                    matched_by_value = next((candidate for candidate in active_options.values() if candidate.value == raw_item), None)
                    if matched_by_value is None:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Question {question.id} received an invalid option reference",
                        )
                    selected_options.append(matched_by_value)
                    resolved_ids.append(matched_by_value.id)
                value_json = resolved_ids
                score_value = self.calculate_score_value(question, selected_options=selected_options)
            elif question.question_type == "number":
                if value_number is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=f"Question {question.id} requires value_number",
                    )
                if question.min_value is not None and value_number < question.min_value:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=f"Question {question.id} is below min_value",
                    )
                if question.max_value is not None and value_number > question.max_value:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=f"Question {question.id} is above max_value",
                    )
                score_value = self.calculate_score_value(question, value_number=value_number)
            elif question.question_type in {"text_short", "text_long"}:
                if question.is_required and not value_text:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=f"Question {question.id} requires value_text",
                    )
            elif question.question_type == "date":
                if value_date is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=f"Question {question.id} requires value_date",
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported public question type {question.question_type}",
                )

            answer_models.append(
                FormAnswer(
                    question_id=question.id,
                    option_id=option.id if option is not None else None,
                    value_text=value_text,
                    value_number=value_number,
                    value_date=value_date,
                    value_json=value_json,
                    score_value=score_value,
                )
            )

        response_status = "complete" if len(answer_models) == len(active_questions) else "partial"
        return response_status, answer_models

    def submit_public_response(self, public_slug: str, payload: PublicFormResponseCreate) -> PublicFormResponseRead:
        form = self._get_public_form_row(public_slug)
        if form.status == "closed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Form is closed")
        if form.status != "published":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public form not found")

        loaded_form = self._get_public_form(public_slug)
        response_status, answer_models = self.validate_public_response(loaded_form, payload)

        response = FormResponse(
            project_id=loaded_form.project_id,
            form_id=loaded_form.id,
            respondent_code=payload.respondent_code,
            status=response_status,
            submitted_at=datetime.now(timezone.utc),
            source="public_link",
            metadata_json=payload.metadata_json,
        )
        self.db.add(response)
        self.db.flush()

        for answer in answer_models:
            answer.response_id = response.id
            self.db.add(answer)

        self.db.commit()
        self.db.refresh(response)
        return PublicFormResponseRead(
            status="submitted",
            response_id=response.id,
            form_id=response.form_id,
            submitted_at=response.submitted_at or response.created_at,
        )
