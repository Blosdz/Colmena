import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.form import Form
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.project_variable import ProjectVariable
from app.schemas.reliability import (
    CompositeReliabilityReportRead,
    CompositeReliabilityTargetRead,
    ReliabilityReportRead,
    ReliabilityRunRead,
    ReliabilityRunRequest,
    ReliabilityTargetRead,
)
from app.services.dataset_service import DatasetService, QuestionColumnConfig
from app.statistics.cfa_engine import single_factor_cfa
from app.statistics.reliability_engine import cronbach_alpha


class ReliabilityService:
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

    def _get_instrument_or_404(self, form: Form, instrument_id: str) -> FormInstrument:
        instrument = next((item for item in self._active_instruments(form) if item.id == instrument_id), None)
        if instrument is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found for form")
        return instrument

    def _get_dimension_or_404(self, form: Form, dimension_id: str) -> FormDimension:
        for instrument in self._active_instruments(form):
            dimension = next((item for item in self._active_dimensions(instrument) if item.id == dimension_id), None)
            if dimension is not None:
                return dimension
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dimension not found for form")

    def _has_discarded_responses(self, form: Form) -> bool:
        return any(response.deleted_at is None and response.status == "discarded" for response in form.responses)

    def _score_column(
        self,
        question: FormQuestion,
        mapping: dict[str, QuestionColumnConfig],
        dataframe: pd.DataFrame,
    ) -> str | None:
        config = mapping.get(question.id)
        if config is None:
            return None
        base_name = config.base_name
        score_column = f"{base_name}__score"
        if score_column in dataframe.columns:
            return score_column
        if question.question_type == "number" and base_name in dataframe.columns:
            return base_name
        return None

    def _item_columns(
        self,
        questions: list[FormQuestion],
        mapping: dict[str, QuestionColumnConfig],
        dataframe: pd.DataFrame,
    ) -> tuple[dict[str, str], dict[str, str]]:
        item_columns: dict[str, str] = {}
        item_labels: dict[str, str] = {}
        for question in questions:
            column = self._score_column(question, mapping, dataframe)
            if column is None:
                continue
            item_columns[question.id] = column
            item_labels[question.id] = question.code or question.label
        return item_columns, item_labels

    def _compute_target(
        self,
        *,
        target_type: str,
        target_id: str,
        target_name: str,
        questions: list[FormQuestion],
        dataframe: pd.DataFrame,
        mapping: dict[str, QuestionColumnConfig],
        decimals: int,
        discarded_excluded: bool,
    ) -> ReliabilityTargetRead:
        scored_questions = [question for question in questions if question.is_scored]
        item_columns, item_labels = self._item_columns(scored_questions, mapping, dataframe)
        result = cronbach_alpha(dataframe, item_columns, item_labels=item_labels, decimals=decimals)
        if discarded_excluded:
            result = result.model_copy(
                update={"warnings": list(dict.fromkeys([*result.warnings, "discarded_responses_excluded"]))}
            )
        return ReliabilityTargetRead(
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            item_count=len(item_columns),
            result=result,
        )

    def _compute_composite_target(
        self,
        *,
        target_type: str,
        target_id: str,
        target_name: str,
        questions: list[FormQuestion],
        dataframe: pd.DataFrame,
        mapping: dict[str, QuestionColumnConfig],
        decimals: int,
        discarded_excluded: bool,
    ) -> CompositeReliabilityTargetRead:
        scored_questions = [question for question in questions if question.is_scored]
        item_columns, item_labels = self._item_columns(scored_questions, mapping, dataframe)
        result = single_factor_cfa(dataframe, item_columns, item_labels=item_labels, decimals=decimals)
        if discarded_excluded:
            result = result.model_copy(
                update={"warnings": list(dict.fromkeys([*result.warnings, "discarded_responses_excluded"]))}
            )
        return CompositeReliabilityTargetRead(
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            item_count=len(item_columns),
            result=result,
        )

    def get_instrument_composite_reliability(
        self,
        form_id: str,
        instrument_id: str,
        *,
        decimals: int = 3,
        include_discarded: bool = False,
    ) -> CompositeReliabilityTargetRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        instrument = self._get_instrument_or_404(form, instrument_id)
        questions = [
            question
            for question in self._active_questions(form)
            if question.instrument_id == instrument.id
        ]
        return self._compute_composite_target(
            target_type="instrument",
            target_id=instrument.id,
            target_name=instrument.name,
            questions=questions,
            dataframe=dataframe,
            mapping=mapping,
            decimals=decimals,
            discarded_excluded=not include_discarded and self._has_discarded_responses(form),
        )

    def get_dimension_composite_reliability(
        self,
        form_id: str,
        dimension_id: str,
        *,
        decimals: int = 3,
        include_discarded: bool = False,
    ) -> CompositeReliabilityTargetRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        dimension = self._get_dimension_or_404(form, dimension_id)
        questions = [
            question
            for question in self._active_questions(form)
            if question.dimension_id == dimension.id
        ]
        return self._compute_composite_target(
            target_type="dimension",
            target_id=dimension.id,
            target_name=dimension.name,
            questions=questions,
            dataframe=dataframe,
            mapping=mapping,
            decimals=decimals,
            discarded_excluded=not include_discarded and self._has_discarded_responses(form),
        )

    def get_composite_reliability_report(
        self,
        form_id: str,
        *,
        decimals: int = 3,
        include_discarded: bool = False,
    ) -> CompositeReliabilityReportRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and self._has_discarded_responses(form)
        questions = self._active_questions(form)
        results: list[CompositeReliabilityTargetRead] = []

        for instrument in self._active_instruments(form):
            instrument_questions = [q for q in questions if q.instrument_id == instrument.id]
            results.append(
                self._compute_composite_target(
                    target_type="instrument",
                    target_id=instrument.id,
                    target_name=instrument.name,
                    questions=instrument_questions,
                    dataframe=dataframe,
                    mapping=mapping,
                    decimals=decimals,
                    discarded_excluded=discarded_excluded,
                )
            )
            for dimension in self._active_dimensions(instrument):
                dimension_questions = [q for q in questions if q.dimension_id == dimension.id]
                results.append(
                    self._compute_composite_target(
                        target_type="dimension",
                        target_id=dimension.id,
                        target_name=dimension.name,
                        questions=dimension_questions,
                        dataframe=dataframe,
                        mapping=mapping,
                        decimals=decimals,
                        discarded_excluded=discarded_excluded,
                    )
                )

        warnings: list[str] = []
        if len(dataframe) == 0:
            warnings.append("no_responses")
        if discarded_excluded:
            warnings.append("discarded_responses_excluded")

        return CompositeReliabilityReportRead(
            form_id=form.id,
            project_id=form.project_id,
            include_discarded=include_discarded,
            total_targets=len(results),
            applicable_targets=sum(1 for item in results if item.result.classification != "not_applicable"),
            results=results,
            warnings=list(dict.fromkeys(warnings)),
        )

    def get_instrument_reliability(
        self,
        form_id: str,
        instrument_id: str,
        *,
        decimals: int = 3,
        include_discarded: bool = False,
    ) -> ReliabilityTargetRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        instrument = self._get_instrument_or_404(form, instrument_id)
        questions = [
            question
            for question in self._active_questions(form)
            if question.instrument_id == instrument.id
        ]
        return self._compute_target(
            target_type="instrument",
            target_id=instrument.id,
            target_name=instrument.name,
            questions=questions,
            dataframe=dataframe,
            mapping=mapping,
            decimals=decimals,
            discarded_excluded=not include_discarded and self._has_discarded_responses(form),
        )

    def get_dimension_reliability(
        self,
        form_id: str,
        dimension_id: str,
        *,
        decimals: int = 3,
        include_discarded: bool = False,
    ) -> ReliabilityTargetRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        dimension = self._get_dimension_or_404(form, dimension_id)
        questions = [
            question
            for question in self._active_questions(form)
            if question.dimension_id == dimension.id
        ]
        return self._compute_target(
            target_type="dimension",
            target_id=dimension.id,
            target_name=dimension.name,
            questions=questions,
            dataframe=dataframe,
            mapping=mapping,
            decimals=decimals,
            discarded_excluded=not include_discarded and self._has_discarded_responses(form),
        )

    def get_reliability_report(
        self,
        form_id: str,
        *,
        decimals: int = 3,
        include_discarded: bool = False,
    ) -> ReliabilityReportRead:
        form, dataframe, mapping = self._get_form_context(form_id, include_discarded=include_discarded)
        discarded_excluded = not include_discarded and self._has_discarded_responses(form)
        questions = self._active_questions(form)
        results: list[ReliabilityTargetRead] = []

        for instrument in self._active_instruments(form):
            instrument_questions = [q for q in questions if q.instrument_id == instrument.id]
            results.append(
                self._compute_target(
                    target_type="instrument",
                    target_id=instrument.id,
                    target_name=instrument.name,
                    questions=instrument_questions,
                    dataframe=dataframe,
                    mapping=mapping,
                    decimals=decimals,
                    discarded_excluded=discarded_excluded,
                )
            )
            for dimension in self._active_dimensions(instrument):
                dimension_questions = [q for q in questions if q.dimension_id == dimension.id]
                results.append(
                    self._compute_target(
                        target_type="dimension",
                        target_id=dimension.id,
                        target_name=dimension.name,
                        questions=dimension_questions,
                        dataframe=dataframe,
                        mapping=mapping,
                        decimals=decimals,
                        discarded_excluded=discarded_excluded,
                    )
                )

        for variable in self._active_project_variables(form):
            variable_questions = [q for q in questions if q.project_variable_id == variable.id]
            results.append(
                self._compute_target(
                    target_type="project_variable",
                    target_id=variable.id,
                    target_name=variable.name,
                    questions=variable_questions,
                    dataframe=dataframe,
                    mapping=mapping,
                    decimals=decimals,
                    discarded_excluded=discarded_excluded,
                )
            )

        warnings: list[str] = []
        if len(dataframe) == 0:
            warnings.append("no_responses")
        if discarded_excluded:
            warnings.append("discarded_responses_excluded")

        return ReliabilityReportRead(
            form_id=form.id,
            project_id=form.project_id,
            include_discarded=include_discarded,
            total_targets=len(results),
            applicable_targets=sum(1 for item in results if item.result.classification != "not_applicable"),
            results=results,
            warnings=list(dict.fromkeys(warnings)),
        )

    def run_reliability_analysis(self, form_id: str, payload: ReliabilityRunRequest) -> ReliabilityRunRead:
        report = self.get_reliability_report(
            form_id,
            decimals=payload.decimals,
            include_discarded=payload.include_discarded,
        )
        analysis_run = None
        if payload.store_result:
            analysis_run = AnalysisRun(
                project_id=report.project_id,
                form_id=report.form_id,
                analysis_type="reliability",
                status="completed",
                params_json=payload.model_dump(),
                result_json={
                    "total_targets": report.total_targets,
                    "applicable_targets": report.applicable_targets,
                    "targets": [
                        {
                            "target_type": item.target_type,
                            "target_id": item.target_id,
                            "target_name": item.target_name,
                            "item_count": item.item_count,
                            "alpha": item.result.alpha,
                            "classification": item.result.classification,
                        }
                        for item in report.results
                    ],
                },
            )
            self.db.add(analysis_run)
            self.db.commit()
            self.db.refresh(analysis_run)
        return ReliabilityRunRead(
            analysis_run_id=analysis_run.id if analysis_run is not None else None,
            created_at=analysis_run.created_at if analysis_run is not None else None,
            report=report,
        )
