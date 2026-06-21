from dataclasses import dataclass

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.form import Form
from app.models.form_question import FormQuestion
from app.models.project_variable import ProjectVariable
from app.schemas.group_comparison import (
    ComparisonTargetInput,
    ComparisonTargetRead,
    EffectSizeRead,
    GroupComparisonOptionsRead,
    GroupComparisonRequest,
    GroupComparisonResultRead,
    GroupComparisonRunRead,
    GroupDescriptiveRead,
    VarianceHomogeneityRead,
)
from app.schemas.normality import NormalityDescriptiveContextRead, NormalityTestResultRead
from app.services.normality_service import NormalityService
from app.statistics.group_comparison_engine import (
    build_group_descriptives,
    classify_effect_size,
    clean_groups,
    detect_outliers_by_group,
    independent_t_test,
    kruskal_wallis_test,
    levene_variance_test,
    mann_whitney_u_test,
    one_way_anova,
    welch_t_test,
)
from app.statistics.normality_engine import evaluate_numeric_normality


@dataclass
class ResolvedOutcomeTarget:
    target_type: str
    target_id: str
    label: str
    measurement_level: str
    series: pd.Series | None
    numeric: bool


@dataclass
class ResolvedGroupTarget:
    target_type: str
    target_id: str
    label: str
    measurement_level: str
    label_series: pd.Series | None
    value_series: pd.Series | None
    categorical: bool


class GroupComparisonService:
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

    def _to_target_read(self, target: ResolvedOutcomeTarget | ResolvedGroupTarget) -> ComparisonTargetRead:
        return ComparisonTargetRead(target_type=target.target_type, target_id=target.target_id, label=target.label)

    def _question_supports_grouping(self, question: FormQuestion) -> bool:
        if question.deleted_at is not None:
            return False
        if question.question_type in {"single_choice", "dropdown", "boolean", "likert"}:
            return True
        if question.data_type == "categorical" and question.question_type not in {"number", "text_long", "date"}:
            return True
        return False

    def _project_variable_group_data(
        self,
        variable: ProjectVariable,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
    ) -> tuple[pd.Series | None, pd.Series | None]:
        linked_questions = [
            question
            for question in self.normality_service._active_questions(form)
            if question.project_variable_id == variable.id
        ]
        if len(linked_questions) != 1:
            return None, None
        question = linked_questions[0]
        if not self._question_supports_grouping(question):
            return None, None
        base_name = self.normality_service._get_base_column(question, mapping)
        label_series = dataframe[base_name] if base_name in dataframe.columns else None
        value_name = f"{base_name}__value"
        value_series = dataframe[value_name] if value_name in dataframe.columns else label_series
        return label_series, value_series

    def resolve_outcome_target(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        target: ComparisonTargetInput,
        *,
        score_aggregation: str,
    ) -> ResolvedOutcomeTarget:
        if target.target_type == "question":
            question = self.normality_service._get_question_or_404(form, target.target_id)
            series = self.normality_service._question_series(question, dataframe, mapping)
            return ResolvedOutcomeTarget(
                target_type="question",
                target_id=question.id,
                label=question.label,
                measurement_level=question.measurement_level,
                series=series,
                numeric=series is not None,
            )
        if target.target_type == "dimension":
            dimension = self.normality_service._get_dimension_or_404(form, target.target_id)
            questions = [
                question
                for question in self.normality_service._active_questions(form)
                if question.dimension_id == dimension.id and question.is_scored
            ]
            series, scored_count = self.normality_service._aggregate_group_series(
                questions,
                dataframe,
                mapping,
                aggregation=score_aggregation,
            )
            return ResolvedOutcomeTarget(
                target_type="dimension",
                target_id=dimension.id,
                label=dimension.name,
                measurement_level="interval",
                series=series,
                numeric=series is not None and scored_count > 0,
            )
        if target.target_type == "instrument":
            instrument = self.normality_service._get_instrument_or_404(form, target.target_id)
            questions = [
                question
                for question in self.normality_service._active_questions(form)
                if question.instrument_id == instrument.id and question.is_scored
            ]
            series, scored_count = self.normality_service._aggregate_group_series(
                questions,
                dataframe,
                mapping,
                aggregation=score_aggregation,
            )
            return ResolvedOutcomeTarget(
                target_type="instrument",
                target_id=instrument.id,
                label=instrument.name,
                measurement_level="interval",
                series=series,
                numeric=series is not None and scored_count > 0,
            )
        if target.target_type == "project_variable":
            variable = self.normality_service._get_project_variable_or_404(form, target.target_id)
            series, numeric_count = self.normality_service._project_variable_series(
                variable,
                form,
                dataframe,
                mapping,
                aggregation=score_aggregation,
            )
            return ResolvedOutcomeTarget(
                target_type="project_variable",
                target_id=variable.id,
                label=variable.name,
                measurement_level=variable.measurement_level,
                series=series,
                numeric=series is not None and numeric_count > 0,
            )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported outcome target")

    def resolve_group_target(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        target: ComparisonTargetInput,
    ) -> ResolvedGroupTarget:
        if target.target_type == "question":
            question = self.normality_service._get_question_or_404(form, target.target_id)
            if not self._question_supports_grouping(question):
                return ResolvedGroupTarget(
                    target_type="question",
                    target_id=question.id,
                    label=question.label,
                    measurement_level=question.measurement_level,
                    label_series=None,
                    value_series=None,
                    categorical=False,
                )
            base_name = self.normality_service._get_base_column(question, mapping)
            label_series = dataframe[base_name] if base_name in dataframe.columns else None
            value_name = f"{base_name}__value"
            value_series = dataframe[value_name] if value_name in dataframe.columns else label_series
            return ResolvedGroupTarget(
                target_type="question",
                target_id=question.id,
                label=question.label,
                measurement_level=question.measurement_level,
                label_series=label_series,
                value_series=value_series,
                categorical=label_series is not None and value_series is not None,
            )
        if target.target_type == "project_variable":
            variable = self.normality_service._get_project_variable_or_404(form, target.target_id)
            label_series, value_series = self._project_variable_group_data(variable, form, dataframe, mapping)
            return ResolvedGroupTarget(
                target_type="project_variable",
                target_id=variable.id,
                label=variable.name,
                measurement_level=variable.measurement_level,
                label_series=label_series,
                value_series=value_series,
                categorical=label_series is not None and value_series is not None,
            )
        if target.target_type == "dimension":
            dimension = self.normality_service._get_dimension_or_404(form, target.target_id)
            return ResolvedGroupTarget(
                target_type="dimension",
                target_id=dimension.id,
                label=dimension.name,
                measurement_level="interval",
                label_series=None,
                value_series=None,
                categorical=False,
            )
        instrument = self.normality_service._get_instrument_or_404(form, target.target_id)
        return ResolvedGroupTarget(
            target_type="instrument",
            target_id=instrument.id,
            label=instrument.name,
            measurement_level="interval",
            label_series=None,
            value_series=None,
            categorical=False,
        )

    def _build_normality_result(
        self,
        *,
        group_value: str,
        group_label: str,
        outcome_label: str,
        series: pd.Series,
        alpha: float,
        decimals: int,
    ) -> NormalityTestResultRead:
        result = evaluate_numeric_normality(
            series,
            total_n=len(series.dropna()),
            method="auto",
            alpha=alpha,
            decimals=decimals,
        )
        context = result["descriptive_context"]
        return NormalityTestResultRead(
            target_type="question",
            target_id=str(group_value),
            target_name=f"{outcome_label} | {group_label}",
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
            descriptive_context=NormalityDescriptiveContextRead(
                mean=context.mean,
                median=context.median,
                standard_deviation=context.standard_deviation,
                skewness=context.skewness,
                kurtosis=context.kurtosis,
                minimum=context.minimum,
                maximum=context.maximum,
            ),
        )

    def get_normality_by_group(
        self,
        groups: dict[str, pd.Series],
        group_labels: dict[str, str],
        *,
        outcome_label: str,
        alpha: float,
        decimals: int,
    ) -> list[NormalityTestResultRead]:
        return [
            self._build_normality_result(
                group_value=group_value,
                group_label=group_labels.get(group_value, group_value),
                outcome_label=outcome_label,
                series=series,
                alpha=alpha,
                decimals=decimals,
            )
            for group_value, series in groups.items()
        ]

    def get_variance_homogeneity(
        self,
        groups: dict[str, pd.Series],
        *,
        alpha: float,
        decimals: int,
    ) -> VarianceHomogeneityRead:
        result = levene_variance_test(groups, alpha=alpha, decimals=decimals)
        if result["classification"] == "homogeneous":
            interpretation = (
                "La prueba de Levene no evidencio una diferencia estadisticamente significativa entre las varianzas de los grupos, "
                "por lo que pueden tratarse como compatibles con homogeneidad para esta decision inicial."
            )
        elif result["classification"] == "non_homogeneous":
            interpretation = (
                "La prueba de Levene evidencio diferencias estadisticamente significativas entre las varianzas de los grupos. "
                "Por prudencia, conviene evitar supuestos estrictos de homogeneidad en la seleccion del metodo."
            )
        else:
            interpretation = (
                "No fue posible evaluar de manera confiable la homogeneidad de varianzas con los datos disponibles."
            )
        return VarianceHomogeneityRead(
            method=result["method"],
            statistic=result["statistic"],
            p_value=result["p_value"],
            alpha=result["alpha"],
            classification=result["classification"],
            interpretation=interpretation,
            warnings=result["warnings"],
        )

    def choose_auto_method(
        self,
        *,
        group_count: int,
        normality_by_group: list[NormalityTestResultRead],
        variance_homogeneity: VarianceHomogeneityRead | None,
    ) -> tuple[str, list[str]]:
        warnings = ["method_auto_selected"]
        all_normal = bool(normality_by_group) and all(item.classification == "normal" for item in normality_by_group)
        has_non_normal = any(item.classification == "non_normal" for item in normality_by_group)
        has_inconclusive = any(item.classification in {"inconclusive", "not_applicable"} for item in normality_by_group)
        if has_non_normal:
            warnings.append("non_normal_distribution")
        if has_inconclusive:
            warnings.append("normality_not_available")
        if variance_homogeneity is not None and variance_homogeneity.classification == "non_homogeneous":
            warnings.append("variance_not_homogeneous")

        if group_count == 2:
            if all_normal and variance_homogeneity is not None and variance_homogeneity.classification == "homogeneous":
                return "t_student_independent", warnings
            if all_normal and variance_homogeneity is not None and variance_homogeneity.classification == "non_homogeneous":
                return "welch_t", warnings
            return "mann_whitney_u", warnings

        if all_normal and variance_homogeneity is not None and variance_homogeneity.classification == "homogeneous":
            return "anova_one_way", warnings
        return "kruskal_wallis", warnings

    def _effect_size_interpretation(self, name: str, value: float | None, magnitude: str) -> str:
        if value is None:
            return "No fue posible calcular un tamano del efecto confiable con los datos disponibles."
        return f"El tamano del efecto ({name}) se interpreta como {magnitude} para esta comparacion inicial."

    def _build_effect_size(self, name: str | None, value: float | None) -> EffectSizeRead | None:
        if name is None:
            return None
        magnitude = classify_effect_size(name, value)
        warnings = ["effect_size_unavailable"] if value is None else []
        return EffectSizeRead(
            name=name,
            value=value,
            magnitude=magnitude,
            interpretation=self._effect_size_interpretation(name, value, magnitude),
            warnings=warnings,
        )

    def _build_not_applicable_result(
        self,
        *,
        form: Form,
        request: GroupComparisonRequest,
        outcome_target: ResolvedOutcomeTarget,
        group_target: ResolvedGroupTarget,
        total_n: int,
        valid_n: int,
        missing_n: int,
        group_count: int,
        groups: list[GroupDescriptiveRead],
        warnings: list[str],
        interpretation: str,
        normality_by_group: list[NormalityTestResultRead],
        variance_homogeneity: VarianceHomogeneityRead | None,
        required_next_steps: list[str],
    ) -> GroupComparisonRunRead:
        result = GroupComparisonResultRead(
            form_id=form.id,
            project_id=form.project_id,
            method_requested=request.method,
            method_used="not_applicable",
            alpha=request.alpha,
            outcome_target=self._to_target_read(outcome_target),
            group_target=self._to_target_read(group_target),
            total_n=total_n,
            valid_n=valid_n,
            missing_n=missing_n,
            group_count=group_count,
            groups=groups,
            statistic=None,
            p_value=None,
            degrees_of_freedom=None,
            classification="not_applicable",
            effect_size=None,
            variance_homogeneity=variance_homogeneity,
            normality_by_group=normality_by_group,
            interpretation=interpretation,
            warnings=list(dict.fromkeys(warnings)),
            required_next_steps=required_next_steps,
            assumptions=[],
        )
        analysis_run = None
        if request.store_result:
            analysis_run = self.store_group_comparison_run(form, request, result)
        return GroupComparisonRunRead(analysis_run_id=analysis_run.id if analysis_run is not None else None, result=result)

    def build_group_comparison_interpretation(
        self,
        *,
        method_used: str,
        classification: str,
        group_count: int,
        group_descriptives: list[GroupDescriptiveRead],
    ) -> str:
        if classification == "not_applicable":
            return (
                "No fue posible ejecutar una comparacion entre grupos con los datos disponibles. "
                "Se recomienda revisar la naturaleza del outcome, la variable de agrupacion y el tamano muestral."
            )
        if classification == "not_statistically_significant":
            return (
                "No se identifico una diferencia estadisticamente significativa entre los grupos comparados, dado que el valor p fue mayor o igual al nivel de significancia establecido. "
                "Por tanto, no se cuenta con evidencia suficiente para afirmar que los grupos difieren en el resultado evaluado dentro de la muestra analizada."
            )
        if group_count > 2 and method_used in {"anova_one_way", "kruskal_wallis"}:
            return (
                "Se identifico una diferencia estadisticamente significativa entre al menos dos de los grupos comparados. "
                "No obstante, esta prueba global no indica por si sola entre que grupos especificos se encuentran las diferencias, por lo que en una fase posterior podrian requerirse comparaciones post hoc."
            )
        if len(group_descriptives) >= 2:
            ordered = sorted(group_descriptives, key=lambda item: item.mean if item.mean is not None else float("-inf"))
            lowest = ordered[0].group_label
            highest = ordered[-1].group_label
            return (
                "Se identifico una diferencia estadisticamente significativa entre los grupos comparados, dado que el valor p fue menor al nivel de significancia establecido. "
                f"A partir de las medias observadas, el grupo {highest} presenta puntuaciones mayores que {lowest}; sin embargo, esta diferencia debe interpretarse dentro del contexto del diseno de investigacion y no como evidencia causal."
            )
        return (
            "Se identifico una diferencia estadisticamente significativa entre los grupos comparados. "
            "El resultado debe interpretarse con prudencia y sin atribuir relaciones causales."
        )

    def build_group_comparison_warnings(
        self,
        *,
        request: GroupComparisonRequest,
        form: Form,
        total_n: int,
        valid_n: int,
        missing_n: int,
        outcome_target: ResolvedOutcomeTarget,
        group_target: ResolvedGroupTarget,
        groups: dict[str, pd.Series],
        normality_by_group: list[NormalityTestResultRead],
        variance_homogeneity: VarianceHomogeneityRead | None,
        effect_size: EffectSizeRead | None,
        initial_warnings: list[str],
        method_used: str,
    ) -> list[str]:
        warnings = list(initial_warnings)
        if not request.include_discarded and self.normality_service._has_discarded_responses(form):
            warnings.append("discarded_responses_excluded")
        if request.method != "auto":
            warnings.append("method_forced")
        if missing_n > 0:
            warnings.extend(["pairwise_deletion_used", "missing_values_present"])
        if total_n > 0 and (missing_n / total_n) * 100 >= 20:
            warnings.append("high_missingness")
        if valid_n < 30 and valid_n > 0:
            warnings.append("low_power_small_sample")
        if not outcome_target.numeric:
            warnings.append("outcome_non_numeric")
        if not group_target.categorical:
            warnings.append("grouping_non_categorical")
        if len(groups) < 2:
            warnings.append("only_one_group")
        if len(groups) > 20:
            warnings.append("too_many_groups")
        if any(series.dropna().shape[0] < 3 for series in groups.values()):
            warnings.append("group_with_low_n")
        if detect_outliers_by_group(groups):
            warnings.append("outliers_possible")
        if any(item.classification == "non_normal" for item in normality_by_group):
            warnings.append("non_normal_distribution")
        if any(item.classification in {"inconclusive", "not_applicable"} for item in normality_by_group):
            warnings.append("normality_not_available")
        if variance_homogeneity is not None and variance_homogeneity.classification == "non_homogeneous":
            warnings.append("variance_not_homogeneous")
        if effect_size is not None and effect_size.value is None:
            warnings.append("effect_size_unavailable")
        if method_used in {"anova_one_way", "kruskal_wallis"}:
            warnings.append("posthoc_required")
        return list(dict.fromkeys(warnings))

    def _build_assumptions(self, method_used: str) -> list[str]:
        if method_used == "t_student_independent":
            return [
                "independent_groups",
                "numeric_outcome",
                "categorical_group",
                "group_normality_compatible",
                "homogeneous_variances",
            ]
        if method_used == "welch_t":
            return [
                "independent_groups",
                "numeric_outcome",
                "categorical_group",
                "group_normality_compatible",
            ]
        if method_used == "mann_whitney_u":
            return [
                "independent_groups",
                "ordinal_or_non_normal_outcome",
                "categorical_group",
            ]
        if method_used == "anova_one_way":
            return [
                "independent_groups",
                "numeric_outcome",
                "categorical_group",
                "group_normality_compatible",
                "homogeneous_variances",
            ]
        if method_used == "kruskal_wallis":
            return [
                "independent_groups",
                "ordinal_or_non_normal_outcome",
                "categorical_group",
            ]
        return []

    def _run_statistical_method(
        self,
        *,
        method_used: str,
        groups: dict[str, pd.Series],
        alpha: float,
        decimals: int,
    ) -> dict:
        ordered_keys = list(groups.keys())
        if method_used == "t_student_independent":
            return independent_t_test(groups[ordered_keys[0]], groups[ordered_keys[1]], alpha=alpha, decimals=decimals)
        if method_used == "welch_t":
            return welch_t_test(groups[ordered_keys[0]], groups[ordered_keys[1]], alpha=alpha, decimals=decimals)
        if method_used == "mann_whitney_u":
            return mann_whitney_u_test(groups[ordered_keys[0]], groups[ordered_keys[1]], alpha=alpha, decimals=decimals)
        if method_used == "anova_one_way":
            return one_way_anova(groups, alpha=alpha, decimals=decimals)
        if method_used == "kruskal_wallis":
            return kruskal_wallis_test(groups, alpha=alpha, decimals=decimals)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported group comparison method")

    def store_group_comparison_run(
        self,
        form: Form,
        request: GroupComparisonRequest,
        result: GroupComparisonResultRead,
    ) -> AnalysisRun:
        analysis_run = AnalysisRun(
            project_id=form.project_id,
            form_id=form.id,
            analysis_type="group_comparison",
            status="completed",
            params_json=request.model_dump(),
            result_json={
                "method_used": result.method_used,
                "valid_n": result.valid_n,
                "group_count": result.group_count,
                "statistic": result.statistic,
                "p_value": result.p_value,
                "classification": result.classification,
            },
        )
        self.db.add(analysis_run)
        self.db.commit()
        self.db.refresh(analysis_run)
        return analysis_run

    def get_comparison_options(self, form_id: str, *, include_discarded: bool = False) -> GroupComparisonOptionsRead:
        form, dataframe, mapping = self._get_context(form_id, include_discarded=include_discarded)
        outcomes: list[ComparisonTargetRead] = []
        groups: list[ComparisonTargetRead] = []

        for question in self.normality_service._active_questions(form):
            if self.normality_service._question_series(question, dataframe, mapping) is not None:
                outcomes.append(ComparisonTargetRead(target_type="question", target_id=question.id, label=question.label))
            if self._question_supports_grouping(question):
                groups.append(ComparisonTargetRead(target_type="question", target_id=question.id, label=question.label))

        for instrument in self.normality_service._active_instruments(form):
            scored_questions = [question for question in self.normality_service._active_questions(form) if question.instrument_id == instrument.id and question.is_scored]
            if scored_questions:
                outcomes.append(ComparisonTargetRead(target_type="instrument", target_id=instrument.id, label=instrument.name))
            for dimension in self.normality_service._active_dimensions(instrument):
                dimension_questions = [question for question in scored_questions if question.dimension_id == dimension.id]
                if dimension_questions:
                    outcomes.append(ComparisonTargetRead(target_type="dimension", target_id=dimension.id, label=dimension.name))

        for variable in self.normality_service._active_project_variables(form):
            series, numeric_count = self.normality_service._project_variable_series(
                variable,
                form,
                dataframe,
                mapping,
                aggregation="mean",
            )
            if series is not None and numeric_count > 0:
                outcomes.append(ComparisonTargetRead(target_type="project_variable", target_id=variable.id, label=variable.name))
            label_series, value_series = self._project_variable_group_data(variable, form, dataframe, mapping)
            if label_series is not None and value_series is not None:
                groups.append(ComparisonTargetRead(target_type="project_variable", target_id=variable.id, label=variable.name))

        seen_outcomes: set[tuple[str, str]] = set()
        unique_outcomes: list[ComparisonTargetRead] = []
        for item in outcomes:
            key = (item.target_type, item.target_id)
            if key not in seen_outcomes:
                seen_outcomes.add(key)
                unique_outcomes.append(item)

        seen_groups: set[tuple[str, str]] = set()
        unique_groups: list[ComparisonTargetRead] = []
        for item in groups:
            key = (item.target_type, item.target_id)
            if key not in seen_groups:
                seen_groups.add(key)
                unique_groups.append(item)

        return GroupComparisonOptionsRead(outcomes=unique_outcomes, groups=unique_groups)

    def run_group_comparison(self, form_id: str, request: GroupComparisonRequest) -> GroupComparisonRunRead:
        form, dataframe, mapping = self._get_context(form_id, include_discarded=request.include_discarded)
        outcome_target = self.resolve_outcome_target(
            form,
            dataframe,
            mapping,
            request.outcome,
            score_aggregation=request.score_aggregation,
        )
        group_target = self.resolve_group_target(form, dataframe, mapping, request.group)

        raw_frame = clean_groups(
            outcome_target.series if outcome_target.series is not None else pd.Series(dtype="float"),
            group_target.value_series if group_target.value_series is not None else pd.Series(dtype="object"),
        )
        raw_frame["group_label"] = group_target.label_series if group_target.label_series is not None else None

        total_n = len(dataframe)
        valid_group_frame = raw_frame[raw_frame["group"].notna()].copy()
        valid_group_frame["group"] = valid_group_frame["group"].astype(str)
        valid_group_frame["group_label"] = valid_group_frame["group_label"].astype(str)
        paired_frame = valid_group_frame.dropna(subset=["outcome"]).copy()

        valid_n = len(paired_frame)
        missing_n = total_n - valid_n
        group_total_counts = {
            str(group_value): int(count)
            for group_value, count in valid_group_frame.groupby("group").size().to_dict().items()
        }
        group_labels = {
            str(group_value): str(subset["group_label"].iloc[0])
            for group_value, subset in valid_group_frame.groupby("group")
        }
        groups = {
            str(group_value): pd.to_numeric(subset["outcome"], errors="coerce").dropna()
            for group_value, subset in paired_frame.groupby("group")
        }
        group_descriptives = [
            GroupDescriptiveRead(**item)
            for item in build_group_descriptives(
                groups,
                group_labels=group_labels,
                total_counts=group_total_counts,
                decimals=request.decimals,
            )
        ]
        group_count = len(groups)

        normality_by_group = (
            self.get_normality_by_group(
                groups,
                group_labels,
                outcome_label=outcome_target.label,
                alpha=request.alpha,
                decimals=request.decimals,
            )
            if outcome_target.numeric
            else []
        )
        variance_homogeneity = (
            self.get_variance_homogeneity(groups, alpha=request.alpha, decimals=request.decimals)
            if outcome_target.numeric and group_count >= 2
            else None
        )

        initial_warnings: list[str] = []
        required_next_steps: list[str] = []

        if not outcome_target.numeric:
            return self._build_not_applicable_result(
                form=form,
                request=request,
                outcome_target=outcome_target,
                group_target=group_target,
                total_n=total_n,
                valid_n=valid_n,
                missing_n=missing_n,
                group_count=group_count,
                groups=group_descriptives,
                warnings=["outcome_non_numeric"],
                interpretation="No fue posible ejecutar la comparacion porque el outcome no es numerico ni puntuable.",
                normality_by_group=normality_by_group,
                variance_homogeneity=variance_homogeneity,
                required_next_steps=["Seleccionar un outcome numerico o puntuable para la comparacion."],
            )

        if not group_target.categorical:
            return self._build_not_applicable_result(
                form=form,
                request=request,
                outcome_target=outcome_target,
                group_target=group_target,
                total_n=total_n,
                valid_n=valid_n,
                missing_n=missing_n,
                group_count=group_count,
                groups=group_descriptives,
                warnings=["grouping_non_categorical"],
                interpretation="No fue posible ejecutar la comparacion porque la variable de agrupacion no es categorica.",
                normality_by_group=normality_by_group,
                variance_homogeneity=variance_homogeneity,
                required_next_steps=["Seleccionar una variable de agrupacion categorica."],
            )

        if valid_n < 3:
            return self._build_not_applicable_result(
                form=form,
                request=request,
                outcome_target=outcome_target,
                group_target=group_target,
                total_n=total_n,
                valid_n=valid_n,
                missing_n=missing_n,
                group_count=group_count,
                groups=group_descriptives,
                warnings=["insufficient_n"],
                interpretation="No fue posible ejecutar la comparacion porque no hay casos validos suficientes.",
                normality_by_group=normality_by_group,
                variance_homogeneity=variance_homogeneity,
                required_next_steps=["Recolectar mas observaciones validas antes de comparar grupos."],
            )

        if group_count < 2:
            return self._build_not_applicable_result(
                form=form,
                request=request,
                outcome_target=outcome_target,
                group_target=group_target,
                total_n=total_n,
                valid_n=valid_n,
                missing_n=missing_n,
                group_count=group_count,
                groups=group_descriptives,
                warnings=["only_one_group"],
                interpretation="No fue posible ejecutar la comparacion porque solo se detecto un grupo valido.",
                normality_by_group=normality_by_group,
                variance_homogeneity=variance_homogeneity,
                required_next_steps=["Verificar la variable de agrupacion o aumentar la diversidad de grupos."],
            )

        if paired_frame["outcome"].nunique(dropna=True) <= 1:
            return self._build_not_applicable_result(
                form=form,
                request=request,
                outcome_target=outcome_target,
                group_target=group_target,
                total_n=total_n,
                valid_n=valid_n,
                missing_n=missing_n,
                group_count=group_count,
                groups=group_descriptives,
                warnings=["constant_values"],
                interpretation="No fue posible ejecutar la comparacion porque el outcome no presenta variacion entre los casos validos.",
                normality_by_group=normality_by_group,
                variance_homogeneity=variance_homogeneity,
                required_next_steps=["Revisar la codificacion del outcome o seleccionar una medida con variacion."],
            )

        method_used = request.method
        if request.method == "auto":
            method_used, auto_warnings = self.choose_auto_method(
                group_count=group_count,
                normality_by_group=normality_by_group,
                variance_homogeneity=variance_homogeneity,
            )
            initial_warnings.extend(auto_warnings)

        if group_count > 2 and method_used in {"t_student_independent", "welch_t", "mann_whitney_u"}:
            return self._build_not_applicable_result(
                form=form,
                request=request,
                outcome_target=outcome_target,
                group_target=group_target,
                total_n=total_n,
                valid_n=valid_n,
                missing_n=missing_n,
                group_count=group_count,
                groups=group_descriptives,
                warnings=[*initial_warnings, "too_many_groups"],
                interpretation="El metodo solicitado no es adecuado para una agrupacion con mas de dos grupos.",
                normality_by_group=normality_by_group,
                variance_homogeneity=variance_homogeneity,
                required_next_steps=["Usar ANOVA o Kruskal-Wallis, o reducir la agrupacion a dos grupos."],
            )

        if group_count == 2 and method_used in {"anova_one_way", "kruskal_wallis"} and request.method != "auto":
            initial_warnings.append("method_forced")

        test_result = self._run_statistical_method(
            method_used=method_used,
            groups=groups,
            alpha=request.alpha,
            decimals=request.decimals,
        )
        effect_size = self._build_effect_size(test_result.get("effect_size_name"), test_result.get("effect_size_value"))

        warnings = self.build_group_comparison_warnings(
            request=request,
            form=form,
            total_n=total_n,
            valid_n=valid_n,
            missing_n=missing_n,
            outcome_target=outcome_target,
            group_target=group_target,
            groups=groups,
            normality_by_group=normality_by_group,
            variance_homogeneity=variance_homogeneity,
            effect_size=effect_size,
            initial_warnings=[*initial_warnings, *([] if variance_homogeneity is None else variance_homogeneity.warnings)],
            method_used=method_used,
        )

        if method_used in {"anova_one_way", "kruskal_wallis"} and test_result["classification"] == "statistically_significant" and group_count > 2:
            required_next_steps.append("Ejecutar comparaciones post hoc en una fase posterior.")

        result = GroupComparisonResultRead(
            form_id=form.id,
            project_id=form.project_id,
            method_requested=request.method,
            method_used=test_result["method_used"],
            alpha=request.alpha,
            outcome_target=self._to_target_read(outcome_target),
            group_target=self._to_target_read(group_target),
            total_n=total_n,
            valid_n=valid_n,
            missing_n=missing_n,
            group_count=group_count,
            groups=group_descriptives,
            statistic=test_result["statistic"],
            p_value=test_result["p_value"],
            degrees_of_freedom=test_result["degrees_of_freedom"],
            classification=test_result["classification"],
            effect_size=effect_size,
            variance_homogeneity=variance_homogeneity,
            normality_by_group=normality_by_group,
            interpretation=self.build_group_comparison_interpretation(
                method_used=test_result["method_used"],
                classification=test_result["classification"],
                group_count=group_count,
                group_descriptives=group_descriptives,
            ),
            warnings=warnings,
            required_next_steps=required_next_steps,
            assumptions=self._build_assumptions(test_result["method_used"]),
        )

        analysis_run = None
        if request.store_result:
            analysis_run = self.store_group_comparison_run(form, request, result)
        return GroupComparisonRunRead(analysis_run_id=analysis_run.id if analysis_run is not None else None, result=result)
