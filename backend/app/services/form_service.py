from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.base import Base
from app.models.form import Form
from app.models.form_answer import FormAnswer
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.models.form_response import FormResponse
from app.models.form_section import FormSection
from app.models.project import Project
from app.models.project_variable import ProjectVariable
from app.schemas.form import FormCreate, FormUpdate
from app.schemas.form_dimension import FormDimensionCreate, FormDimensionUpdate
from app.schemas.form_instrument import FormInstrumentCreate, FormInstrumentUpdate
from app.schemas.form_question import FormQuestionCreate, FormQuestionUpdate
from app.schemas.form_question_option import FormQuestionOptionCreate, FormQuestionOptionUpdate
from app.schemas.form_section import FormSectionCreate, FormSectionUpdate


class FormService:
    def __init__(self, db: Session):
        self.db = db

    def _get_project(self, project_id: str) -> Project:
        project = self.db.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.deleted_at.is_(None),
            )
        )
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def _get_form(self, form_id: str) -> Form:
        form = self.db.scalar(
            select(Form).where(
                Form.id == form_id,
                Form.deleted_at.is_(None),
            )
        )
        if form is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
        return form

    def _get_section(self, section_id: str) -> FormSection:
        section = self.db.scalar(
            select(FormSection).where(
                FormSection.id == section_id,
                FormSection.deleted_at.is_(None),
            )
        )
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form section not found")
        return section

    def _get_instrument(self, instrument_id: str) -> FormInstrument:
        instrument = self.db.scalar(
            select(FormInstrument).where(
                FormInstrument.id == instrument_id,
                FormInstrument.deleted_at.is_(None),
            )
        )
        if instrument is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form instrument not found")
        return instrument

    def _get_dimension(self, dimension_id: str) -> FormDimension:
        dimension = self.db.scalar(
            select(FormDimension).where(
                FormDimension.id == dimension_id,
                FormDimension.deleted_at.is_(None),
            )
        )
        if dimension is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form dimension not found")
        return dimension

    def _get_question(self, question_id: str) -> FormQuestion:
        question = self.db.scalar(
            select(FormQuestion).where(
                FormQuestion.id == question_id,
                FormQuestion.deleted_at.is_(None),
            )
        )
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form question not found")
        return question

    def _get_option(self, option_id: str) -> FormQuestionOption:
        option = self.db.scalar(
            select(FormQuestionOption).where(
                FormQuestionOption.id == option_id,
                FormQuestionOption.deleted_at.is_(None),
            )
        )
        if option is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form question option not found")
        return option

    def _get_project_variable_for_project(self, project_id: str, variable_id: str) -> ProjectVariable:
        variable = self.db.scalar(
            select(ProjectVariable).where(
                ProjectVariable.id == variable_id,
                ProjectVariable.project_id == project_id,
                ProjectVariable.deleted_at.is_(None),
            )
        )
        if variable is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project variable not found")
        return variable

    def _validate_question_links(
        self,
        form: Form,
        *,
        section_id: str | None,
        instrument_id: str | None,
        dimension_id: str | None,
        project_variable_id: str | None,
    ) -> dict[str, str | None]:
        resolved_section_id = section_id
        resolved_instrument_id = instrument_id
        resolved_dimension_id = dimension_id
        resolved_variable_id = project_variable_id

        if resolved_section_id is not None:
            section = self._get_section(resolved_section_id)
            if section.form_id != form.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Section does not belong to the target form",
                )

        instrument = None
        if resolved_instrument_id is not None:
            instrument = self._get_instrument(resolved_instrument_id)
            if instrument.form_id != form.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Instrument does not belong to the target form",
                )

        if resolved_dimension_id is not None:
            dimension = self._get_dimension(resolved_dimension_id)
            dimension_instrument = self._get_instrument(dimension.instrument_id)
            if dimension_instrument.form_id != form.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Dimension does not belong to the target form",
                )
            if instrument is None:
                instrument = dimension_instrument
                resolved_instrument_id = dimension.instrument_id
            elif dimension.instrument_id != instrument.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Dimension does not belong to the selected instrument",
                )

        if resolved_variable_id is not None:
            self._get_project_variable_for_project(form.project_id, resolved_variable_id)

        return {
            "section_id": resolved_section_id,
            "instrument_id": resolved_instrument_id,
            "dimension_id": resolved_dimension_id,
            "project_variable_id": resolved_variable_id,
        }

    def create_form(self, project_id: str, payload: FormCreate) -> Form:
        self._get_project(project_id)
        form = Form(project_id=project_id, **payload.model_dump())
        self.db.add(form)
        self.db.commit()
        self.db.refresh(form)
        return form

    def list_forms(self, project_id: str) -> tuple[list[Form], int]:
        self._get_project(project_id)
        filters = [Form.project_id == project_id, Form.deleted_at.is_(None)]
        items = list(self.db.scalars(select(Form).where(*filters).order_by(Form.created_at.asc())).all())
        total = int(self.db.scalar(select(func.count()).select_from(Form).where(*filters)) or 0)
        return items, total

    def consolidate_project_forms(self, project_id: str) -> Form:
        project = self._get_project(project_id)
        forms = list(
            self.db.scalars(
                select(Form)
                .options(
                    selectinload(Form.sections),
                    selectinload(Form.instruments),
                    selectinload(Form.questions).selectinload(FormQuestion.options),
                )
                .where(Form.project_id == project_id, Form.deleted_at.is_(None))
                .order_by(Form.created_at.asc())
            ).all()
        )
        if not forms:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project has no forms")

        response_counts = dict(
            self.db.execute(
                select(FormResponse.form_id, func.count(FormResponse.id))
                .where(
                    FormResponse.form_id.in_([form.id for form in forms]),
                    FormResponse.deleted_at.is_(None),
                )
                .group_by(FormResponse.form_id)
            ).all()
        )
        primary = max(
            enumerate(forms),
            key=lambda item: (int(response_counts.get(item[1].id, 0)), -item[0]),
        )[1]
        now = datetime.now(timezone.utc)

        def is_participant_section(section: FormSection) -> bool:
            return section.title.strip().casefold() == "datos del participante"

        participant_section = next(
            (
                section
                for section in primary.sections
                if section.deleted_at is None and is_participant_section(section)
            ),
            None,
        )
        participant_questions = {
            question.code.casefold(): question
            for question in primary.questions
            if question.deleted_at is None
            and question.instrument_id is None
            and question.code
            and (
                question.question_role == "sociodemographic"
                or any(
                    section.id == question.section_id and is_participant_section(section)
                    for section in primary.sections
                    if section.deleted_at is None
                )
            )
        }

        excluded_bulk_tables = {
            "form_instruments",
            "form_public_snapshots",
            "form_questions",
            "form_sections",
        }

        for secondary in forms:
            if secondary.id == primary.id:
                continue

            secondary_participant_sections = {
                section.id
                for section in secondary.sections
                if section.deleted_at is None and is_participant_section(section)
            }
            if participant_section is None and secondary_participant_sections:
                participant_section = next(
                    section
                    for section in secondary.sections
                    if section.id in secondary_participant_sections
                )
                participant_section.form_id = primary.id
                secondary_participant_sections.remove(participant_section.id)

            for section in secondary.sections:
                if section.deleted_at is not None or section.id == getattr(participant_section, "id", None):
                    continue
                if section.id in secondary_participant_sections:
                    section.deleted_at = now
                else:
                    section.form_id = primary.id

            for instrument in secondary.instruments:
                if instrument.deleted_at is None:
                    instrument.form_id = primary.id

            for question in secondary.questions:
                if question.deleted_at is not None:
                    continue
                is_participant_question = (
                    question.instrument_id is None
                    and (
                        question.question_role == "sociodemographic"
                        or question.section_id in secondary_participant_sections
                    )
                )
                target = (
                    participant_questions.get(question.code.casefold())
                    if is_participant_question and question.code
                    else None
                )
                if target is not None and target.question_type == question.question_type:
                    source_options = {option.id: option for option in question.options}
                    target_options_by_value: dict[str, list[FormQuestionOption]] = {}
                    for option in target.options:
                        if option.deleted_at is None:
                            target_options_by_value.setdefault(option.value, []).append(option)

                    staged_answers: list[tuple[FormAnswer, str | None, list | dict | None]] = []
                    can_merge = True
                    answers = list(
                        self.db.scalars(
                            select(FormAnswer).where(FormAnswer.question_id == question.id)
                        ).all()
                    )
                    for answer in answers:
                        target_option_id = answer.option_id
                        if answer.option_id is not None:
                            source_option = source_options.get(answer.option_id)
                            candidates = (
                                target_options_by_value.get(source_option.value, [])
                                if source_option is not None
                                else []
                            )
                            if len(candidates) != 1:
                                can_merge = False
                                break
                            target_option_id = candidates[0].id

                        target_value_json = answer.value_json
                        if isinstance(answer.value_json, list):
                            target_value_json = []
                            for raw_value in answer.value_json:
                                if not isinstance(raw_value, str):
                                    target_value_json.append(raw_value)
                                    continue
                                source_option = source_options.get(raw_value)
                                candidates = (
                                    target_options_by_value.get(source_option.value, [])
                                    if source_option is not None
                                    else []
                                )
                                if len(candidates) != 1:
                                    can_merge = False
                                    break
                                target_value_json.append(candidates[0].id)
                        if not can_merge:
                            break
                        staged_answers.append((answer, target_option_id, target_value_json))

                    if can_merge:
                        for answer, target_option_id, target_value_json in staged_answers:
                            duplicate = self.db.scalar(
                                select(FormAnswer).where(
                                    FormAnswer.response_id == answer.response_id,
                                    FormAnswer.question_id == target.id,
                                    FormAnswer.id != answer.id,
                                )
                            )
                            if duplicate is not None:
                                self.db.delete(answer)
                                continue
                            answer.question_id = target.id
                            answer.option_id = target_option_id
                            answer.value_json = target_value_json
                        question.deleted_at = now
                        continue

                question.form_id = primary.id
                if is_participant_question and participant_section is not None:
                    question.section_id = participant_section.id
                    if question.code:
                        participant_questions.setdefault(question.code.casefold(), question)

            for table in Base.metadata.tables.values():
                if table.name in excluded_bulk_tables or "form_id" not in table.c:
                    continue
                self.db.execute(
                    update(table)
                    .where(table.c.form_id == secondary.id)
                    .values(form_id=primary.id)
                )

            secondary.status = "closed"
            secondary.collect_closed_at = now
            secondary.deleted_at = now

        self.db.flush()

        active_instruments = list(
            self.db.scalars(
                select(FormInstrument)
                .where(
                    FormInstrument.form_id == primary.id,
                    FormInstrument.deleted_at.is_(None),
                )
                .order_by(FormInstrument.sort_order.asc(), FormInstrument.created_at.asc())
            ).all()
        )
        active_sections = list(
            self.db.scalars(
                select(FormSection).where(
                    FormSection.form_id == primary.id,
                    FormSection.deleted_at.is_(None),
                )
            ).all()
        )
        if participant_section is not None:
            participant_section.sort_order = 0

        for index, instrument in enumerate(active_instruments, start=1):
            instrument.sort_order = index - 1
            instrument_section = next(
                (
                    section
                    for section in active_sections
                    if not is_participant_section(section)
                    and section.title.strip().casefold() == instrument.name.strip().casefold()
                ),
                None,
            )
            if instrument_section is None:
                instrument_section = FormSection(
                    form_id=primary.id,
                    title=instrument.name,
                    description=instrument.description,
                    sort_order=index,
                )
                self.db.add(instrument_section)
                self.db.flush()
                active_sections.append(instrument_section)
            else:
                instrument_section.sort_order = index

            instrument_questions = list(
                self.db.scalars(
                    select(FormQuestion)
                    .where(
                        FormQuestion.form_id == primary.id,
                        FormQuestion.instrument_id == instrument.id,
                        FormQuestion.deleted_at.is_(None),
                    )
                    .order_by(FormQuestion.sort_order.asc(), FormQuestion.created_at.asc())
                ).all()
            )
            for question_index, question in enumerate(instrument_questions):
                question.section_id = instrument_section.id
                question.sort_order = question_index

        required_question_ids = set(
            self.db.scalars(
                select(FormQuestion.id).where(
                    FormQuestion.form_id == primary.id,
                    FormQuestion.deleted_at.is_(None),
                    FormQuestion.is_required.is_(True),
                )
            ).all()
        )
        responses = list(
            self.db.scalars(
                select(FormResponse).where(
                    FormResponse.form_id == primary.id,
                    FormResponse.deleted_at.is_(None),
                )
            ).all()
        )
        for response in responses:
            answered_question_ids = set(
                self.db.scalars(
                    select(FormAnswer.question_id).where(FormAnswer.response_id == response.id)
                ).all()
            )
            response.status = (
                "complete" if required_question_ids.issubset(answered_question_ids) else "partial"
            )

        primary.title = project.title
        self.db.commit()
        self.db.refresh(primary)
        return primary

    def get_form(self, form_id: str) -> Form:
        return self._get_form(form_id)

    def update_form(self, form_id: str, payload: FormUpdate) -> Form:
        form = self._get_form(form_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(form, field, value)
        self.db.commit()
        self.db.refresh(form)
        return form

    def soft_delete_form(self, form_id: str) -> dict[str, str]:
        form = self._get_form(form_id)
        form.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": form.id}

    def create_section(self, form_id: str, payload: FormSectionCreate) -> FormSection:
        self._get_form(form_id)
        section = FormSection(form_id=form_id, **payload.model_dump())
        self.db.add(section)
        self.db.commit()
        self.db.refresh(section)
        return section

    def list_sections(self, form_id: str) -> tuple[list[FormSection], int]:
        self._get_form(form_id)
        filters = [FormSection.form_id == form_id, FormSection.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(FormSection)
                .where(*filters)
                .order_by(FormSection.sort_order.asc(), FormSection.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(FormSection).where(*filters)) or 0)
        return items, total

    def update_section(self, section_id: str, payload: FormSectionUpdate) -> FormSection:
        section = self._get_section(section_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(section, field, value)
        self.db.commit()
        self.db.refresh(section)
        return section

    def soft_delete_section(self, section_id: str) -> dict[str, str]:
        section = self._get_section(section_id)
        section.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": section.id}

    def create_instrument(self, form_id: str, payload: FormInstrumentCreate) -> FormInstrument:
        form = self._get_form(form_id)
        data = payload.model_dump()
        variable_id = data.get("project_variable_id")
        if variable_id is not None:
            self._get_project_variable_for_project(form.project_id, variable_id)
        instrument = FormInstrument(form_id=form_id, **data)
        self.db.add(instrument)
        self.db.commit()
        self.db.refresh(instrument)
        return instrument

    def list_instruments(self, form_id: str) -> tuple[list[FormInstrument], int]:
        self._get_form(form_id)
        filters = [FormInstrument.form_id == form_id, FormInstrument.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(FormInstrument)
                .where(*filters)
                .order_by(FormInstrument.sort_order.asc(), FormInstrument.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(FormInstrument).where(*filters)) or 0)
        return items, total

    def update_instrument(self, instrument_id: str, payload: FormInstrumentUpdate) -> FormInstrument:
        instrument = self._get_instrument(instrument_id)
        update_data = payload.model_dump(exclude_unset=True)
        variable_id = update_data.get("project_variable_id")
        if variable_id is not None:
            self._get_project_variable_for_project(instrument.form.project_id, variable_id)
        for field, value in update_data.items():
            setattr(instrument, field, value)
        self.db.commit()
        self.db.refresh(instrument)
        return instrument

    def soft_delete_instrument(self, instrument_id: str) -> dict[str, str]:
        instrument = self._get_instrument(instrument_id)
        instrument.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": instrument.id}

    def create_dimension(self, instrument_id: str, payload: FormDimensionCreate) -> FormDimension:
        self._get_instrument(instrument_id)
        dimension = FormDimension(instrument_id=instrument_id, **payload.model_dump())
        self.db.add(dimension)
        self.db.commit()
        self.db.refresh(dimension)
        return dimension

    def list_dimensions(self, instrument_id: str) -> tuple[list[FormDimension], int]:
        self._get_instrument(instrument_id)
        filters = [FormDimension.instrument_id == instrument_id, FormDimension.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(FormDimension)
                .where(*filters)
                .order_by(FormDimension.sort_order.asc(), FormDimension.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(FormDimension).where(*filters)) or 0)
        return items, total

    def update_dimension(self, dimension_id: str, payload: FormDimensionUpdate) -> FormDimension:
        dimension = self._get_dimension(dimension_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(dimension, field, value)
        self.db.commit()
        self.db.refresh(dimension)
        return dimension

    def soft_delete_dimension(self, dimension_id: str) -> dict[str, str]:
        dimension = self._get_dimension(dimension_id)
        dimension.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": dimension.id}

    def create_question(self, form_id: str, payload: FormQuestionCreate) -> FormQuestion:
        form = self._get_form(form_id)
        data = payload.model_dump()
        resolved_links = self._validate_question_links(
            form,
            section_id=data.get("section_id"),
            instrument_id=data.get("instrument_id"),
            dimension_id=data.get("dimension_id"),
            project_variable_id=data.get("project_variable_id"),
        )
        data.update(resolved_links)
        question = FormQuestion(form_id=form_id, **data)
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def list_questions(self, form_id: str) -> tuple[list[FormQuestion], int]:
        self._get_form(form_id)
        filters = [FormQuestion.form_id == form_id, FormQuestion.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(FormQuestion)
                .where(*filters)
                .order_by(FormQuestion.sort_order.asc(), FormQuestion.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(FormQuestion).where(*filters)) or 0)
        return items, total

    def get_question(self, question_id: str) -> FormQuestion:
        return self._get_question(question_id)

    def update_question(self, question_id: str, payload: FormQuestionUpdate) -> FormQuestion:
        question = self._get_question(question_id)
        update_data = payload.model_dump(exclude_unset=True)

        current_links = {
            "section_id": question.section_id,
            "instrument_id": question.instrument_id,
            "dimension_id": question.dimension_id,
            "project_variable_id": question.project_variable_id,
        }
        current_links.update({key: update_data.get(key, current_links[key]) for key in current_links})
        resolved_links = self._validate_question_links(question.form, **current_links)
        update_data.update(resolved_links)

        for field, value in update_data.items():
            setattr(question, field, value)

        self.db.commit()
        self.db.refresh(question)
        return question

    def soft_delete_question(self, question_id: str) -> dict[str, str]:
        question = self._get_question(question_id)
        question.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": question.id}

    def create_option(self, question_id: str, payload: FormQuestionOptionCreate) -> FormQuestionOption:
        self._get_question(question_id)
        option = FormQuestionOption(question_id=question_id, **payload.model_dump())
        self.db.add(option)
        self.db.commit()
        self.db.refresh(option)
        return option

    def list_options(self, question_id: str) -> tuple[list[FormQuestionOption], int]:
        self._get_question(question_id)
        filters = [FormQuestionOption.question_id == question_id, FormQuestionOption.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(FormQuestionOption)
                .where(*filters)
                .order_by(FormQuestionOption.sort_order.asc(), FormQuestionOption.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(FormQuestionOption).where(*filters)) or 0)
        return items, total

    def update_option(self, option_id: str, payload: FormQuestionOptionUpdate) -> FormQuestionOption:
        option = self._get_option(option_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(option, field, value)
        self.db.commit()
        self.db.refresh(option)
        return option

    def soft_delete_option(self, option_id: str) -> dict[str, str]:
        option = self._get_option(option_id)
        option.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": option.id}
