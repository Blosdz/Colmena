from dataclasses import dataclass

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.form import Form
from app.models.form_question import FormQuestion
from app.schemas.normality import NormalityTestResultRead
from app.schemas.statistical_decision import (
    DecisionVariableInput,
    StatisticalDecisionRead,
    StatisticalDecisionRequest,
)
from app.services.normality_service import NormalityService
from app.statistics.correlation_engine import detect_many_ties, is_dichotomous
from app.statistics.decision_engine import (
    recommend_association_categorical,
    recommend_correlation,
    recommend_descriptive_only,
    recommend_independent_groups,
    recommend_related_groups,
)
from app.statistics.normality_engine import evaluate_numeric_normality


@dataclass
class ResolvedDecisionVariable:
    target_type: str
    target_id: str
    target_name: str
    kind: str
    measurement_level: str
    series: pd.Series
    normality_result: NormalityTestResultRead
    role: str | None


def item_is_dichotomous(item: ResolvedDecisionVariable) -> bool:
    return item.measurement_level == "dichotomous" or is_dichotomous(item.series)


class StatisticalDecisionService:
    def __init__(self, db: Session):
        self.db = db
        self.normality_service = NormalityService(db)

    def _get_context(
        self,
        form_id: str,
        *,
        include_discarded: bool,
    ) -> tuple[Form, pd.DataFrame, dict]:
        return self.normality_service._get_form_context(form_id, include_discarded=include_discarded)

    def _resolve_question(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        variable_input: DecisionVariableInput,
        request: StatisticalDecisionRequest,
    ) -> ResolvedDecisionVariable:
        assert variable_input.question_id is not None
        question = self.normality_service._get_question_or_404(form, variable_input.question_id)
        if self.normality_service._is_numeric_question(question):
            series = self.normality_service._question_series(question, dataframe, mapping)
            normality_result = self.normality_service.get_question_normality(
                form.id,
                question.id,
                method=request.normality_method,
                alpha=request.alpha,
                decimals=3,
                include_discarded=request.include_discarded,
            )
            kind = "numeric"
        else:
            column = self.normality_service._get_base_column(question, mapping)
            series = dataframe[column] if column in dataframe.columns else pd.Series(dtype="object")
            normality_result = self.normality_service.get_question_normality(
                form.id,
                question.id,
                method=request.normality_method,
                alpha=request.alpha,
                decimals=3,
                include_discarded=request.include_discarded,
            )
            kind = "categorical"
        return ResolvedDecisionVariable(
            target_type="question",
            target_id=question.id,
            target_name=question.label,
            kind=kind,
            measurement_level=question.measurement_level,
            series=series,
            normality_result=normality_result,
            role=variable_input.role,
        )

    def _resolve_dimension(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        variable_input: DecisionVariableInput,
        request: StatisticalDecisionRequest,
    ) -> ResolvedDecisionVariable:
        assert variable_input.dimension_id is not None
        dimension = self.normality_service._get_dimension_or_404(form, variable_input.dimension_id)
        questions = [
            question
            for question in self.normality_service._active_questions(form)
            if question.dimension_id == dimension.id and question.is_scored
        ]
        series, _ = self.normality_service._aggregate_group_series(
            questions,
            dataframe,
            mapping,
            aggregation=request.score_aggregation,
        )
        normality_result = next(
            item
            for item in self.normality_service.get_dimension_normality_results(
                form.id,
                method=request.normality_method,
                alpha=request.alpha,
                decimals=3,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
            )
            if item.target_id == dimension.id
        )
        return ResolvedDecisionVariable(
            target_type="dimension",
            target_id=dimension.id,
            target_name=dimension.name,
            kind="numeric",
            measurement_level="interval",
            series=series if series is not None else pd.Series(dtype="float"),
            normality_result=normality_result,
            role=variable_input.role,
        )

    def _resolve_instrument(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        variable_input: DecisionVariableInput,
        request: StatisticalDecisionRequest,
    ) -> ResolvedDecisionVariable:
        assert variable_input.instrument_id is not None
        instrument = self.normality_service._get_instrument_or_404(form, variable_input.instrument_id)
        questions = [
            question
            for question in self.normality_service._active_questions(form)
            if question.instrument_id == instrument.id and question.is_scored
        ]
        series, _ = self.normality_service._aggregate_group_series(
            questions,
            dataframe,
            mapping,
            aggregation=request.score_aggregation,
        )
        normality_result = next(
            item
            for item in self.normality_service.get_instrument_normality_results(
                form.id,
                method=request.normality_method,
                alpha=request.alpha,
                decimals=3,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
            )
            if item.target_id == instrument.id
        )
        return ResolvedDecisionVariable(
            target_type="instrument",
            target_id=instrument.id,
            target_name=instrument.name,
            kind="numeric",
            measurement_level="interval",
            series=series if series is not None else pd.Series(dtype="float"),
            normality_result=normality_result,
            role=variable_input.role,
        )

    def _resolve_project_variable(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        variable_input: DecisionVariableInput,
        request: StatisticalDecisionRequest,
    ) -> ResolvedDecisionVariable:
        assert variable_input.project_variable_id is not None
        project_variable = self.normality_service._get_project_variable_or_404(form, variable_input.project_variable_id)
        series, numeric_count = self.normality_service._project_variable_series(
            project_variable,
            form,
            dataframe,
            mapping,
            aggregation=request.score_aggregation,
        )
        if series is None:
            linked_questions = [
                question
                for question in self.normality_service._active_questions(form)
                if question.project_variable_id == project_variable.id
            ]
            if len(linked_questions) == 1 and not self.normality_service._is_numeric_question(linked_questions[0]):
                column = self.normality_service._get_base_column(linked_questions[0], mapping)
                series = dataframe[column] if column in dataframe.columns else pd.Series(dtype="object")
                kind = "categorical"
            else:
                kind = "categorical" if numeric_count == 0 else "numeric"
                series = pd.Series(dtype="object") if kind == "categorical" else pd.Series(dtype="float")
        else:
            kind = "numeric"
        normality_result = next(
            item
            for item in self.normality_service.get_project_variable_normality_results(
                form.id,
                method=request.normality_method,
                alpha=request.alpha,
                decimals=3,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
            )
            if item.target_id == project_variable.id
        )
        return ResolvedDecisionVariable(
            target_type="project_variable",
            target_id=project_variable.id,
            target_name=project_variable.name,
            kind=kind,
            measurement_level=project_variable.measurement_level,
            series=series,
            normality_result=normality_result,
            role=variable_input.role,
        )

    def _resolve_variable(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        variable_input: DecisionVariableInput,
        request: StatisticalDecisionRequest,
    ) -> ResolvedDecisionVariable:
        provided = [
            variable_input.question_id,
            variable_input.dimension_id,
            variable_input.instrument_id,
            variable_input.project_variable_id,
        ]
        if sum(1 for value in provided if value is not None) != 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Each variable must define exactly one target id")
        if variable_input.question_id is not None:
            return self._resolve_question(form, dataframe, mapping, variable_input, request)
        if variable_input.dimension_id is not None:
            return self._resolve_dimension(form, dataframe, mapping, variable_input, request)
        if variable_input.instrument_id is not None:
            return self._resolve_instrument(form, dataframe, mapping, variable_input, request)
        return self._resolve_project_variable(form, dataframe, mapping, variable_input, request)

    def _group_normality_ok(
        self,
        outcome: ResolvedDecisionVariable,
        group: ResolvedDecisionVariable,
        request: StatisticalDecisionRequest,
    ) -> tuple[bool, int]:
        paired = pd.DataFrame({"outcome": outcome.series, "group": group.series}).dropna()
        if paired.empty:
            return False, 0
        min_group_n = 0
        all_normal = True
        for _, subset in paired.groupby("group"):
            subset_series = pd.to_numeric(subset["outcome"], errors="coerce").dropna()
            if subset_series.empty:
                continue
            if min_group_n == 0 or len(subset_series) < min_group_n:
                min_group_n = len(subset_series)
            result = evaluate_numeric_normality(
                subset_series,
                total_n=len(subset_series),
                method=request.normality_method,
                alpha=request.alpha,
                decimals=3,
            )
            if result["classification"] != "normal":
                all_normal = False
        return all_normal, min_group_n

    def _build_paired_difference_normality(
        self,
        before: ResolvedDecisionVariable,
        after: ResolvedDecisionVariable,
        request: StatisticalDecisionRequest,
    ) -> NormalityTestResultRead:
        paired = pd.DataFrame({"before": before.series, "after": after.series}).dropna()
        diff = paired["after"] - paired["before"] if not paired.empty else pd.Series(dtype="float")
        result = evaluate_numeric_normality(
            diff,
            total_n=len(diff),
            method=request.normality_method,
            alpha=request.alpha,
            decimals=3,
        )
        return NormalityTestResultRead(
            target_type="question",
            target_id="paired_difference",
            target_name="Diferencia pareada",
            method=result["method"],
            statistic=result["statistic"],
            p_value=result["p_value"],
            alpha=result["alpha"],
            valid_n=result["valid_n"],
            missing_n=result["missing_n"],
            missing_percent=result["missing_percent"],
            classification=result["classification"],
            interpretation=result["interpretation"],
            warnings=result["warnings"],
            descriptive_context=self.normality_service._context_from_result(result),
        )

    def make_decision(
        self,
        form_id: str,
        request: StatisticalDecisionRequest,
    ) -> StatisticalDecisionRead:
        form, dataframe, mapping = self._get_context(form_id, include_discarded=request.include_discarded)
        resolved = [
            self._resolve_variable(form, dataframe, mapping, variable_input, request)
            for variable_input in request.variables
        ]
        normality_results = [item.normality_result for item in resolved]
        warnings: list[str] = []
        assumptions_checked: list[str] = []
        assumptions_failed: list[str] = []
        required_next_steps: list[str] = []

        if request.analysis_goal == "descriptive_only":
            engine_result = recommend_descriptive_only("descriptive_only_requested")
            required_next_steps.append("Definir claramente la pregunta inferencial antes de recomendar una prueba estadística.")
        elif request.analysis_goal == "correlation":
            x = next((item for item in resolved if item.role == "x"), resolved[0] if len(resolved) > 0 else None)
            y = next((item for item in resolved if item.role == "y"), resolved[1] if len(resolved) > 1 else None)
            if x is None or y is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Correlation requires variables with roles x and y")
            if x.kind != "numeric" or y.kind != "numeric":
                engine_result = recommend_descriptive_only("invalid_variable_types")
            else:
                assumptions_checked.extend(["numeric_variables", "normality_reviewed"])
                all_normal = all(item.normality_result.classification == "normal" for item in [x, y])
                has_ordinal = any(item.measurement_level == "ordinal" for item in [x, y])
                min_valid_n = min(item.normality_result.valid_n for item in [x, y])
                x_dichotomous = item_is_dichotomous(x)
                y_dichotomous = item_is_dichotomous(y)
                has_dichotomous_continuous = (
                    (x_dichotomous and not y_dichotomous and y.measurement_level != "ordinal")
                    or (y_dichotomous and not x_dichotomous and x.measurement_level != "ordinal")
                )
                many_ties = not has_ordinal and (detect_many_ties(x.series) or detect_many_ties(y.series))
                engine_result = recommend_correlation(
                    all_normal=all_normal,
                    has_ordinal=has_ordinal,
                    min_valid_n=min_valid_n,
                    has_dichotomous_continuous=has_dichotomous_continuous,
                    many_ties=many_ties,
                )
                if not all_normal:
                    assumptions_failed.append("normality")
                if has_ordinal:
                    assumptions_failed.append("ordinal_scale")
                required_next_steps.append("Calcular la correlación sugerida en la siguiente fase usando las variables seleccionadas.")
        elif request.analysis_goal == "association_categorical":
            if len(resolved) < 2 or any(item.kind != "categorical" for item in resolved[:2]):
                engine_result = recommend_descriptive_only("invalid_variable_types")
            else:
                assumptions_checked.extend(["categorical_variables"])
                engine_result = recommend_association_categorical()
                required_next_steps.append("Construir tabla de contingencia inferencial y revisar frecuencias esperadas.")
        elif request.analysis_goal == "comparison_independent_groups":
            outcome = next((item for item in resolved if item.role == "outcome"), None)
            group = next((item for item in resolved if item.role == "group"), None)
            if outcome is None or group is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="comparison_independent_groups requires outcome and group roles")
            if group.kind != "categorical":
                engine_result = recommend_descriptive_only("group_must_be_categorical")
            else:
                group_count = int(group.series.dropna().nunique())
                assumptions_checked.extend(["grouping_variable", "normality_reviewed"])
                if outcome.kind == "numeric":
                    all_normal, min_group_n = self._group_normality_ok(outcome, group, request)
                else:
                    all_normal, min_group_n = False, int(group.series.dropna().shape[0])
                engine_result = recommend_independent_groups(
                    group_count=group_count,
                    outcome_normal=all_normal,
                    min_group_n=min_group_n,
                    categorical_outcome=outcome.kind != "numeric",
                )
                if not all_normal and outcome.kind == "numeric":
                    assumptions_failed.append("normality")
                required_next_steps.append("Evaluar homogeneidad de varianzas y ejecutar la prueba recomendada en una fase posterior.")
        elif request.analysis_goal == "comparison_related_groups":
            before = next((item for item in resolved if item.role == "paired_before"), None)
            after = next((item for item in resolved if item.role == "paired_after"), None)
            if before is None or after is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="comparison_related_groups requires paired_before and paired_after roles")
            if before.kind != "numeric" or after.kind != "numeric":
                engine_result = recommend_descriptive_only("invalid_variable_types")
            else:
                diff_normality = self._build_paired_difference_normality(before, after, request)
                normality_results.append(diff_normality)
                both_normal = diff_normality.classification == "normal"
                engine_result = recommend_related_groups(
                    both_normal=both_normal,
                    min_valid_n=diff_normality.valid_n,
                )
                assumptions_checked.extend(["paired_design", "difference_normality_reviewed"])
                if not both_normal:
                    assumptions_failed.append("difference_normality")
                required_next_steps.append("Confirmar emparejamiento y ejecutar la prueba sugerida sobre las diferencias.")
        else:
            engine_result = recommend_descriptive_only("unsupported_analysis_goal")

        warnings.extend(engine_result.get("warnings", []))
        assumptions_failed.extend(engine_result.get("assumptions_failed", []))
        analysis_run = None
        if request.store_result:
            analysis_run = AnalysisRun(
                project_id=form.project_id,
                form_id=form.id,
                analysis_type="statistical_decision",
                status="completed",
                params_json=request.model_dump(),
                result_json={
                    "analysis_goal": request.analysis_goal,
                    "recommended_test": engine_result["recommended_test"],
                    "route": engine_result["route"],
                    "confidence": engine_result["confidence"],
                },
            )
            self.db.add(analysis_run)
            self.db.commit()
            self.db.refresh(analysis_run)

        return StatisticalDecisionRead(
            form_id=form.id,
            project_id=form.project_id,
            analysis_goal=request.analysis_goal,
            recommended_test=engine_result["recommended_test"],
            alternative_tests=engine_result.get("alternative_tests", []),
            route=engine_result["route"],
            confidence=engine_result["confidence"],
            assumptions_checked=list(dict.fromkeys(assumptions_checked)),
            assumptions_failed=list(dict.fromkeys(assumptions_failed)),
            required_next_steps=list(dict.fromkeys(required_next_steps)),
            explanation=engine_result["explanation"],
            warnings=list(dict.fromkeys(warnings)),
            normality_results=normality_results,
            analysis_run_id=analysis_run.id if analysis_run is not None else None,
        )
