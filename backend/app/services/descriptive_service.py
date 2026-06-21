from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.form import Form
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.project_variable import ProjectVariable
from app.schemas.descriptive import (
    AnalysisRunRead,
    CrosstabRead,
    DescriptiveOverviewRead,
    DescriptiveRunRead,
    DescriptiveRunRequest,
    DimensionDescriptiveRead,
    FormDescriptiveReportRead,
    InstrumentDescriptiveRead,
    NumericDescriptiveRead,
    ProjectVariableDescriptiveRead,
    QuestionDescriptiveRead,
)
from app.services.dataset_service import DatasetService, QuestionColumnConfig
from app.statistics.crosstab_engine import build_crosstab
from app.statistics.descriptive_engine import numeric_descriptive
from app.statistics.frequency_engine import frequency_table, multiple_choice_frequency
from app.statistics.score_engine import (
    compute_dimension_scores,
    compute_group_score,
    compute_instrument_scores,
)


CATEGORICAL_QUESTION_TYPES = {"single_choice", "dropdown", "likert", "boolean", "multiple_choice"}
TEXT_CATEGORICAL_TYPES = {"text_short"}
NUMERIC_QUESTION_TYPES = {"number"}


class DescriptiveService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)

    def _get_form_context(
        self,
        form_id: str,
        *,
        include_discarded: bool,
    ) -> tuple[Form, pd.DataFrame, dict[str, QuestionColumnConfig]]:
        form, _, dataframe, mapping = self.dataset_service.build_dataset_dataframe(
            form_id,
            mode="mixed",
            include_metadata=True,
            include_discarded=include_discarded,
            expand_multiple_choice=False,
        )
        return form, dataframe, mapping

    def _active_questions(self, form: Form) -> list[FormQuestion]:
        return sorted(
            (question for question in form.questions if question.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )

    def _active_instruments(self, form: Form) -> list[FormInstrument]:
        return sorted(
            (instrument for instrument in form.instruments if instrument.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )

    def _active_dimensions(self, instrument: FormInstrument) -> list[FormDimension]:
        return sorted(
            (dimension for dimension in instrument.dimensions if dimension.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )

    def _active_project_variables(self, form: Form) -> list[ProjectVariable]:
        return sorted(
            (variable for variable in form.project.variables if variable.deleted_at is None),
            key=lambda item: (item.name.lower(), item.created_at),
        )

    def _get_question_or_404(self, form: Form, question_id: str) -> FormQuestion:
        question = next((item for item in self._active_questions(form) if item.id == question_id), None)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found for form")
        return question

    def _ordered_pairs(self, question: FormQuestion) -> list[tuple[str, str | None]] | None:
        if question.question_type not in CATEGORICAL_QUESTION_TYPES:
            return None
        options = sorted(
            (option for option in question.options if option.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )
        if not options:
            return None
        return [(option.value, option.label) for option in options]

    def _is_categorical_question(self, question: FormQuestion) -> bool:
        return question.question_type in CATEGORICAL_QUESTION_TYPES or question.question_type in TEXT_CATEGORICAL_TYPES

    def _is_numeric_question(self, question: FormQuestion) -> bool:
        return question.question_type in NUMERIC_QUESTION_TYPES or question.is_scored

    def _get_base_column(self, question: FormQuestion, mapping: dict[str, QuestionColumnConfig]) -> str:
        return mapping[question.id].base_name

    def _get_value_column(self, question: FormQuestion, mapping: dict[str, QuestionColumnConfig], dataframe: pd.DataFrame) -> str:
        base_name = self._get_base_column(question, mapping)
        value_column = f"{base_name}__value"
        return value_column if value_column in dataframe.columns else base_name

    def _get_score_column(self, question: FormQuestion, mapping: dict[str, QuestionColumnConfig], dataframe: pd.DataFrame) -> str | None:
        base_name = self._get_base_column(question, mapping)
        score_column = f"{base_name}__score"
        if score_column in dataframe.columns:
            return score_column
        if question.question_type == "number" and base_name in dataframe.columns:
            return base_name
        return None

    def _round(self, value: float | None, decimals: int) -> float | None:
        if value is None:
            return None
        return round(float(value), decimals)

    def build_numeric_descriptive(self, series: pd.Series, decimals: int = 3) -> NumericDescriptiveRead:
        return numeric_descriptive(series, decimals=decimals)

    def build_frequency_table(
        self,
        question: FormQuestion,
        dataframe: pd.DataFrame,
        mapping: dict[str, QuestionColumnConfig],
        *,
        decimals: int,
    ) -> tuple[list[Any], int]:
        total_n = len(dataframe)
        base_name = self._get_base_column(question, mapping)
        if question.question_type == "multiple_choice":
            json_column = f"{base_name}__json"
            json_series = dataframe[json_column] if json_column in dataframe.columns else pd.Series(dtype="object")
            return multiple_choice_frequency(
                json_series,
                total_n,
                ordered_pairs=self._ordered_pairs(question),
                decimals=decimals,
            )

        label_series = dataframe[base_name] if base_name in dataframe.columns else pd.Series(dtype="object")
        value_series = dataframe[self._get_value_column(question, mapping, dataframe)]
        return frequency_table(
            value_series,
            total_n,
            labels=label_series,
            ordered_pairs=self._ordered_pairs(question),
            decimals=decimals,
        )

    def build_descriptive_warnings(
        self,
        *,
        total_n: int,
        valid_n: int,
        missing_n: int,
        numeric_series: pd.Series | None = None,
        frequencies_present: bool = False,
        numeric_present: bool = False,
        discarded_responses_excluded: bool = False,
        scored_item_count: int | None = None,
    ) -> list[str]:
        warnings: list[str] = []
        if total_n == 0:
            warnings.append("no_responses")
        if discarded_responses_excluded:
            warnings.append("discarded_responses_excluded")
        if valid_n == 0:
            warnings.append("all_values_missing")
        if total_n > 0 and (missing_n / total_n) * 100 >= 20:
            warnings.append("high_missingness")
        if 0 < valid_n < 3:
            warnings.append("low_valid_n")
        if not frequencies_present:
            warnings.append("no_categorical_data")
        if not numeric_present:
            warnings.append("no_numeric_data")
        if scored_item_count == 0:
            warnings.append("no_scored_items")
        if numeric_series is not None:
            cleaned = pd.to_numeric(numeric_series, errors="coerce").dropna()
            if not cleaned.empty and cleaned.nunique(dropna=True) <= 1:
                warnings.append("constant_values")
        return list(dict.fromkeys(warnings))

    def _build_question_descriptive(
        self,
        question: FormQuestion,
        dataframe: pd.DataFrame,
        mapping: dict[str, QuestionColumnConfig],
        *,
        decimals: int,
        discarded_responses_excluded: bool,
    ) -> QuestionDescriptiveRead:
        frequencies = []
        valid_n = 0
        missing_n = len(dataframe)
        numeric = None
        numeric_series: pd.Series | None = None

        if self._is_categorical_question(question):
            frequencies, valid_n = self.build_frequency_table(question, dataframe, mapping, decimals=decimals)
            missing_n = len(dataframe) - valid_n

        if self._is_numeric_question(question):
            score_column = self._get_score_column(question, mapping, dataframe)
            if score_column is not None and score_column in dataframe.columns:
                numeric_series = pd.to_numeric(dataframe[score_column], errors="coerce")
                numeric = self.build_numeric_descriptive(numeric_series, decimals=decimals)
                valid_n = max(valid_n, numeric.valid_n)
                missing_n = min(missing_n, numeric.missing_n) if self._is_categorical_question(question) else numeric.missing_n

        warnings = self.build_descriptive_warnings(
            total_n=len(dataframe),
            valid_n=valid_n,
            missing_n=missing_n,
            numeric_series=numeric_series,
            frequencies_present=bool(frequencies),
            numeric_present=numeric is not None and numeric.valid_n > 0,
            discarded_responses_excluded=discarded_responses_excluded,
            scored_item_count=1 if question.is_scored else None,
        )
        if not question.is_scored and "no_scored_items" in warnings:
            warnings.remove("no_scored_items")

        return QuestionDescriptiveRead(
            question_id=question.id,
            code=question.code,
            label=question.label,
            question_type=question.question_type,
            question_role=question.question_role,
            measurement_level=question.measurement_level,
            data_type=question.data_type,
            is_scored=question.is_scored,
            valid_n=valid_n,
            missing_n=missing_n,
            frequencies=frequencies,
            numeric=numeric,
            warnings=warnings,
        )

    def _build_question_descriptives(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict[str, QuestionColumnConfig],
        *,
        decimals: int,
        discarded_responses_excluded: bool,
    ) -> list[QuestionDescriptiveRead]:
        return [
            self._build_question_descriptive(
                question,
                dataframe,
                mapping,
                decimals=decimals,
                discarded_responses_excluded=discarded_responses_excluded,
            )
            for question in self._active_questions(form)
        ]

    def _build_group_numeric(
        self,
        dataframe: pd.DataFrame,
        questions: list[FormQuestion],
        mapping: dict[str, QuestionColumnConfig],
        *,
        aggregation: str,
        decimals: int,
    ) -> tuple[NumericDescriptiveRead | None, int]:
        score_columns = [
            column_name
            for question in questions
            if (column_name := self._get_score_column(question, mapping, dataframe)) is not None
        ]
        scored_item_count = len(score_columns)
        if not score_columns:
            return None, 0
        score_frame = compute_group_score(dataframe, score_columns, aggregation=aggregation)
        return self.build_numeric_descriptive(score_frame["score"], decimals=decimals), scored_item_count

    def build_dimension_scores(
        self,
        form_id: str,
        *,
        include_discarded: bool,
        decimals: int,
        score_aggregation: str,
    ) -> list[DimensionDescriptiveRead]:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and any(
            response.deleted_at is None and response.status == "discarded" for response in form.responses
        )
        dimension_question_columns: dict[str, list[str]] = {}
        dimension_meta: dict[str, tuple[FormDimension, list[FormQuestion]]] = {}
        for instrument in self._active_instruments(form):
            for dimension in self._active_dimensions(instrument):
                questions = [
                    question
                    for question in self._active_questions(form)
                    if question.dimension_id == dimension.id and question.is_scored
                ]
                columns = [
                    column_name
                    for question in questions
                    if (column_name := self._get_score_column(question, mapping, dataframe)) is not None
                ]
                dimension_question_columns[dimension.id] = columns
                dimension_meta[dimension.id] = (dimension, questions)

        score_tables = compute_dimension_scores(
            dataframe,
            dimension_question_columns,
            aggregation=score_aggregation,
        )

        results: list[DimensionDescriptiveRead] = []
        for dimension_id, (dimension, questions) in dimension_meta.items():
            scored_item_count = len(dimension_question_columns[dimension_id])
            score_frame = score_tables[dimension_id]
            numeric = self.build_numeric_descriptive(score_frame["score"], decimals=decimals) if scored_item_count else None
            warnings = self.build_descriptive_warnings(
                total_n=len(dataframe),
                valid_n=numeric.valid_n if numeric else 0,
                missing_n=numeric.missing_n if numeric else len(dataframe),
                numeric_series=score_frame["score"] if scored_item_count else None,
                frequencies_present=False,
                numeric_present=numeric is not None and numeric.valid_n > 0,
                discarded_responses_excluded=discarded_excluded,
                scored_item_count=scored_item_count,
            )
            results.append(
                DimensionDescriptiveRead(
                    dimension_id=dimension.id,
                    instrument_id=dimension.instrument_id,
                    name=dimension.name,
                    item_count=len(questions),
                    scored_item_count=scored_item_count,
                    aggregation=score_aggregation,
                    numeric=numeric,
                    warnings=warnings,
                )
            )
        return results

    def build_instrument_scores(
        self,
        form_id: str,
        *,
        include_discarded: bool,
        decimals: int,
        score_aggregation: str,
    ) -> list[InstrumentDescriptiveRead]:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        dimension_items = self.build_dimension_scores(
            form_id,
            include_discarded=include_discarded,
            decimals=decimals,
            score_aggregation=score_aggregation,
        )
        dimension_map: dict[str, list[DimensionDescriptiveRead]] = {}
        for item in dimension_items:
            dimension_map.setdefault(item.instrument_id, []).append(item)

        discarded_excluded = not include_discarded and any(
            response.deleted_at is None and response.status == "discarded" for response in form.responses
        )
        instrument_question_columns: dict[str, list[str]] = {}
        instrument_meta: dict[str, tuple[FormInstrument, list[FormQuestion]]] = {}
        for instrument in self._active_instruments(form):
            questions = [
                question
                for question in self._active_questions(form)
                if question.instrument_id == instrument.id and question.is_scored
            ]
            columns = [
                column_name
                for question in questions
                if (column_name := self._get_score_column(question, mapping, dataframe)) is not None
            ]
            instrument_question_columns[instrument.id] = columns
            instrument_meta[instrument.id] = (instrument, questions)

        score_tables = compute_instrument_scores(
            dataframe,
            instrument_question_columns,
            aggregation=score_aggregation,
        )

        results: list[InstrumentDescriptiveRead] = []
        for instrument_id, (instrument, questions) in instrument_meta.items():
            scored_item_count = len(instrument_question_columns[instrument_id])
            score_frame = score_tables[instrument_id]
            numeric = self.build_numeric_descriptive(score_frame["score"], decimals=decimals) if scored_item_count else None
            warnings = self.build_descriptive_warnings(
                total_n=len(dataframe),
                valid_n=numeric.valid_n if numeric else 0,
                missing_n=numeric.missing_n if numeric else len(dataframe),
                numeric_series=score_frame["score"] if scored_item_count else None,
                frequencies_present=False,
                numeric_present=numeric is not None and numeric.valid_n > 0,
                discarded_responses_excluded=discarded_excluded,
                scored_item_count=scored_item_count,
            )
            results.append(
                InstrumentDescriptiveRead(
                    instrument_id=instrument.id,
                    name=instrument.name,
                    acronym=instrument.acronym,
                    item_count=len(questions),
                    scored_item_count=scored_item_count,
                    aggregation=score_aggregation,
                    dimensions=dimension_map.get(instrument.id, []),
                    numeric=numeric,
                    warnings=warnings,
                )
            )
        return results

    def get_project_variable_descriptives(
        self,
        form_id: str,
        *,
        include_discarded: bool = False,
        decimals: int = 3,
    ) -> list[ProjectVariableDescriptiveRead]:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and any(
            response.deleted_at is None and response.status == "discarded" for response in form.responses
        )
        question_descriptives = {
            item.question_id: item
            for item in self._build_question_descriptives(
                form,
                dataframe,
                mapping,
                decimals=decimals,
                discarded_responses_excluded=discarded_excluded,
            )
        }

        results: list[ProjectVariableDescriptiveRead] = []
        for variable in self._active_project_variables(form):
            questions = [
                question
                for question in self._active_questions(form)
                if question.project_variable_id == variable.id
            ]
            scored_questions = [question for question in questions if question.is_scored]
            numeric, scored_item_count = self._build_group_numeric(
                dataframe,
                scored_questions,
                mapping,
                aggregation="mean",
                decimals=decimals,
            )

            categorical_questions = [question for question in questions if self._is_categorical_question(question)]
            frequencies = []
            if len(categorical_questions) == 1:
                frequencies, _ = self.build_frequency_table(
                    categorical_questions[0],
                    dataframe,
                    mapping,
                    decimals=decimals,
                )

            warnings = self.build_descriptive_warnings(
                total_n=len(dataframe),
                valid_n=numeric.valid_n if numeric else (questions and max(question_descriptives[q.id].valid_n for q in questions) or 0),
                missing_n=numeric.missing_n if numeric else (questions and min(question_descriptives[q.id].missing_n for q in questions) or len(dataframe)),
                numeric_series=None,
                frequencies_present=bool(frequencies),
                numeric_present=numeric is not None and numeric.valid_n > 0,
                discarded_responses_excluded=discarded_excluded,
                scored_item_count=scored_item_count,
            )
            results.append(
                ProjectVariableDescriptiveRead(
                    variable_id=variable.id,
                    name=variable.name,
                    variable_role=variable.variable_role,
                    measurement_level=variable.measurement_level,
                    data_type=variable.data_type,
                    question_count=len(questions),
                    scored_question_count=len(scored_questions),
                    questions=[question_descriptives[question.id] for question in questions],
                    numeric=numeric,
                    frequencies=frequencies,
                    warnings=warnings,
                )
            )
        return results

    def get_descriptive_overview(
        self,
        form_id: str,
        *,
        include_discarded: bool = False,
    ) -> DescriptiveOverviewRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        active_questions = self._active_questions(form)
        total_responses = len([response for response in form.responses if response.deleted_at is None])
        discarded_responses = len(
            [response for response in form.responses if response.deleted_at is None and response.status == "discarded"]
        )
        included_responses = len(dataframe)

        missing_counts = 0
        for question in active_questions:
            base_name = self._get_base_column(question, mapping)
            if question.question_type == "multiple_choice":
                column_name = f"{base_name}__json"
                series = dataframe[column_name] if column_name in dataframe.columns else pd.Series(dtype="object")
                missing_counts += int(series.apply(lambda value: not isinstance(value, list) or len(value) == 0).sum())
            else:
                column_name = self._get_score_column(question, mapping, dataframe) if self._is_numeric_question(question) else None
                if column_name and column_name in dataframe.columns:
                    series = pd.to_numeric(dataframe[column_name], errors="coerce")
                    missing_counts += int(series.isna().sum())
                else:
                    value_column = self._get_value_column(question, mapping, dataframe)
                    series = dataframe[value_column] if value_column in dataframe.columns else pd.Series(dtype="object")
                    missing_counts += int(series.isna().sum())

        total_cells = included_responses * len(active_questions)
        missing_percent = self._round((missing_counts / total_cells) * 100 if total_cells else 0.0, 3)

        warnings: list[str] = []
        if included_responses == 0:
            warnings.append("no_responses")
        if not include_discarded and discarded_responses > 0:
            warnings.append("discarded_responses_excluded")
        if missing_percent is not None and missing_percent >= 20:
            warnings.append("high_missingness")

        return DescriptiveOverviewRead(
            form_id=form.id,
            project_id=form.project_id,
            total_responses=total_responses,
            included_responses=included_responses,
            discarded_responses=discarded_responses,
            total_questions=len(active_questions),
            scored_questions=sum(1 for question in active_questions if question.is_scored),
            categorical_questions=sum(1 for question in active_questions if self._is_categorical_question(question)),
            numeric_questions=sum(1 for question in active_questions if self._is_numeric_question(question)),
            missing_overview={
                "total_cells": total_cells,
                "missing_cells": missing_counts,
                "missing_percent": missing_percent,
            },
            warnings=list(dict.fromkeys(warnings)),
        )

    def get_question_descriptive(
        self,
        form_id: str,
        question_id: str,
        *,
        include_discarded: bool = False,
        decimals: int = 3,
    ) -> QuestionDescriptiveRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        question = self._get_question_or_404(form, question_id)
        discarded_excluded = not include_discarded and any(
            response.deleted_at is None and response.status == "discarded" for response in form.responses
        )
        return self._build_question_descriptive(
            question,
            dataframe,
            mapping,
            decimals=decimals,
            discarded_responses_excluded=discarded_excluded,
        )

    def get_dimension_descriptives(
        self,
        form_id: str,
        *,
        include_discarded: bool = False,
        decimals: int = 3,
        score_aggregation: str = "mean",
    ) -> list[DimensionDescriptiveRead]:
        return self.build_dimension_scores(
            form_id,
            include_discarded=include_discarded,
            decimals=decimals,
            score_aggregation=score_aggregation,
        )

    def get_instrument_descriptives(
        self,
        form_id: str,
        *,
        include_discarded: bool = False,
        decimals: int = 3,
        score_aggregation: str = "mean",
    ) -> list[InstrumentDescriptiveRead]:
        return self.build_instrument_scores(
            form_id,
            include_discarded=include_discarded,
            decimals=decimals,
            score_aggregation=score_aggregation,
        )

    def get_form_descriptives(
        self,
        form_id: str,
        *,
        include_discarded: bool = False,
        decimals: int = 3,
        score_aggregation: str = "mean",
    ) -> FormDescriptiveReportRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and any(
            response.deleted_at is None and response.status == "discarded" for response in form.responses
        )
        questions = self._build_question_descriptives(
            form,
            dataframe,
            mapping,
            decimals=decimals,
            discarded_responses_excluded=discarded_excluded,
        )
        dimensions = self.get_dimension_descriptives(
            form_id,
            include_discarded=include_discarded,
            decimals=decimals,
            score_aggregation=score_aggregation,
        )
        instruments = self.get_instrument_descriptives(
            form_id,
            include_discarded=include_discarded,
            decimals=decimals,
            score_aggregation=score_aggregation,
        )
        project_variables = self.get_project_variable_descriptives(
            form_id,
            include_discarded=include_discarded,
            decimals=decimals,
        )
        overview = self.get_descriptive_overview(form_id, include_discarded=include_discarded)
        return FormDescriptiveReportRead(
            form_id=form.id,
            project_id=form.project_id,
            mode="descriptive",
            decimals=decimals,
            overview=overview,
            questions=questions,
            dimensions=dimensions,
            instruments=instruments,
            project_variables=project_variables,
        )

    def get_crosstab(
        self,
        form_id: str,
        *,
        row_question_id: str,
        column_question_id: str,
        include_discarded: bool = False,
        decimals: int = 3,
    ) -> CrosstabRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        row_question = self._get_question_or_404(form, row_question_id)
        column_question = self._get_question_or_404(form, column_question_id)
        if not self._is_categorical_question(row_question) or not self._is_categorical_question(column_question):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Crosstab requires categorical or closed questions",
            )

        row_column = self._get_base_column(row_question, mapping)
        column_column = self._get_base_column(column_question, mapping)
        row_values, column_values, cells, total_n = build_crosstab(
            dataframe,
            row_column,
            column_column,
            decimals=decimals,
        )
        warnings = []
        if total_n == 0:
            warnings.append("no_responses")
        if 0 < total_n < 3:
            warnings.append("low_valid_n")
        if not include_discarded and any(
            response.deleted_at is None and response.status == "discarded" for response in form.responses
        ):
            warnings.append("discarded_responses_excluded")
        return CrosstabRead(
            form_id=form.id,
            row_question_id=row_question.id,
            column_question_id=column_question.id,
            row_question_label=row_question.label,
            column_question_label=column_question.label,
            total_n=total_n,
            rows=row_values,
            columns=column_values,
            cells=cells,
            warnings=list(dict.fromkeys(warnings)),
        )

    def run_descriptive_analysis(
        self,
        form_id: str,
        payload: DescriptiveRunRequest,
    ) -> DescriptiveRunRead:
        report = self.get_form_descriptives(
            form_id,
            include_discarded=payload.include_discarded,
            decimals=payload.decimals,
            score_aggregation=payload.score_aggregation,
        )
        analysis_run = None
        if payload.store_result:
            analysis_run = AnalysisRun(
                project_id=report.project_id,
                form_id=report.form_id,
                analysis_type="descriptive",
                status="completed",
                params_json=payload.model_dump(),
                result_json={
                    "overview": report.overview.model_dump(),
                    "question_count": len(report.questions),
                    "dimension_count": len(report.dimensions),
                    "instrument_count": len(report.instruments),
                    "project_variable_count": len(report.project_variables),
                },
            )
            self.db.add(analysis_run)
            self.db.commit()
            self.db.refresh(analysis_run)

        return DescriptiveRunRead(
            form_id=form_id,
            stored=analysis_run is not None,
            analysis_run=AnalysisRunRead.model_validate(analysis_run) if analysis_run is not None else None,
            report=report,
        )
