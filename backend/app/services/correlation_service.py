from dataclasses import dataclass

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.form import Form
from app.models.form_instrument import FormInstrument
from app.schemas.correlation import (
    CorrelationMatrixCellRead,
    CorrelationMatrixRead,
    CorrelationMatrixRequest,
    CorrelationRequest,
    CorrelationResultRead,
    CorrelationRunRead,
    CorrelationTargetInput,
    CorrelationTargetRead,
)
from app.schemas.normality import NormalityTestResultRead
from app.services.normality_service import NormalityService
from app.statistics.correlation_engine import (
    build_pair_diagnostics,
    correlation_magnitude_label,
    is_dichotomous,
    run_correlation,
)


@dataclass
class ResolvedCorrelationTarget:
    target_type: str
    target_id: str
    label: str
    measurement_level: str
    series: pd.Series | None
    normality_result: NormalityTestResultRead | None
    numeric: bool
    is_dichotomous: bool = False


class CorrelationService:
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

    def resolve_question_series(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        question_id: str,
        request_method: str,
        alpha: float,
        include_discarded: bool,
    ) -> ResolvedCorrelationTarget:
        question = self.normality_service._get_question_or_404(form, question_id)
        series = self.normality_service._question_series(question, dataframe, mapping)
        normality_result = (
            self.normality_service.get_question_normality(
                form.id,
                question.id,
                method=request_method,
                alpha=alpha,
                decimals=3,
                include_discarded=include_discarded,
            )
            if series is not None
            else None
        )
        return ResolvedCorrelationTarget(
            target_type="question",
            target_id=question.id,
            label=question.label,
            measurement_level=question.measurement_level,
            series=series,
            normality_result=normality_result,
            numeric=series is not None,
            is_dichotomous=(
                question.question_type == "boolean"
                or (series is not None and is_dichotomous(series))
            ),
        )

    def resolve_dimension_series(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        dimension_id: str,
        score_aggregation: str,
        request_method: str,
        alpha: float,
        include_discarded: bool,
    ) -> ResolvedCorrelationTarget:
        dimension = self.normality_service._get_dimension_or_404(form, dimension_id)
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
        normality_result = next(
            (
                item
                for item in self.normality_service.get_dimension_normality_results(
                    form.id,
                    method=request_method,
                    alpha=alpha,
                    decimals=3,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                )
                if item.target_id == dimension.id
            ),
            None,
        )
        return ResolvedCorrelationTarget(
            target_type="dimension",
            target_id=dimension.id,
            label=dimension.name,
            measurement_level="interval",
            series=series,
            normality_result=normality_result,
            numeric=series is not None and scored_count > 0,
        )

    def resolve_instrument_series(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        instrument_id: str,
        score_aggregation: str,
        request_method: str,
        alpha: float,
        include_discarded: bool,
    ) -> ResolvedCorrelationTarget:
        instrument = self.normality_service._get_instrument_or_404(form, instrument_id)
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
        normality_result = next(
            (
                item
                for item in self.normality_service.get_instrument_normality_results(
                    form.id,
                    method=request_method,
                    alpha=alpha,
                    decimals=3,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                )
                if item.target_id == instrument.id
            ),
            None,
        )
        return ResolvedCorrelationTarget(
            target_type="instrument",
            target_id=instrument.id,
            label=instrument.name,
            measurement_level="interval",
            series=series,
            normality_result=normality_result,
            numeric=series is not None and scored_count > 0,
        )

    def resolve_project_variable_series(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        project_variable_id: str,
        score_aggregation: str,
        request_method: str,
        alpha: float,
        include_discarded: bool,
    ) -> ResolvedCorrelationTarget:
        variable = self.normality_service._get_project_variable_or_404(form, project_variable_id)
        series, numeric_count = self.normality_service._project_variable_series(
            variable,
            form,
            dataframe,
            mapping,
            aggregation=score_aggregation,
        )
        normality_result = next(
            (
                item
                for item in self.normality_service.get_project_variable_normality_results(
                    form.id,
                    method=request_method,
                    alpha=alpha,
                    decimals=3,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                )
                if item.target_id == variable.id
            ),
            None,
        )
        return ResolvedCorrelationTarget(
            target_type="project_variable",
            target_id=variable.id,
            label=variable.name,
            measurement_level=variable.measurement_level,
            series=series,
            normality_result=normality_result,
            numeric=series is not None and numeric_count > 0,
            is_dichotomous=(
                variable.measurement_level == "dichotomous"
                or (series is not None and is_dichotomous(series))
            ),
        )

    def resolve_correlation_target(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        target: CorrelationTargetInput,
        *,
        score_aggregation: str,
        request_method: str,
        alpha: float,
        include_discarded: bool,
    ) -> ResolvedCorrelationTarget:
        if target.target_type == "question":
            return self.resolve_question_series(
                form,
                dataframe,
                mapping,
                target.target_id,
                request_method,
                alpha,
                include_discarded,
            )
        if target.target_type == "dimension":
            return self.resolve_dimension_series(
                form,
                dataframe,
                mapping,
                target.target_id,
                score_aggregation,
                request_method,
                alpha,
                include_discarded,
            )
        if target.target_type == "instrument":
            return self.resolve_instrument_series(
                form,
                dataframe,
                mapping,
                target.target_id,
                score_aggregation,
                request_method,
                alpha,
                include_discarded,
            )
        if target.target_type == "project_variable":
            return self.resolve_project_variable_series(
                form,
                dataframe,
                mapping,
                target.target_id,
                score_aggregation,
                request_method,
                alpha,
                include_discarded,
            )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported correlation target")

    def choose_auto_method(
        self,
        x_target: ResolvedCorrelationTarget,
        y_target: ResolvedCorrelationTarget,
        diagnostics: dict,
    ) -> tuple[str, list[str]]:
        warnings = ["method_auto_selected"]
        # (a) Un lado dicotómico + otro continuo (no ordinal ni dicotómico) -> punto-biserial.
        dichotomous_targets = [t for t in (x_target, y_target) if t.is_dichotomous]
        if len(dichotomous_targets) == 1:
            other = y_target if dichotomous_targets[0] is x_target else x_target
            if not other.is_dichotomous and other.measurement_level != "ordinal":
                warnings.append("dichotomous_continuous_pair")
                return "point_biserial", warnings
        # (b) Alguna variable ordinal: Kendall si hay muchos empates y muestra pequeña
        # (n < 30), condición en la que Kendall es más robusta; Spearman en otro caso.
        if x_target.measurement_level == "ordinal" or y_target.measurement_level == "ordinal":
            warnings.append("ordinal_data")
            if diagnostics.get("many_ties") and diagnostics.get("valid_n", 0) < 30:
                warnings.append("many_ties")
                return "kendall", warnings
            return "spearman", warnings
        x_normality = x_target.normality_result
        y_normality = y_target.normality_result
        if x_normality is None or y_normality is None:
            warnings.append("normality_not_available")
            return "spearman", warnings
        # (d) Ambas numéricas, normales, n>=30 y sin outliers extremos -> Pearson.
        if x_normality.classification == "normal" and y_normality.classification == "normal":
            if diagnostics.get("outliers_possible"):
                warnings.append("outliers_possible")
                return "spearman", warnings
            if diagnostics.get("valid_n", 0) < 30:
                warnings.append("small_sample_low_power")
                return "spearman", warnings
            return "pearson", warnings
        if "inconclusive" in {x_normality.classification, y_normality.classification} or "not_applicable" in {
            x_normality.classification,
            y_normality.classification,
        }:
            warnings.append("normality_not_available")
            return "spearman", warnings
        # (e) En otro caso -> Spearman.
        warnings.append("non_normal_distribution")
        return "spearman", warnings

    def build_correlation_interpretation(
        self,
        *,
        coefficient: float | None,
        significance: str,
        magnitude: str,
        direction: str,
    ) -> str:
        if coefficient is None:
            return (
                "No fue posible calcular la correlación con los datos disponibles. "
                "Se recomienda revisar el tamaño muestral, la presencia de valores constantes o la naturaleza de las variables."
            )
        if significance == "not_statistically_significant":
            return (
                "No se identificó una correlación estadísticamente significativa entre las variables analizadas, dado que el valor p fue mayor o igual al nivel de significancia establecido. "
                "Por ello, no se cuenta con evidencia suficiente para afirmar una asociación lineal o monotónica entre ambas variables en la muestra evaluada."
            )
        relation = "positiva" if direction == "positive" else "negativa" if direction == "negative" else "prácticamente nula"
        return (
            f"Se identificó una correlación {relation}, de magnitud {correlation_magnitude_label(magnitude)} y estadísticamente significativa entre las variables analizadas. "
            "Esto indica una asociación estadística entre ambas medidas; sin embargo, el resultado no debe interpretarse como evidencia de causalidad."
        )

    def build_hypotheses(self) -> tuple[str, str]:
        return (
            "H₀: ρ = 0 (no existe correlación entre las variables en la población).",
            "H₁: ρ ≠ 0 (existe correlación entre las variables en la población).",
        )

    def build_method_rationale(
        self,
        method_used: str,
        x_target: ResolvedCorrelationTarget,
        y_target: ResolvedCorrelationTarget,
        diagnostics: dict,
    ) -> str:
        if method_used == "point_biserial":
            return (
                "Se empleó la correlación punto-biserial porque una de las variables es dicotómica "
                "y la otra es cuantitativa continua."
            )
        if method_used == "pearson":
            return (
                "Se utilizó el coeficiente de Pearson porque ambas variables son cuantitativas, "
                "presentaron distribución aproximadamente normal, no se detectaron valores atípicos extremos "
                "y el tamaño muestral fue suficiente (n ≥ 30) para una ruta paramétrica."
            )
        if method_used == "kendall":
            return (
                "Se empleó la Tau de Kendall porque al menos una variable es ordinal, presentó un número "
                "elevado de empates y el tamaño muestral es reducido (n < 30), condiciones ante las cuales "
                "este coeficiente resulta más robusto que el de Spearman."
            )
        # spearman
        reasons: list[str] = []
        if x_target.measurement_level == "ordinal" or y_target.measurement_level == "ordinal":
            reasons.append("al menos una variable se midió en escala ordinal")
        if diagnostics.get("outliers_possible"):
            reasons.append("se detectaron posibles valores atípicos")
        if diagnostics.get("valid_n", 0) < 30:
            reasons.append("el tamaño muestral es reducido (n < 30)")
        if not reasons:
            reasons.append("no se cumplieron de forma convincente los supuestos de una ruta paramétrica (p. ej. normalidad)")
        return (
            "Se empleó la correlación de Spearman porque " + "; ".join(reasons) + "."
        )

    def build_correlation_warnings(
        self,
        x_target: ResolvedCorrelationTarget,
        y_target: ResolvedCorrelationTarget,
        *,
        valid_n: int,
        missing_n: int,
        diagnostics: dict,
        method_requested: str,
        method_used: str,
        initial_warnings: list[str],
    ) -> list[str]:
        warnings = list(initial_warnings)
        if method_requested != "auto":
            warnings.append("method_forced")
        if missing_n > 0:
            warnings.extend(["pairwise_deletion_used", "missing_values_present"])
        total_n = valid_n + missing_n
        if total_n > 0:
            x_missing_percent = round(((x_target.series.isna().sum() if x_target.series is not None else total_n) / total_n) * 100, 3)
            y_missing_percent = round(((y_target.series.isna().sum() if y_target.series is not None else total_n) / total_n) * 100, 3)
            if x_missing_percent >= 20 or y_missing_percent >= 20:
                warnings.append("high_missingness")
        if valid_n < 30 and valid_n > 0:
            warnings.append("low_power_small_sample")
        if diagnostics["many_ties"]:
            warnings.append("many_ties")
        if diagnostics["outliers_possible"]:
            warnings.append("outliers_possible")
        if x_target.measurement_level == "ordinal" or y_target.measurement_level == "ordinal":
            warnings.append("ordinal_data")
        if method_used in {"spearman", "kendall"} and any(
            result is not None and result.classification == "non_normal"
            for result in [x_target.normality_result, y_target.normality_result]
        ):
            warnings.append("non_normal_distribution")
        warnings.append("correlation_not_causation")
        return list(dict.fromkeys(warnings))

    def _to_target_read(self, target: ResolvedCorrelationTarget) -> CorrelationTargetRead:
        return CorrelationTargetRead(
            target_type=target.target_type,
            target_id=target.target_id,
            label=target.label,
        )

    def _store_correlation_run(self, form: Form, params_json: dict, result_json: dict) -> AnalysisRun:
        analysis_run = AnalysisRun(
            project_id=form.project_id,
            form_id=form.id,
            analysis_type="correlation",
            status="completed",
            params_json=params_json,
            result_json=result_json,
        )
        self.db.add(analysis_run)
        self.db.commit()
        self.db.refresh(analysis_run)
        return analysis_run

    def run_pair_correlation(self, form_id: str, request: CorrelationRequest) -> CorrelationRunRead:
        form, dataframe, mapping = self._get_context(form_id, include_discarded=request.include_discarded)
        x_target = self.resolve_correlation_target(
            form,
            dataframe,
            mapping,
            request.x,
            score_aggregation=request.score_aggregation,
            request_method="auto",
            alpha=request.alpha,
            include_discarded=request.include_discarded,
        )
        y_target = self.resolve_correlation_target(
            form,
            dataframe,
            mapping,
            request.y,
            score_aggregation=request.score_aggregation,
            request_method="auto",
            alpha=request.alpha,
            include_discarded=request.include_discarded,
        )

        initial_warnings: list[str] = []
        if not request.include_discarded and self.normality_service._has_discarded_responses(form):
            initial_warnings.append("discarded_responses_excluded")

        null_hypothesis, alternative_hypothesis = self.build_hypotheses()

        if not x_target.numeric or not y_target.numeric or x_target.series is None or y_target.series is None:
            result = CorrelationResultRead(
                form_id=form.id,
                project_id=form.project_id,
                method_requested=request.method,
                method_used="not_applicable",
                alpha=request.alpha,
                x_target=self._to_target_read(x_target),
                y_target=self._to_target_read(y_target),
                valid_n=0,
                missing_n=len(dataframe),
                coefficient=None,
                p_value=None,
                direction="none",
                magnitude="not_applicable",
                significance="not_applicable",
                classification="not_applicable",
                interpretation="No fue posible calcular la correlación con los datos disponibles. Se recomienda revisar el tipo de variable y confirmar que ambos targets sean numéricos o puntuables.",
                null_hypothesis=null_hypothesis,
                alternative_hypothesis=alternative_hypothesis,
                method_justification="No se seleccionó un método de correlación porque al menos una de las variables no es numérica o puntuable.",
                warnings=list(dict.fromkeys([*initial_warnings, "non_numeric", "correlation_not_causation"])),
                normality_context={"x": x_target.normality_result, "y": y_target.normality_result},
                assumptions=[],
            )
            analysis_run = self._store_correlation_run(form, request.model_dump(), {"classification": result.classification}) if request.store_result else None
            return CorrelationRunRead(analysis_run_id=analysis_run.id if analysis_run is not None else None, result=result)

        diagnostics = build_pair_diagnostics(x_target.series, y_target.series)
        method_used = request.method
        if request.method == "auto":
            method_used, auto_warnings = self.choose_auto_method(x_target, y_target, diagnostics)
            initial_warnings.extend(auto_warnings)

        engine_result = run_correlation(
            x_target.series,
            y_target.series,
            method=method_used,
            alpha=request.alpha,
            decimals=request.decimals,
        )
        warnings = self.build_correlation_warnings(
            x_target,
            y_target,
            valid_n=diagnostics["valid_n"],
            missing_n=diagnostics["missing_n"],
            diagnostics=diagnostics,
            method_requested=request.method,
            method_used=engine_result["method_used"],
            initial_warnings=[*initial_warnings, *engine_result["warnings"]],
        )

        result = CorrelationResultRead(
            form_id=form.id,
            project_id=form.project_id,
            method_requested=request.method,
            method_used=engine_result["method_used"],
            alpha=request.alpha,
            x_target=self._to_target_read(x_target),
            y_target=self._to_target_read(y_target),
            valid_n=diagnostics["valid_n"],
            missing_n=diagnostics["missing_n"],
            coefficient=engine_result["coefficient"],
            p_value=engine_result["p_value"],
            direction=engine_result["direction"],
            magnitude=engine_result["magnitude"],
            significance=engine_result["significance"],
            classification=engine_result["classification"],
            interpretation=self.build_correlation_interpretation(
                coefficient=engine_result["coefficient"],
                significance=engine_result["significance"],
                magnitude=engine_result["magnitude"],
                direction=engine_result["direction"],
            ),
            null_hypothesis=null_hypothesis,
            alternative_hypothesis=alternative_hypothesis,
            method_justification=self.build_method_rationale(
                engine_result["method_used"], x_target, y_target, diagnostics
            ),
            warnings=warnings,
            normality_context={"x": x_target.normality_result, "y": y_target.normality_result},
            assumptions=engine_result["assumptions"],
        )
        analysis_run = None
        if request.store_result:
            analysis_run = self._store_correlation_run(
                form,
                request.model_dump(),
                {
                    "method_used": result.method_used,
                    "valid_n": result.valid_n,
                    "coefficient": result.coefficient,
                    "p_value": result.p_value,
                    "classification": result.classification,
                },
            )
        return CorrelationRunRead(
            analysis_run_id=analysis_run.id if analysis_run is not None else None,
            result=result,
        )

    def _diagonal_cell(self, target: ResolvedCorrelationTarget, total_n: int) -> CorrelationMatrixCellRead:
        valid_n = int(pd.to_numeric(target.series, errors="coerce").dropna().shape[0]) if target.series is not None else 0
        return CorrelationMatrixCellRead(
            row_target_id=target.target_id,
            column_target_id=target.target_id,
            row_label=target.label,
            column_label=target.label,
            method_used="identity",
            valid_n=min(valid_n, total_n),
            coefficient=1.0 if target.numeric and valid_n > 0 else None,
            p_value=None,
            magnitude="very_strong" if target.numeric and valid_n > 0 else "not_applicable",
            significance="not_applicable",
            warnings=["correlation_not_causation"] if target.numeric and valid_n > 0 else ["non_numeric", "correlation_not_causation"],
        )

    def run_correlation_matrix(
        self,
        form_id: str,
        request: CorrelationMatrixRequest,
    ) -> CorrelationMatrixRead:
        form, dataframe, mapping = self._get_context(form_id, include_discarded=request.include_discarded)
        resolved_targets = [
            self.resolve_correlation_target(
                form,
                dataframe,
                mapping,
                target,
                score_aggregation=request.score_aggregation,
                request_method="auto",
                alpha=request.alpha,
                include_discarded=request.include_discarded,
            )
            for target in request.targets
        ]
        cells: list[CorrelationMatrixCellRead] = []
        matrix_warnings: list[str] = []

        for row_index, row_target in enumerate(resolved_targets):
            for column_index, column_target in enumerate(resolved_targets):
                if row_index == column_index:
                    cells.append(self._diagonal_cell(row_target, len(dataframe)))
                    continue
                pair_request = CorrelationRequest(
                    x=CorrelationTargetInput(target_type=row_target.target_type, target_id=row_target.target_id),
                    y=CorrelationTargetInput(target_type=column_target.target_type, target_id=column_target.target_id),
                    method=request.method,
                    alpha=request.alpha,
                    decimals=request.decimals,
                    include_discarded=request.include_discarded,
                    score_aggregation=request.score_aggregation,
                    store_result=False,
                )
                pair_result = self.run_pair_correlation(form_id, pair_request).result
                matrix_warnings.extend(pair_result.warnings)
                cells.append(
                    CorrelationMatrixCellRead(
                        row_target_id=row_target.target_id,
                        column_target_id=column_target.target_id,
                        row_label=row_target.label,
                        column_label=column_target.label,
                        method_used=pair_result.method_used,
                        valid_n=pair_result.valid_n,
                        coefficient=pair_result.coefficient,
                        p_value=pair_result.p_value,
                        magnitude=pair_result.magnitude,
                        significance=pair_result.significance,
                        warnings=pair_result.warnings,
                    )
                )

        analysis_run = None
        if request.store_result:
            analysis_run = self._store_correlation_run(
                form,
                request.model_dump(),
                {
                    "target_count": len(resolved_targets),
                    "cell_count": len(cells),
                    "method_requested": request.method,
                },
            )
        return CorrelationMatrixRead(
            form_id=form.id,
            project_id=form.project_id,
            method_requested=request.method,
            alpha=request.alpha,
            targets=[self._to_target_read(target) for target in resolved_targets],
            cells=cells,
            warnings=list(dict.fromkeys(matrix_warnings)),
            analysis_run_id=analysis_run.id if analysis_run is not None else None,
        )

    def get_instrument_dimension_matrix(
        self,
        form_id: str,
        instrument_id: str,
        *,
        method: str,
        alpha: float,
        decimals: int,
        include_discarded: bool,
        score_aggregation: str,
    ) -> CorrelationMatrixRead:
        form, _, _ = self._get_context(form_id, include_discarded=include_discarded)
        instrument: FormInstrument = self.normality_service._get_instrument_or_404(form, instrument_id)
        targets = [
            CorrelationTargetInput(target_type="dimension", target_id=dimension.id, label=dimension.name)
            for dimension in self.normality_service._active_dimensions(instrument)
        ]
        return self.run_correlation_matrix(
            form_id,
            CorrelationMatrixRequest(
                targets=targets,
                method=method,
                alpha=alpha,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
                store_result=False,
            ),
        )

    def get_instruments_matrix(
        self,
        form_id: str,
        *,
        method: str,
        alpha: float,
        decimals: int,
        include_discarded: bool,
        score_aggregation: str,
    ) -> CorrelationMatrixRead:
        form, _, _ = self._get_context(form_id, include_discarded=include_discarded)
        targets = [
            CorrelationTargetInput(target_type="instrument", target_id=instrument.id, label=instrument.name)
            for instrument in self.normality_service._active_instruments(form)
        ]
        return self.run_correlation_matrix(
            form_id,
            CorrelationMatrixRequest(
                targets=targets,
                method=method,
                alpha=alpha,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
                store_result=False,
            ),
        )

    def get_project_variables_matrix(
        self,
        form_id: str,
        *,
        method: str,
        alpha: float,
        decimals: int,
        include_discarded: bool,
        score_aggregation: str,
    ) -> CorrelationMatrixRead:
        form, _, _ = self._get_context(form_id, include_discarded=include_discarded)
        targets = [
            CorrelationTargetInput(target_type="project_variable", target_id=variable.id, label=variable.name)
            for variable in self.normality_service._active_project_variables(form)
        ]
        return self.run_correlation_matrix(
            form_id,
            CorrelationMatrixRequest(
                targets=targets,
                method=method,
                alpha=alpha,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
                store_result=False,
            ),
        )
