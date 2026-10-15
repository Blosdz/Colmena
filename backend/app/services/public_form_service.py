from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.realtime import publish_response_event
from app.models.form import Form
from app.models.form_answer import FormAnswer
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.models.form_public_snapshot import FormPublicSnapshot
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
from app.utils.slug import generate_public_slug


class PublicFormService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def _build_public_urls(
        self,
        form: Form,
        snapshot: FormPublicSnapshot | None = None,
    ) -> PublicFormLinkRead:
        public_url = None
        api_url = None
        if form.public_slug:
            base_url = self.settings.public_base_url.rstrip("/")
            # El enlace público se sirve vía AppThesis (gateway) como tenant, si está configurado.
            gateway = self.settings.appthesis_public_url.rstrip("/")
            if gateway:
                public_url = f"{gateway}/#/{self.settings.tenant_slug}/forms/{form.public_slug}"
            else:
                public_url = f"{base_url}/public/forms/{form.public_slug}"
            # La API pública siempre apunta al backend de Colmena.
            api_url = f"{base_url}/api/public/forms/{form.public_slug}"
        return PublicFormLinkRead(
            form_id=form.id,
            status=form.status,
            public_slug=form.public_slug,
            public_url=public_url,
            api_url=api_url,
            published_instrument_ids=self._published_instrument_ids(snapshot),
        )

    def _published_instrument_ids(
        self,
        snapshot: FormPublicSnapshot | None,
    ) -> list[str]:
        if snapshot is None:
            return []
        return [
            str(instrument.get("id"))
            for instrument in snapshot.payload_json.get("instruments", [])
            if instrument.get("id")
        ]

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

    def _active_snapshot(self, form_id: str) -> FormPublicSnapshot | None:
        return self.db.scalar(
            select(FormPublicSnapshot)
            .where(
                FormPublicSnapshot.form_id == form_id,
                FormPublicSnapshot.is_active.is_(True),
            )
            .order_by(FormPublicSnapshot.version.desc())
        )

    def _create_snapshot(
        self,
        form: Form,
        instrument_ids: list[str] | None = None,
    ) -> FormPublicSnapshot:
        active_snapshot = self._active_snapshot(form.id)
        if active_snapshot is not None:
            active_snapshot.is_active = False

        latest_version = int(
            self.db.scalar(
                select(func.max(FormPublicSnapshot.version)).where(
                    FormPublicSnapshot.form_id == form.id
                )
            )
            or 0
        )
        snapshot = FormPublicSnapshot(
            form_id=form.id,
            version=latest_version + 1,
            is_active=True,
            payload_json={},
        )
        self.db.add(snapshot)
        self.db.flush()

        public_form = self._serialize_public_form(form)
        if instrument_ids is not None:
            selected_ids = set(instrument_ids)
            selected_questions = [
                question
                for question in public_form.questions
                if question.instrument_id is None or question.instrument_id in selected_ids
            ]
            selected_section_ids = {
                question.section_id
                for question in selected_questions
                if question.section_id is not None
            }
            public_form = public_form.model_copy(
                update={
                    "instruments": [
                        instrument
                        for instrument in public_form.instruments
                        if instrument.id in selected_ids
                    ],
                    "questions": selected_questions,
                    "sections": [
                        section
                        for section in public_form.sections
                        if section.id in selected_section_ids
                    ],
                }
            )
        public_form = public_form.model_copy(update={"snapshot_id": snapshot.id})
        snapshot.payload_json = public_form.model_dump(mode="json")
        return snapshot

    def _snapshot_payload(self, snapshot: FormPublicSnapshot) -> PublicFormRead:
        payload = PublicFormRead.model_validate(snapshot.payload_json)
        if payload.snapshot_id != snapshot.id:
            payload = payload.model_copy(update={"snapshot_id": snapshot.id})
        return payload

    def publish_form(
        self,
        form_id: str,
        instrument_ids: list[str] | None = None,
    ) -> tuple[Form, PublicFormLinkRead]:
        form = self._get_form(form_id)
        if self._active_questions_count(form.id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a form without active questions",
            )
        active_instrument_ids = {
            instrument.id
            for instrument in form.instruments
            if instrument.deleted_at is None
        }
        selected_instrument_ids = None
        if instrument_ids is not None:
            selected_instrument_ids = list(dict.fromkeys(instrument_ids))
            if active_instrument_ids and not selected_instrument_ids:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Selecciona al menos un instrumento para publicar.",
                )
            invalid_ids = set(selected_instrument_ids) - active_instrument_ids
            if invalid_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uno o más instrumentos no pertenecen al formulario.",
                )

        self._ensure_public_slug(form)
        form.status = "published"
        if form.collect_started_at is None:
            form.collect_started_at = datetime.now(timezone.utc)
        snapshot = self._create_snapshot(form, selected_instrument_ids)
        self.db.commit()
        self.db.refresh(form)
        return form, self._build_public_urls(form, snapshot)

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
        active_snapshot = self._active_snapshot(form.id)
        selected_instrument_ids = self._published_instrument_ids(active_snapshot)
        self._create_snapshot(form, selected_instrument_ids or None)
        self.db.commit()
        self.db.refresh(form)
        return form

    def get_public_link(self, form_id: str) -> PublicFormLinkRead:
        form = self._get_form(form_id)
        return self._build_public_urls(form, self._active_snapshot(form.id))

    def get_public_form_by_slug(self, public_slug: str) -> PublicFormRead:
        form = self._get_public_form(public_slug)
        snapshot = self._active_snapshot(form.id)
        if snapshot is None:
            snapshot = self._create_snapshot(form)
            self.db.commit()
            self.db.refresh(snapshot)
        return self._snapshot_payload(snapshot)

    def _submission_snapshot(self, form: Form, snapshot_id: str | None) -> FormPublicSnapshot:
        if snapshot_id:
            snapshot = self.db.scalar(
                select(FormPublicSnapshot).where(
                    FormPublicSnapshot.id == snapshot_id,
                    FormPublicSnapshot.form_id == form.id,
                )
            )
            if snapshot is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El cuestionario fue actualizado. Recarga el enlace para continuar.",
                )
            return snapshot

        snapshot = self._active_snapshot(form.id)
        if snapshot is None:
            snapshot = self._create_snapshot(form)
            self.db.flush()
        return snapshot

    def _snapshot_choice_score(
        self,
        question: PublicFormQuestionRead,
        selected_options: list[FormQuestionOption],
        allowed_options: list[FormQuestionOption],
    ) -> float | None:
        available_scores = [option.score for option in allowed_options if option.score is not None]
        scores: list[float] = []
        for option in selected_options:
            if option.score is None:
                continue
            score = option.score
            if question.is_reverse_scored and len(available_scores) >= 2:
                score = max(available_scores) + min(available_scores) - score
            scores.append(float(score))
        if not scores:
            return None
        return float(sum(scores))

    def _remap_answers_to_active_snapshot(
        self,
        source_form: PublicFormRead,
        active_form: PublicFormRead,
        answers: list[FormAnswer],
    ) -> None:
        if source_form.snapshot_id == active_form.snapshot_id:
            return

        source_questions = {question.id: question for question in source_form.questions}
        active_questions_by_id = {question.id: question for question in active_form.questions}
        active_questions_by_code: dict[str, list[PublicFormQuestionRead]] = {}
        for question in active_form.questions:
            if question.code:
                active_questions_by_code.setdefault(question.code, []).append(question)

        for answer in answers:
            source_question = source_questions.get(answer.question_id)
            if source_question is None:
                continue

            target_question = active_questions_by_id.get(source_question.id)
            if target_question is None and source_question.code:
                candidates = active_questions_by_code.get(source_question.code, [])
                if len(candidates) == 1 and candidates[0].question_type == source_question.question_type:
                    target_question = candidates[0]
            if target_question is None:
                continue

            source_options = {option.id: option for option in source_question.options}
            target_options_by_id = {option.id: option for option in target_question.options}
            target_options_by_value: dict[str, list[PublicFormOptionRead]] = {}
            for option in target_question.options:
                target_options_by_value.setdefault(option.value, []).append(option)

            answer.question_id = target_question.id
            if answer.option_id is not None and answer.option_id not in target_options_by_id:
                source_option = source_options.get(answer.option_id)
                candidates = (
                    target_options_by_value.get(source_option.value, [])
                    if source_option is not None
                    else []
                )
                if len(candidates) == 1:
                    answer.option_id = candidates[0].id

            if isinstance(answer.value_json, list):
                remapped_values: list = []
                for raw_value in answer.value_json:
                    if not isinstance(raw_value, str) or raw_value in target_options_by_id:
                        remapped_values.append(raw_value)
                        continue
                    source_option = source_options.get(raw_value)
                    candidates = (
                        target_options_by_value.get(source_option.value, [])
                        if source_option is not None
                        else []
                    )
                    remapped_values.append(candidates[0].id if len(candidates) == 1 else raw_value)
                answer.value_json = remapped_values

    def validate_public_response(
        self,
        form: Form,
        payload: PublicFormResponseCreate,
        public_form: PublicFormRead,
    ) -> tuple[str, list[FormAnswer]]:
        snapshot_questions = {question.id: question for question in public_form.questions}
        provided_answers = {answer.question_id: answer for answer in payload.answers}
        if len(provided_answers) != len(payload.answers):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El envío contiene respuestas duplicadas.",
            )

        for question in snapshot_questions.values():
            if question.is_required and question.id not in provided_answers:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Missing required answer for question {question.id}",
                )

        question_ids = list(snapshot_questions)
        stored_questions = list(
            self.db.scalars(
                select(FormQuestion)
                .options(selectinload(FormQuestion.options))
                .where(
                    FormQuestion.form_id == form.id,
                    FormQuestion.id.in_(question_ids),
                )
            ).all()
        )
        stored_question_map = {question.id: question for question in stored_questions}
        if len(stored_question_map) != len(snapshot_questions):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se pudo recuperar la versión original del cuestionario.",
            )

        answer_models: list[FormAnswer] = []

        for answer_payload in payload.answers:
            question = snapshot_questions.get(answer_payload.question_id)
            stored_question = stored_question_map.get(answer_payload.question_id)
            if question is None or stored_question is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El cuestionario fue actualizado. Recarga el enlace para continuar.",
                )

            allowed_option_ids = {item.id for item in question.options}
            stored_options = {
                option.id: option
                for option in stored_question.options
                if option.id in allowed_option_ids
            }
            allowed_options = list(stored_options.values())
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
                option = stored_options.get(answer_payload.option_id)
                if option is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Option does not belong to question {question.id}",
                    )
                score_value = self._snapshot_choice_score(question, [option], allowed_options)
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
                    current_option = stored_options.get(raw_item)
                    if current_option is not None:
                        selected_options.append(current_option)
                        resolved_ids.append(current_option.id)
                        continue
                    matched_by_value = next(
                        (candidate for candidate in allowed_options if candidate.value == raw_item),
                        None,
                    )
                    if matched_by_value is None:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Question {question.id} received an invalid option reference",
                        )
                    selected_options.append(matched_by_value)
                    resolved_ids.append(matched_by_value.id)
                value_json = resolved_ids
                score_value = self._snapshot_choice_score(question, selected_options, allowed_options)
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
                score_value = value_number if question.is_scored else None
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
                    question_id=stored_question.id,
                    option_id=option.id if option is not None else None,
                    value_text=value_text,
                    value_number=value_number,
                    value_date=value_date,
                    value_json=value_json,
                    score_value=score_value,
                )
            )

        response_status = "complete" if len(answer_models) == len(snapshot_questions) else "partial"
        return response_status, answer_models

    def submit_public_response(
        self,
        public_slug: str,
        payload: PublicFormResponseCreate,
        client_ip: str | None = None,
    ) -> PublicFormResponseRead:
        form = self._get_public_form_row(public_slug)
        if form.status == "closed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Form is closed")
        if form.status != "published":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public form not found")

        loaded_form = self._get_public_form(public_slug)
        snapshot = self._submission_snapshot(loaded_form, payload.snapshot_id)
        public_form = self._snapshot_payload(snapshot)
        response_status, answer_models = self.validate_public_response(
            loaded_form,
            payload,
            public_form,
        )
        active_snapshot = self._active_snapshot(loaded_form.id)
        if active_snapshot is not None:
            active_public_form = self._snapshot_payload(active_snapshot)
            self._remap_answers_to_active_snapshot(
                public_form,
                active_public_form,
                answer_models,
            )
            active_required_ids = {
                question.id for question in active_public_form.questions if question.is_required
            }
            answered_ids = {answer.question_id for answer in answer_models}
            response_status = (
                "complete" if active_required_ids.issubset(answered_ids) else "partial"
            )

        if isinstance(payload.metadata_json, dict):
            response_metadata = {
                **payload.metadata_json,
                "public_snapshot_id": snapshot.id,
            }
        else:
            response_metadata = {
                "client_metadata": payload.metadata_json,
                "public_snapshot_id": snapshot.id,
            }

        response = FormResponse(
            project_id=loaded_form.project_id,
            form_id=loaded_form.id,
            respondent_code=payload.respondent_code,
            status=response_status,
            submitted_at=datetime.now(timezone.utc),
            source="public_link",
            respondent_ip=client_ip,
            metadata_json=response_metadata,
        )
        self.db.add(response)
        self.db.flush()

        for answer in answer_models:
            answer.response_id = response.id
            self.db.add(answer)

        self.db.commit()
        self.db.refresh(response)
        publish_response_event(
            form_id=response.form_id,
            project_id=response.project_id,
            response_id=response.id,
            response_status=response.status,
            submitted_at=response.submitted_at or response.created_at,
            source=response.source,
        )
        return PublicFormResponseRead(
            status="submitted",
            response_id=response.id,
            form_id=response.form_id,
            submitted_at=response.submitted_at or response.created_at,
        )
