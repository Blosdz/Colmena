from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from fastapi import HTTPException, status

from app.models.base import utc_now
from app.models.form import Form
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.models.form_response import FormResponse
from app.models.form_answer import FormAnswer
from app.schemas.form_response import FormResponseCreate
from app.utils.scoring import calculate_option_score


class ResponseService:
    def __init__(self, db: Session):
        self.db = db

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

    def _get_question_for_form(self, form_id: str, question_id: str) -> FormQuestion:
        question = self.db.scalar(
            select(FormQuestion).where(
                FormQuestion.id == question_id,
                FormQuestion.form_id == form_id,
                FormQuestion.deleted_at.is_(None),
            )
        )
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form question not found")
        return question

    def _get_option_for_question(self, question_id: str, option_id: str) -> FormQuestionOption:
        option = self.db.scalar(
            select(FormQuestionOption).where(
                FormQuestionOption.id == option_id,
                FormQuestionOption.question_id == question_id,
                FormQuestionOption.deleted_at.is_(None),
            )
        )
        if option is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form question option not found")
        return option

    def _get_response(self, response_id: str) -> FormResponse:
        response = self.db.scalar(
            select(FormResponse)
            .options(selectinload(FormResponse.answers))
            .where(
                FormResponse.id == response_id,
                FormResponse.deleted_at.is_(None),
            )
        )
        if response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form response not found")
        return response

    def create_response(self, form_id: str, payload: FormResponseCreate) -> FormResponse:
        form = self._get_form(form_id)
        response = FormResponse(
            project_id=form.project_id,
            form_id=form.id,
            respondent_code=payload.respondent_code,
            status=payload.status,
            submitted_at=payload.submitted_at or utc_now(),
            source=payload.source,
            metadata_json=payload.metadata_json,
        )
        self.db.add(response)
        self.db.flush()

        for answer_payload in payload.answers:
            question = self._get_question_for_form(form.id, answer_payload.question_id)
            option = None
            if answer_payload.option_id is not None:
                option = self._get_option_for_question(question.id, answer_payload.option_id)

            answer = FormAnswer(
                response_id=response.id,
                question_id=question.id,
                option_id=option.id if option is not None else None,
                value_text=answer_payload.value_text,
                value_number=answer_payload.value_number,
                value_date=answer_payload.value_date,
                value_json=answer_payload.value_json,
                score_value=answer_payload.score_value
                if answer_payload.score_value is not None
                else (
                    calculate_option_score(question, option)
                    if option is not None
                    else (
                        answer_payload.value_number
                        if question.question_type == "number" and question.is_scored and answer_payload.value_number is not None
                        else None
                    )
                ),
            )
            self.db.add(answer)

        self.db.commit()
        return self._get_response(response.id)

    def list_responses(self, form_id: str) -> tuple[list[FormResponse], int]:
        self._get_form(form_id)
        filters = [FormResponse.form_id == form_id, FormResponse.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(FormResponse)
                .options(selectinload(FormResponse.answers))
                .where(*filters)
                .order_by(FormResponse.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(FormResponse).where(*filters)) or 0)
        return items, total

    def get_response(self, response_id: str) -> FormResponse:
        return self._get_response(response_id)
