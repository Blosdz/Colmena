from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.base import utc_now
from app.models.export_artifact import ExportArtifact
from app.models.form import Form
from app.models.form_answer import FormAnswer
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.models.form_response import FormResponse
from app.models.form_section import FormSection
from app.models.project_variable import ProjectVariable
from app.schemas.dataset import (
    AnswerUpdateRequest,
    CompletenessItemRead,
    CompletenessSummaryRead,
    DataDictionaryItemRead,
    DataDictionaryRead,
    DatasetColumnRead,
    DatasetExportRead,
    DatasetRead,
    ResponseStatusRead,
)
from app.utils.columns import build_fallback_column_name, sanitize_column_name
from app.utils.scoring import calculate_multiple_choice_score, calculate_option_score


ALLOWED_DATASET_MODES = {"label", "value", "score", "mixed"}
ALLOWED_RESPONSE_STATUSES = {"partial", "complete", "discarded"}


@dataclass
class QuestionColumnConfig:
    question_id: str
    base_name: str
    label: str
    column_names: list[str]
    question_type: str


class DatasetService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.exports_dir = self.settings.backend_dir / "data" / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def _get_form(self, form_id: str) -> Form:
        form = self.db.scalar(
            select(Form)
            .options(
                selectinload(Form.questions).selectinload(FormQuestion.options),
                selectinload(Form.questions).selectinload(FormQuestion.section),
                selectinload(Form.questions).selectinload(FormQuestion.instrument),
                selectinload(Form.questions).selectinload(FormQuestion.dimension),
                selectinload(Form.questions).selectinload(FormQuestion.project_variable),
                selectinload(Form.responses).selectinload(FormResponse.answers).selectinload(FormAnswer.option),
                selectinload(Form.sections),
                selectinload(Form.instruments).selectinload(FormInstrument.dimensions),
            )
            .where(Form.id == form_id, Form.deleted_at.is_(None))
        )
        if form is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
        return form

    def _get_question(self, question_id: str) -> FormQuestion:
        question = self.db.scalar(
            select(FormQuestion)
            .options(selectinload(FormQuestion.options))
            .where(FormQuestion.id == question_id, FormQuestion.deleted_at.is_(None))
        )
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form question not found")
        return question

    def _get_answer(self, answer_id: str) -> FormAnswer:
        answer = self.db.scalar(
            select(FormAnswer)
            .options(
                selectinload(FormAnswer.question).selectinload(FormQuestion.options),
                selectinload(FormAnswer.option),
                selectinload(FormAnswer.response),
            )
            .where(FormAnswer.id == answer_id)
        )
        if answer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form answer not found")
        return answer

    def _get_response(self, response_id: str) -> FormResponse:
        response = self.db.scalar(
            select(FormResponse)
            .where(FormResponse.id == response_id, FormResponse.deleted_at.is_(None))
        )
        if response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form response not found")
        return response

    def _get_option_for_question(self, question: FormQuestion, option_id: str) -> FormQuestionOption:
        option = next(
            (current for current in question.options if current.id == option_id and current.deleted_at is None),
            None,
        )
        if option is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Option does not belong to question")
        return option

    def _get_form_responses(self, form: Form, include_discarded: bool) -> list[FormResponse]:
        responses = [response for response in form.responses if response.deleted_at is None]
        if not include_discarded:
            responses = [response for response in responses if response.status != "discarded"]
        return sorted(
            responses,
            key=lambda item: (
                item.submitted_at or item.created_at,
                item.created_at,
            ),
        )

    def _serialize_datetime(self, value: datetime | None) -> str | None:
        return value.isoformat() if value is not None else None

    def get_form_with_structure(self, form_id: str) -> Form:
        return self._get_form(form_id)

    def resolve_question_column_map(
        self,
        form: Form,
        *,
        mode: str,
        expand_multiple_choice: bool,
        include_metadata: bool,
    ) -> tuple[list[DatasetColumnRead], dict[str, QuestionColumnConfig]]:
        if mode not in ALLOWED_DATASET_MODES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid dataset mode")

        used_names: dict[str, int] = {}
        columns: list[DatasetColumnRead] = []
        mapping: dict[str, QuestionColumnConfig] = {}

        if include_metadata:
            for metadata_name in [
                "response_id",
                "project_id",
                "form_id",
                "respondent_code",
                "response_status",
                "source",
                "submitted_at",
                "created_at",
            ]:
                columns.append(
                    DatasetColumnRead(
                        name=metadata_name,
                        label=metadata_name,
                        question_id=None,
                        kind="metadata",
                    )
                )

        active_questions = sorted(
            (question for question in form.questions if question.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )

        for question in active_questions:
            raw_name = sanitize_column_name(question.code or "") or build_fallback_column_name(question.sort_order, question.id)
            count = used_names.get(raw_name, 0) + 1
            used_names[raw_name] = count
            base_name = raw_name if count == 1 else f"{raw_name}_{count}"

            column_names = [base_name]
            columns.append(DatasetColumnRead(name=base_name, label=question.label, question_id=question.id, kind=mode))

            if mode == "mixed":
                if question.question_type in {"single_choice", "dropdown", "likert", "boolean", "multiple_choice"}:
                    value_name = f"{base_name}__value"
                    column_names.append(value_name)
                    columns.append(DatasetColumnRead(name=value_name, label=f"{question.label} value", question_id=question.id, kind="value"))
                if (
                    question.question_type in {"single_choice", "dropdown", "likert", "boolean", "multiple_choice"}
                    and any(option.score is not None for option in question.options if option.deleted_at is None)
                ) or (question.question_type == "number" and question.is_scored):
                    score_name = f"{base_name}__score"
                    column_names.append(score_name)
                    columns.append(DatasetColumnRead(name=score_name, label=f"{question.label} score", question_id=question.id, kind="score"))
                if question.question_type == "multiple_choice":
                    json_name = f"{base_name}__json"
                    column_names.append(json_name)
                    columns.append(DatasetColumnRead(name=json_name, label=f"{question.label} json", question_id=question.id, kind="json"))

            if expand_multiple_choice and question.question_type == "multiple_choice":
                active_options = sorted(
                    (option for option in question.options if option.deleted_at is None),
                    key=lambda item: (item.sort_order, item.created_at),
                )
                option_used_names: dict[str, int] = {}
                for option in active_options:
                    option_suffix_raw = sanitize_column_name(option.value or option.label) or sanitize_column_name(option.id)[:6]
                    option_count = option_used_names.get(option_suffix_raw, 0) + 1
                    option_used_names[option_suffix_raw] = option_count
                    option_suffix = option_suffix_raw if option_count == 1 else f"{option_suffix_raw}_{option_count}"
                    option_column = f"{base_name}__{option_suffix}"
                    column_names.append(option_column)
                    columns.append(
                        DatasetColumnRead(
                            name=option_column,
                            label=f"{question.label} {option.label}",
                            question_id=question.id,
                            kind="expanded_option",
                        )
                    )

            mapping[question.id] = QuestionColumnConfig(
                question_id=question.id,
                base_name=base_name,
                label=question.label,
                column_names=column_names,
                question_type=question.question_type,
            )

        return columns, mapping

    def _answer_payload_for_dataset(
        self,
        question: FormQuestion,
        answer: FormAnswer | None,
    ) -> dict[str, Any]:
        if answer is None:
            return {"label": None, "value": None, "score": None, "json": None, "selected_option_ids": []}

        option_map = {option.id: option for option in question.options if option.deleted_at is None}

        if question.question_type in {"single_choice", "dropdown", "likert", "boolean"}:
            option = answer.option or (option_map.get(answer.option_id) if answer.option_id else None)
            return {
                "label": option.label if option else answer.value_text,
                "value": option.value if option else answer.value_text,
                "score": answer.score_value,
                "json": None,
                "selected_option_ids": [option.id] if option else [],
            }

        if question.question_type == "multiple_choice":
            raw_values = answer.value_json if isinstance(answer.value_json, list) else []
            selected_options: list[FormQuestionOption] = []
            resolved_ids: list[str] = []
            for raw_value in raw_values:
                if isinstance(raw_value, str) and raw_value in option_map:
                    selected_options.append(option_map[raw_value])
                    resolved_ids.append(raw_value)
                elif isinstance(raw_value, str):
                    matched = next((option for option in option_map.values() if option.value == raw_value), None)
                    if matched is not None:
                        selected_options.append(matched)
                        resolved_ids.append(matched.id)
            labels = "; ".join(option.label for option in selected_options) or None
            values = "; ".join(option.value for option in selected_options) or None
            score = answer.score_value if answer.score_value is not None else calculate_multiple_choice_score(question, selected_options)
            json_value = [
                {"id": option.id, "label": option.label, "value": option.value, "score": option.score}
                for option in selected_options
            ] or None
            return {
                "label": labels,
                "value": values,
                "score": score,
                "json": json_value,
                "selected_option_ids": resolved_ids,
            }

        if question.question_type == "number":
            return {
                "label": answer.value_number,
                "value": answer.value_number,
                "score": answer.score_value,
                "json": None,
                "selected_option_ids": [],
            }

        if question.question_type in {"text_short", "text_long"}:
            return {
                "label": answer.value_text,
                "value": answer.value_text,
                "score": None,
                "json": None,
                "selected_option_ids": [],
            }

        if question.question_type == "date":
            date_value = self._serialize_datetime(answer.value_date)
            return {
                "label": date_value,
                "value": date_value,
                "score": None,
                "json": None,
                "selected_option_ids": [],
            }

        return {"label": None, "value": None, "score": None, "json": None, "selected_option_ids": []}

    def _row_to_exportable(self, row: dict[str, Any]) -> dict[str, Any]:
        exportable: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, (dict, list)):
                exportable[key] = json.dumps(value, ensure_ascii=False)
            else:
                exportable[key] = value
        return exportable

    def build_form_dataset(
        self,
        form_id: str,
        *,
        mode: str = "mixed",
        include_metadata: bool = True,
        include_discarded: bool = False,
        expand_multiple_choice: bool = False,
        include_scores: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> DatasetRead:
        form = self._get_form(form_id)
        columns, mapping = self.resolve_question_column_map(
            form,
            mode=mode,
            expand_multiple_choice=expand_multiple_choice,
            include_metadata=include_metadata,
        )
        responses = self._get_form_responses(form, include_discarded=include_discarded)
        total_rows = len(responses)
        paged_responses = responses[offset : offset + limit]

        rows: list[dict[str, Any]] = []
        for response in paged_responses:
            row: dict[str, Any] = {}
            if include_metadata:
                row.update(
                    {
                        "response_id": response.id,
                        "project_id": response.project_id,
                        "form_id": response.form_id,
                        "respondent_code": response.respondent_code,
                        "response_status": response.status,
                        "source": response.source,
                        "submitted_at": self._serialize_datetime(response.submitted_at),
                        "created_at": self._serialize_datetime(response.created_at),
                    }
                )

            answer_map = {answer.question_id: answer for answer in response.answers}
            active_questions = sorted(
                (question for question in form.questions if question.deleted_at is None),
                key=lambda item: (item.sort_order, item.created_at),
            )

            for question in active_questions:
                config = mapping[question.id]
                payload = self._answer_payload_for_dataset(question, answer_map.get(question.id))

                if mode == "label":
                    row[config.base_name] = payload["label"]
                elif mode == "value":
                    row[config.base_name] = payload["value"]
                elif mode == "score":
                    row[config.base_name] = payload["score"]
                else:
                    row[config.base_name] = payload["label"]
                    if question.question_type in {"single_choice", "dropdown", "likert", "boolean", "multiple_choice"}:
                        row[f"{config.base_name}__value"] = payload["value"]
                    if f"{config.base_name}__score" in config.column_names:
                        row[f"{config.base_name}__score"] = payload["score"]
                    if question.question_type == "multiple_choice":
                        row[f"{config.base_name}__json"] = payload["json"]

                if expand_multiple_choice and question.question_type == "multiple_choice":
                    option_columns = {
                        column.name: column
                        for column in columns
                        if column.question_id == question.id and column.kind == "expanded_option"
                    }
                    selected_option_ids = set(payload["selected_option_ids"])
                    for option in sorted(
                        (current for current in question.options if current.deleted_at is None),
                        key=lambda item: (item.sort_order, item.created_at),
                    ):
                        suffix = sanitize_column_name(option.value or option.label) or sanitize_column_name(option.id)[:6]
                        matching_columns = [name for name in option_columns if name.startswith(f"{config.base_name}__{suffix}")]
                        for column_name in matching_columns:
                            row[column_name] = 1 if option.id in selected_option_ids else 0

            rows.append(row)

        dataset = DatasetRead(
            form_id=form.id,
            mode=mode,
            total_rows=total_rows,
            total_columns=len(columns),
            columns=columns,
            rows=rows,
        )
        if include_scores:
            from app.services.advanced_scoring_service import AdvancedScoringService

            dataset = AdvancedScoringService(self.db).integrate_scores_into_dataset(dataset)
        return dataset

    def build_data_dictionary(self, form_id: str) -> DataDictionaryRead:
        form = self._get_form(form_id)
        _, mapping = self.resolve_question_column_map(
            form,
            mode="mixed",
            expand_multiple_choice=False,
            include_metadata=True,
        )
        items: list[DataDictionaryItemRead] = []
        for question in sorted(
            (question for question in form.questions if question.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        ):
            config = mapping[question.id]
            items.append(
                DataDictionaryItemRead(
                    question_id=question.id,
                    column_name=config.base_name,
                    code=question.code,
                    label=question.label,
                    question_type=question.question_type,
                    question_role=question.question_role,
                    measurement_level=question.measurement_level,
                    data_type=question.data_type,
                    is_required=question.is_required,
                    is_scored=question.is_scored,
                    is_reverse_scored=question.is_reverse_scored,
                    section_title=question.section.title if question.section is not None else None,
                    instrument_name=question.instrument.name if question.instrument is not None else None,
                    dimension_name=question.dimension.name if question.dimension is not None else None,
                    project_variable_name=question.project_variable.name if question.project_variable is not None else None,
                    options=[
                        {
                            "id": option.id,
                            "label": option.label,
                            "value": option.value,
                            "score": option.score,
                            "sort_order": option.sort_order,
                        }
                        for option in sorted(
                            (option for option in question.options if option.deleted_at is None),
                            key=lambda item: (item.sort_order, item.created_at),
                        )
                    ],
                )
            )
        return DataDictionaryRead(form_id=form.id, items=items)

    def _is_answered(self, question: FormQuestion, answer: FormAnswer | None) -> bool:
        if answer is None:
            return False
        if question.question_type in {"single_choice", "dropdown", "likert", "boolean"}:
            return answer.option_id is not None
        if question.question_type == "multiple_choice":
            return isinstance(answer.value_json, list) and len(answer.value_json) > 0
        if question.question_type == "number":
            return answer.value_number is not None
        if question.question_type in {"text_short", "text_long"}:
            return bool(answer.value_text)
        if question.question_type == "date":
            return answer.value_date is not None
        return False

    def build_completeness_summary(self, form_id: str) -> CompletenessSummaryRead:
        form = self._get_form(form_id)
        responses = self._get_form_responses(form, include_discarded=False)
        _, mapping = self.resolve_question_column_map(
            form,
            mode="mixed",
            expand_multiple_choice=False,
            include_metadata=True,
        )
        items: list[CompletenessItemRead] = []
        total_responses = len(responses)
        active_questions = sorted(
            (question for question in form.questions if question.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )
        for question in active_questions:
            answered_count = 0
            for response in responses:
                answer = next((answer for answer in response.answers if answer.question_id == question.id), None)
                if self._is_answered(question, answer):
                    answered_count += 1
            missing_count = total_responses - answered_count
            missing_percent = float((missing_count / total_responses) * 100) if total_responses else 0.0
            if missing_percent < 5:
                warning_level = "ok"
            elif missing_percent < 20:
                warning_level = "warning"
            else:
                warning_level = "critical"
            items.append(
                CompletenessItemRead(
                    question_id=question.id,
                    column_name=mapping[question.id].base_name,
                    label=question.label,
                    total_responses=total_responses,
                    answered_count=answered_count,
                    missing_count=missing_count,
                    missing_percent=round(missing_percent, 2),
                    required=question.is_required,
                    warning_level=warning_level,
                )
            )
        return CompletenessSummaryRead(form_id=form.id, total_responses=total_responses, items=items)

    def get_response_table(self, form_id: str, *, include_discarded: bool = False) -> list[FormResponse]:
        form = self._get_form(form_id)
        return self._get_form_responses(form, include_discarded=include_discarded)

    def validate_answer_update(self, answer: FormAnswer, payload: AnswerUpdateRequest) -> dict[str, Any]:
        question = answer.question
        if question.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit an answer for a deleted question")

        option_id = None
        value_text = None
        value_number = None
        value_date = None
        value_json = None
        score_value = None

        if question.question_type in {"single_choice", "dropdown", "likert", "boolean"}:
            if payload.option_id is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="option_id is required for this question type")
            option = self._get_option_for_question(question, payload.option_id)
            option_id = option.id
            score_value = calculate_option_score(question, option)
        elif question.question_type == "multiple_choice":
            if not isinstance(payload.value_json, list) or not payload.value_json:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="value_json must be a non-empty list")
            selected_options: list[FormQuestionOption] = []
            resolved_ids: list[str] = []
            for raw_value in payload.value_json:
                if not isinstance(raw_value, str):
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="value_json must contain option ids or values")
                matched_option = next(
                    (
                        option
                        for option in question.options
                        if option.deleted_at is None and (option.id == raw_value or option.value == raw_value)
                    ),
                    None,
                )
                if matched_option is None:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid option for multiple choice question")
                selected_options.append(matched_option)
                resolved_ids.append(matched_option.id)
            value_json = resolved_ids
            score_value = calculate_multiple_choice_score(question, selected_options)
        elif question.question_type == "number":
            if payload.value_number is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="value_number is required for this question type")
            if question.min_value is not None and payload.value_number < question.min_value:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="value_number is below min_value")
            if question.max_value is not None and payload.value_number > question.max_value:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="value_number is above max_value")
            value_number = payload.value_number
            if question.is_scored:
                score_value = value_number
        elif question.question_type in {"text_short", "text_long"}:
            value_text = payload.value_text
        elif question.question_type == "date":
            if payload.value_date is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="value_date is required for this question type")
            value_date = payload.value_date
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported question type for editing")

        return {
            "option_id": option_id,
            "value_text": value_text,
            "value_number": value_number,
            "value_date": value_date,
            "value_json": value_json,
            "score_value": score_value,
        }

    def update_answer_value(self, answer_id: str, payload: AnswerUpdateRequest) -> FormAnswer:
        answer = self._get_answer(answer_id)
        update_values = self.validate_answer_update(answer, payload)
        for field, value in update_values.items():
            setattr(answer, field, value)
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def update_response_status(self, response_id: str, status_value: str) -> ResponseStatusRead:
        if status_value not in ALLOWED_RESPONSE_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid response status")
        response = self._get_response(response_id)
        response.status = status_value
        self.db.commit()
        self.db.refresh(response)
        return ResponseStatusRead(response_id=response.id, status=response.status, updated_at=response.updated_at)

    def restore_response(self, response_id: str) -> ResponseStatusRead:
        response = self._get_response(response_id)
        response.status = "complete"
        self.db.commit()
        self.db.refresh(response)
        return ResponseStatusRead(response_id=response.id, status=response.status, updated_at=response.updated_at)

    def _dataset_to_exportable_dataframe(self, dataset: DatasetRead) -> pd.DataFrame:
        rows = [self._row_to_exportable(row) for row in dataset.rows]
        column_names = [column.name for column in dataset.columns]
        return pd.DataFrame(rows, columns=column_names)

    def _dataset_to_raw_dataframe(self, dataset: DatasetRead) -> pd.DataFrame:
        column_names = [column.name for column in dataset.columns]
        return pd.DataFrame(dataset.rows, columns=column_names)

    def build_dataset_dataframe(
        self,
        form_id: str,
        *,
        mode: str = "mixed",
        include_metadata: bool = True,
        include_discarded: bool = False,
        expand_multiple_choice: bool = False,
        include_scores: bool = False,
    ) -> tuple[Form, DatasetRead, pd.DataFrame, dict[str, QuestionColumnConfig]]:
        form = self._get_form(form_id)
        dataset = self._build_full_dataset(
            form_id,
            mode=mode,
            include_metadata=include_metadata,
            include_discarded=include_discarded,
            expand_multiple_choice=expand_multiple_choice,
            include_scores=include_scores,
        )
        _, mapping = self.resolve_question_column_map(
            form,
            mode=mode,
            expand_multiple_choice=expand_multiple_choice,
            include_metadata=include_metadata,
        )
        dataframe = self._dataset_to_raw_dataframe(dataset)
        return form, dataset, dataframe, mapping

    def _build_full_dataset(
        self,
        form_id: str,
        *,
        mode: str,
        include_metadata: bool,
        include_discarded: bool,
        expand_multiple_choice: bool,
        include_scores: bool = False,
    ) -> DatasetRead:
        form = self._get_form(form_id)
        total_rows = len(self._get_form_responses(form, include_discarded=include_discarded))
        limit = max(total_rows, 1)
        return self.build_form_dataset(
            form_id,
            mode=mode,
            include_metadata=include_metadata,
            include_discarded=include_discarded,
            expand_multiple_choice=expand_multiple_choice,
            include_scores=include_scores,
            limit=limit,
            offset=0,
        )

    def _build_export_artifact(
        self,
        *,
        form: Form,
        artifact_type: str,
        file_name: str,
        file_path: Path,
        mime_type: str,
        metadata_json: dict[str, Any],
    ) -> ExportArtifact:
        relative_path = file_path.relative_to(self.settings.backend_dir).as_posix()
        artifact = ExportArtifact(
            project_id=form.project_id,
            form_id=form.id,
            artifact_type=artifact_type,
            file_name=file_name,
            file_path=relative_path,
            mime_type=mime_type,
            file_size_bytes=file_path.stat().st_size,
            metadata_json=metadata_json,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def export_form_dataset_excel(
        self,
        form_id: str,
        *,
        mode: str,
        include_metadata: bool,
        include_discarded: bool,
        expand_multiple_choice: bool,
        include_scores: bool = False,
    ) -> ExportArtifact:
        form = self._get_form(form_id)
        dataset = self._build_full_dataset(
            form_id,
            mode=mode,
            include_metadata=include_metadata,
            include_discarded=include_discarded,
            expand_multiple_choice=expand_multiple_choice,
            include_scores=include_scores,
        )
        dictionary = self.build_data_dictionary(form_id)
        completeness = self.build_completeness_summary(form_id)

        timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
        file_name = f"form_{form.id}_dataset_{timestamp}.xlsx"
        file_path = self.exports_dir / file_name

        dataset_df = self._dataset_to_exportable_dataframe(dataset)
        dictionary_df = pd.DataFrame([item.model_dump() for item in dictionary.items])
        completeness_df = pd.DataFrame([item.model_dump() for item in completeness.items])

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            dataset_df.to_excel(writer, sheet_name="Dataset", index=False)
            dictionary_df.to_excel(writer, sheet_name="DataDictionary", index=False)
            completeness_df.to_excel(writer, sheet_name="Completeness", index=False)

            for sheet_name, dataframe in {
                "Dataset": dataset_df,
                "DataDictionary": dictionary_df,
                "Completeness": completeness_df,
            }.items():
                worksheet = writer.book[sheet_name]
                worksheet.freeze_panes = "A2"
                if dataframe.columns.size > 0:
                    worksheet.auto_filter.ref = worksheet.dimensions
                for column_cells in worksheet.columns:
                    max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 50)

        return self._build_export_artifact(
            form=form,
            artifact_type="dataset_excel",
            file_name=file_name,
            file_path=file_path,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            metadata_json={
                "mode": mode,
                "include_metadata": include_metadata,
                "include_discarded": include_discarded,
                "expand_multiple_choice": expand_multiple_choice,
                "include_scores": include_scores,
            },
        )

    def export_form_dataset_csv(
        self,
        form_id: str,
        *,
        mode: str,
        include_metadata: bool,
        include_discarded: bool,
        expand_multiple_choice: bool,
        include_scores: bool = False,
    ) -> ExportArtifact:
        form = self._get_form(form_id)
        dataset = self._build_full_dataset(
            form_id,
            mode=mode,
            include_metadata=include_metadata,
            include_discarded=include_discarded,
            expand_multiple_choice=expand_multiple_choice,
            include_scores=include_scores,
        )
        timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
        file_name = f"form_{form.id}_dataset_{timestamp}.csv"
        file_path = self.exports_dir / file_name
        self._dataset_to_exportable_dataframe(dataset).to_csv(file_path, index=False, encoding="utf-8-sig")

        return self._build_export_artifact(
            form=form,
            artifact_type="dataset_csv",
            file_name=file_name,
            file_path=file_path,
            mime_type="text/csv",
            metadata_json={
                "mode": mode,
                "include_metadata": include_metadata,
                "include_discarded": include_discarded,
                "expand_multiple_choice": expand_multiple_choice,
                "include_scores": include_scores,
            },
        )

    def list_form_exports(self, form_id: str) -> tuple[list[ExportArtifact], int]:
        self._get_form(form_id)
        filters = [ExportArtifact.form_id == form_id]
        items = list(
            self.db.scalars(
                select(ExportArtifact).where(*filters).order_by(ExportArtifact.created_at.desc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(ExportArtifact).where(*filters)) or 0)
        return items, total
