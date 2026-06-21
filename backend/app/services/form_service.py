from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.form import Form
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
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
