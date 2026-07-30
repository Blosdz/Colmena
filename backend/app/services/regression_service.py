from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.form import Form
from app.schemas.correlation import CorrelationTargetRead
from app.schemas.regression import (
    RegressionCoefficientRead,
    RegressionRequest,
    RegressionResultRead,
    RegressionRunRead,
)
from app.services.correlation_service import CorrelationService, ResolvedCorrelationTarget
from app.statistics.regression_engine import linear_regression


class RegressionService:
    def __init__(self, db: Session):
        self.db = db
        self.correlation_service = CorrelationService(db)

    def _to_target_read(self, target: ResolvedCorrelationTarget) -> CorrelationTargetRead:
        return CorrelationTargetRead(
            target_type=target.target_type,
            target_id=target.target_id,
            label=target.label,
        )

    def _store_regression_run(self, form: Form, params_json: dict, result_json: dict) -> AnalysisRun:
        analysis_run = AnalysisRun(
            project_id=form.project_id,
            form_id=form.id,
            analysis_type="regression",
            status="completed",
            params_json=params_json,
            result_json=result_json,
        )
        self.db.add(analysis_run)
        self.db.commit()
        self.db.refresh(analysis_run)
        return analysis_run

    def build_interpretation(self, classification: str, r_squared: float | None) -> str:
        if classification == "not_applicable":
            return (
                "No fue posible ajustar el modelo de regresión con los datos disponibles. "
                "Se recomienda revisar el tamaño muestral y que las variables involucradas sean numéricas o puntuables."
            )
        if classification == "not_statistically_significant":
            return (
                "El modelo de regresión ajustado no resultó estadísticamente significativo en su conjunto, "
                "por lo que no se cuenta con evidencia suficiente de que los predictores expliquen la variable dependiente."
            )
        return (
            f"El modelo de regresión fue estadísticamente significativo y explica aproximadamente "
            f"{round((r_squared or 0) * 100, 1)}% de la varianza de la variable dependiente (R²). "
            "Los coeficientes individuales deben interpretarse según su significancia particular; el resultado no implica causalidad."
        )

    def run_regression(self, form_id: str, request: RegressionRequest) -> RegressionRunRead:
        form, dataframe, mapping = self.correlation_service._get_context(
            form_id, include_discarded=request.include_discarded
        )

        dependent_target = self.correlation_service.resolve_correlation_target(
            form,
            dataframe,
            mapping,
            request.dependent,
            score_aggregation=request.score_aggregation,
            request_method="auto",
            alpha=request.alpha,
            include_discarded=request.include_discarded,
        )
        independent_targets = [
            self.correlation_service.resolve_correlation_target(
                form,
                dataframe,
                mapping,
                target,
                score_aggregation=request.score_aggregation,
                request_method="auto",
                alpha=request.alpha,
                include_discarded=request.include_discarded,
            )
            for target in request.independents
        ]

        null_hypothesis = "H₀: los coeficientes de los predictores son iguales a 0 (no explican la variable dependiente)."
        alternative_hypothesis = "H₁: al menos un coeficiente de los predictores es distinto de 0."

        usable_independents = {
            target.target_id: target.series
            for target in independent_targets
            if target.numeric and target.series is not None
        }
        target_by_id = {target.target_id: target for target in independent_targets}

        if not dependent_target.numeric or dependent_target.series is None or not usable_independents:
            result = RegressionResultRead(
                form_id=form.id,
                project_id=form.project_id,
                dependent_target=self._to_target_read(dependent_target),
                independent_targets=[self._to_target_read(target) for target in independent_targets],
                alpha=request.alpha,
                valid_n=0,
                intercept=None,
                r_squared=None,
                adjusted_r_squared=None,
                f_statistic=None,
                f_p_value=None,
                classification="not_applicable",
                interpretation=self.build_interpretation("not_applicable", None),
                null_hypothesis=null_hypothesis,
                alternative_hypothesis=alternative_hypothesis,
                coefficients=[],
                warnings=["non_numeric_targets"],
            )
            analysis_run = (
                self._store_regression_run(form, request.model_dump(), {"classification": result.classification})
                if request.store_result
                else None
            )
            return RegressionRunRead(analysis_run_id=analysis_run.id if analysis_run is not None else None, result=result)

        engine_result = linear_regression(
            dependent_target.series,
            usable_independents,
            alpha=request.alpha,
            decimals=request.decimals,
        )

        classification = "not_applicable"
        if engine_result["r_squared"] is not None:
            classification = (
                "statistically_significant"
                if engine_result["f_p_value"] is not None and engine_result["f_p_value"] < request.alpha
                else "not_statistically_significant"
            )

        coefficients = [
            RegressionCoefficientRead(
                target_type=target_by_id[item["name"]].target_type,
                target_id=item["name"],
                label=target_by_id[item["name"]].label,
                coefficient=item["coefficient"],
                standard_error=item["standard_error"],
                t_value=item["t_value"],
                p_value=item["p_value"],
                significant=item["significant"],
                ci_lower=item["ci_lower"],
                ci_upper=item["ci_upper"],
            )
            for item in engine_result["coefficients"]
        ]

        result = RegressionResultRead(
            form_id=form.id,
            project_id=form.project_id,
            dependent_target=self._to_target_read(dependent_target),
            independent_targets=[self._to_target_read(target) for target in independent_targets],
            alpha=request.alpha,
            valid_n=engine_result["valid_n"],
            intercept=engine_result["intercept"],
            r_squared=engine_result["r_squared"],
            adjusted_r_squared=engine_result["adjusted_r_squared"],
            f_statistic=engine_result["f_statistic"],
            f_p_value=engine_result["f_p_value"],
            classification=classification,
            interpretation=self.build_interpretation(classification, engine_result["r_squared"]),
            null_hypothesis=null_hypothesis,
            alternative_hypothesis=alternative_hypothesis,
            coefficients=coefficients,
            warnings=list(dict.fromkeys(engine_result["warnings"])),
        )
        analysis_run = None
        if request.store_result:
            analysis_run = self._store_regression_run(
                form,
                request.model_dump(),
                {
                    "valid_n": result.valid_n,
                    "r_squared": result.r_squared,
                    "f_p_value": result.f_p_value,
                    "classification": result.classification,
                },
            )
        return RegressionRunRead(
            analysis_run_id=analysis_run.id if analysis_run is not None else None,
            result=result,
        )
