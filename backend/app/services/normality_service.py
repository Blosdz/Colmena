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
from app.schemas.normality import (
    NormalityDescriptiveContextRead,
    NormalityReportRead,
    NormalityRunRead,
    NormalityRunRequest,
    NormalityTestResultRead,
)
from app.services.dataset_service import DatasetService, QuestionColumnConfig
from app.statistics.normality_engine import evaluate_numeric_normality


class NormalityService:
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

    def _get_dimension_or_404(self, form: Form, dimension_id: str) -> FormDimension:
        for instrument in self._active_instruments(form):
            dimension = next((item for item in self._active_dimensions(instrument) if item.id == dimension_id), None)
            if dimension is not None:
                return dimension
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dimension not found for form")

    def _get_instrument_or_404(self, form: Form, instrument_id: str) -> FormInstrument:
        instrument = next((item for item in self._active_instruments(form) if item.id == instrument_id), None)
        if instrument is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found for form")
        return instrument

    def _get_project_variable_or_404(self, form: Form, project_variable_id: str) -> ProjectVariable:
        variable = next((item for item in self._active_project_variables(form) if item.id == project_variable_id), None)
        if variable is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project variable not found for form")
        return variable

    def _has_discarded_responses(self, form: Form) -> bool:
        return any(response.deleted_at is None and response.status == "discarded" for response in form.responses)

    def _get_base_column(self, question: FormQuestion, mapping: dict[str, QuestionColumnConfig]) -> str:
        return mapping[question.id].base_name

    def _get_score_column(self, question: FormQuestion, mapping: dict[str, QuestionColumnConfig], dataframe: pd.DataFrame) -> str | None:
        base_name = self._get_base_column(question, mapping)
        score_column = f"{base_name}__score"
        if score_column in dataframe.columns:
            return score_column
        if question.question_type == "number" and base_name in dataframe.columns:
            return base_name
        return None

    def _is_numeric_question(self, question: FormQuestion) -> bool:
        return question.question_type == "number" or question.is_scored

    def _context_from_result(self, result: dict[str, Any]) -> NormalityDescriptiveContextRead:
        descriptive_context = result["descriptive_context"]
        return NormalityDescriptiveContextRead(
            mean=descriptive_context.mean,
            median=descriptive_context.median,
            standard_deviation=descriptive_context.standard_deviation,
            skewness=descriptive_context.skewness,
            kurtosis=descriptive_context.kurtosis,
            minimum=descriptive_context.minimum,
            maximum=descriptive_context.maximum,
        )

    def _build_result(
        self,
        *,
        target_type: str,
        target_id: str,
        target_name: str,
        result: dict[str, Any],
        discarded_responses_excluded: bool,
    ) -> NormalityTestResultRead:
        warnings = list(result["warnings"])
        if discarded_responses_excluded:
            warnings.append("discarded_responses_excluded")
        return NormalityTestResultRead(
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            method=result["method"],
            statistic=result["statistic"],
            p_value=result["p_value"],
            alpha=result["alpha"],
            valid_n=result["valid_n"],
            missing_n=result["missing_n"],
            missing_percent=result["missing_percent"],
            classification=result["classification"],
            interpretation=result["interpretation"],
            warnings=list(dict.fromkeys(warnings)),
            descriptive_context=self._context_from_result(result),
        )

    def _not_applicable_result(
        self,
        *,
        target_type: str,
        target_id: str,
        target_name: str,
        total_n: int,
        warnings: list[str],
        discarded_responses_excluded: bool,
        reason_text: str,
    ) -> NormalityTestResultRead:
        if discarded_responses_excluded:
            warnings = [*warnings, "discarded_responses_excluded"]
        return NormalityTestResultRead(
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            method="not_applicable",
            statistic=None,
            p_value=None,
            alpha=0.05,
            valid_n=0,
            missing_n=total_n,
            missing_percent=round((total_n / total_n) * 100, 3) if total_n else 0.0,
            classification="not_applicable",
            interpretation=reason_text,
            warnings=list(dict.fromkeys(warnings)),
            descriptive_context=NormalityDescriptiveContextRead(
                mean=None,
                median=None,
                standard_deviation=None,
                skewness=None,
                kurtosis=None,
                minimum=None,
                maximum=None,
            ),
        )

    def _question_series(
        self,
        question: FormQuestion,
        dataframe: pd.DataFrame,
        mapping: dict[str, QuestionColumnConfig],
    ) -> pd.Series | None:
        if not self._is_numeric_question(question):
            return None
        score_column = self._get_score_column(question, mapping, dataframe)
        if score_column is None or score_column not in dataframe.columns:
            return None
        return pd.to_numeric(dataframe[score_column], errors="coerce")

    def _aggregate_group_series(
        self,
        questions: list[FormQuestion],
        dataframe: pd.DataFrame,
        mapping: dict[str, QuestionColumnConfig],
        *,
        aggregation: str,
    ) -> tuple[pd.Series | None, int]:
        score_columns = [
            column
            for question in questions
            if (column := self._get_score_column(question, mapping, dataframe)) is not None
        ]
        if not score_columns:
            return None, 0
        numeric_frame = dataframe[score_columns].apply(pd.to_numeric, errors="coerce")
        if aggregation == "sum":
            return numeric_frame.sum(axis=1, min_count=1), len(score_columns)
        return numeric_frame.mean(axis=1), len(score_columns)

    def _project_variable_series(
        self,
        variable: ProjectVariable,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict[str, QuestionColumnConfig],
        *,
        aggregation: str,
    ) -> tuple[pd.Series | None, int]:
        questions = [
            question
            for question in self._active_questions(form)
            if question.project_variable_id == variable.id
        ]
        scored_questions = [question for question in questions if question.is_scored]
        if scored_questions:
            return self._aggregate_group_series(scored_questions, dataframe, mapping, aggregation=aggregation)
        numeric_questions = [question for question in questions if question.question_type == "number"]
        if len(numeric_questions) == 1:
            series = self._question_series(numeric_questions[0], dataframe, mapping)
            return series, 1 if series is not None else 0
        return None, 0

    def _evaluate_series(
        self,
        *,
        target_type: str,
        target_id: str,
        target_name: str,
        series: pd.Series | None,
        total_n: int,
        method: str,
        alpha: float,
        decimals: int,
        discarded_responses_excluded: bool,
        extra_warnings: list[str] | None = None,
    ) -> NormalityTestResultRead:
        if series is None:
            return self._not_applicable_result(
                target_type=target_type,
                target_id=target_id,
                target_name=target_name,
                total_n=total_n,
                warnings=extra_warnings or ["non_numeric"],
                discarded_responses_excluded=discarded_responses_excluded,
                reason_text="No se aplicó una prueba de normalidad porque la variable no cuenta con datos numéricos suficientes o no corresponde a una escala donde la normalidad sea pertinente.",
            )

        result = evaluate_numeric_normality(
            series,
            total_n=total_n,
            method=method,
            alpha=alpha,
            decimals=decimals,
        )
        if extra_warnings:
            result["warnings"] = [*result["warnings"], *extra_warnings]
        return self._build_result(
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            result=result,
            discarded_responses_excluded=discarded_responses_excluded,
        )

    def get_question_normality(
        self,
        form_id: str,
        question_id: str,
        *,
        method: str = "auto",
        alpha: float = 0.05,
        decimals: int = 3,
        include_discarded: bool = False,
    ) -> NormalityTestResultRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        question = self._get_question_or_404(form, question_id)
        series = self._question_series(question, dataframe, mapping)
        return self._evaluate_series(
            target_type="question",
            target_id=question.id,
            target_name=question.label,
            series=series,
            total_n=len(dataframe),
            method=method,
            alpha=alpha,
            decimals=decimals,
            discarded_responses_excluded=not include_discarded and self._has_discarded_responses(form),
            extra_warnings=["non_numeric"] if series is None else None,
        )

    def get_dimension_normality_results(
        self,
        form_id: str,
        *,
        method: str = "auto",
        alpha: float = 0.05,
        decimals: int = 3,
        include_discarded: bool = False,
        score_aggregation: str = "mean",
    ) -> list[NormalityTestResultRead]:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and self._has_discarded_responses(form)
        results: list[NormalityTestResultRead] = []
        for instrument in self._active_instruments(form):
            for dimension in self._active_dimensions(instrument):
                questions = [
                    question
                    for question in self._active_questions(form)
                    if question.dimension_id == dimension.id and question.is_scored
                ]
                series, scored_count = self._aggregate_group_series(
                    questions,
                    dataframe,
                    mapping,
                    aggregation=score_aggregation,
                )
                results.append(
                    self._evaluate_series(
                        target_type="dimension",
                        target_id=dimension.id,
                        target_name=dimension.name,
                        series=series,
                        total_n=len(dataframe),
                        method=method,
                        alpha=alpha,
                        decimals=decimals,
                        discarded_responses_excluded=discarded_excluded,
                        extra_warnings=["no_scored_items"] if scored_count == 0 else None,
                    )
                )
        return results

    def get_instrument_normality_results(
        self,
        form_id: str,
        *,
        method: str = "auto",
        alpha: float = 0.05,
        decimals: int = 3,
        include_discarded: bool = False,
        score_aggregation: str = "mean",
    ) -> list[NormalityTestResultRead]:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and self._has_discarded_responses(form)
        results: list[NormalityTestResultRead] = []
        for instrument in self._active_instruments(form):
            questions = [
                question
                for question in self._active_questions(form)
                if question.instrument_id == instrument.id and question.is_scored
            ]
            series, scored_count = self._aggregate_group_series(
                questions,
                dataframe,
                mapping,
                aggregation=score_aggregation,
            )
            results.append(
                self._evaluate_series(
                    target_type="instrument",
                    target_id=instrument.id,
                    target_name=instrument.name,
                    series=series,
                    total_n=len(dataframe),
                    method=method,
                    alpha=alpha,
                    decimals=decimals,
                    discarded_responses_excluded=discarded_excluded,
                    extra_warnings=["no_scored_items"] if scored_count == 0 else None,
                )
            )
        return results

    def get_project_variable_normality_results(
        self,
        form_id: str,
        *,
        method: str = "auto",
        alpha: float = 0.05,
        decimals: int = 3,
        include_discarded: bool = False,
        score_aggregation: str = "mean",
    ) -> list[NormalityTestResultRead]:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and self._has_discarded_responses(form)
        results: list[NormalityTestResultRead] = []
        for variable in self._active_project_variables(form):
            series, numeric_item_count = self._project_variable_series(
                variable,
                form,
                dataframe,
                mapping,
                aggregation=score_aggregation,
            )
            results.append(
                self._evaluate_series(
                    target_type="project_variable",
                    target_id=variable.id,
                    target_name=variable.name,
                    series=series,
                    total_n=len(dataframe),
                    method=method,
                    alpha=alpha,
                    decimals=decimals,
                    discarded_responses_excluded=discarded_excluded,
                    extra_warnings=["non_numeric"] if numeric_item_count == 0 else None,
                )
            )
        return results

    def get_normality_report(
        self,
        form_id: str,
        *,
        method: str = "auto",
        alpha: float = 0.05,
        decimals: int = 3,
        include_discarded: bool = False,
        score_aggregation: str = "mean",
    ) -> NormalityReportRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and self._has_discarded_responses(form)
        question_results = [
            self._evaluate_series(
                target_type="question",
                target_id=question.id,
                target_name=question.label,
                series=self._question_series(question, dataframe, mapping),
                total_n=len(dataframe),
                method=method,
                alpha=alpha,
                decimals=decimals,
                discarded_responses_excluded=discarded_excluded,
                extra_warnings=["non_numeric"] if not self._is_numeric_question(question) else None,
            )
            for question in self._active_questions(form)
        ]
        dimension_results = self.get_dimension_normality_results(
            form_id,
            method=method,
            alpha=alpha,
            decimals=decimals,
            include_discarded=include_discarded,
            score_aggregation=score_aggregation,
        )
        instrument_results = self.get_instrument_normality_results(
            form_id,
            method=method,
            alpha=alpha,
            decimals=decimals,
            include_discarded=include_discarded,
            score_aggregation=score_aggregation,
        )
        variable_results = self.get_project_variable_normality_results(
            form_id,
            method=method,
            alpha=alpha,
            decimals=decimals,
            include_discarded=include_discarded,
            score_aggregation=score_aggregation,
        )
        results = [*question_results, *dimension_results, *instrument_results, *variable_results]
        counts = {
            "normal": sum(1 for result in results if result.classification == "normal"),
            "non_normal": sum(1 for result in results if result.classification == "non_normal"),
            "inconclusive": sum(1 for result in results if result.classification == "inconclusive"),
            "not_applicable": sum(1 for result in results if result.classification == "not_applicable"),
        }
        warnings: list[str] = []
        if len(dataframe) == 0:
            warnings.append("no_responses")
        if discarded_excluded:
            warnings.append("discarded_responses_excluded")
        return NormalityReportRead(
            form_id=form.id,
            project_id=form.project_id,
            method=method,
            alpha=alpha,
            include_discarded=include_discarded,
            score_aggregation=score_aggregation,
            total_targets=len(results),
            applicable_targets=sum(1 for result in results if result.classification in {"normal", "non_normal", "inconclusive"}),
            normal_count=counts["normal"],
            non_normal_count=counts["non_normal"],
            inconclusive_count=counts["inconclusive"],
            not_applicable_count=counts["not_applicable"],
            results=results,
            warnings=list(dict.fromkeys(warnings)),
        )

    def run_normality_analysis(self, form_id: str, payload: NormalityRunRequest) -> NormalityRunRead:
        report = self.get_normality_report(
            form_id,
            method=payload.method,
            alpha=payload.alpha,
            decimals=payload.decimals,
            include_discarded=payload.include_discarded,
            score_aggregation=payload.score_aggregation,
        )
        analysis_run = None
        if payload.store_result:
            analysis_run = AnalysisRun(
                project_id=report.project_id,
                form_id=report.form_id,
                analysis_type="normality",
                status="completed",
                params_json=payload.model_dump(),
                result_json={
                    "total_targets": report.total_targets,
                    "applicable_targets": report.applicable_targets,
                    "normal_count": report.normal_count,
                    "non_normal_count": report.non_normal_count,
                    "inconclusive_count": report.inconclusive_count,
                    "not_applicable_count": report.not_applicable_count,
                },
            )
            self.db.add(analysis_run)
            self.db.commit()
            self.db.refresh(analysis_run)
        return NormalityRunRead(
            analysis_run_id=analysis_run.id if analysis_run is not None else None,
            created_at=analysis_run.created_at if analysis_run is not None else None,
            report=report,
        )
