from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.form import Form
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.project_variable import ProjectVariable
from app.schemas.analysis_orchestrator import (
    AnalysisAssumptionRead,
    AnalysisOptionsRead,
    AnalysisRequestOptions,
    AnalysisResultBlockRead,
    AnalysisSummaryRead,
    AnalysisTargetInput,
    AnalysisTargetRead,
    AnalysisWorkflowRead,
    ApaTableBlockRead,
    ChartBlockRead,
    ExportBlockRead,
    FullScanRequest,
    OrchestratedAnalysisRead,
    OrchestratedAnalysisRequest,
    RecentAnalysisRunRead,
)
from app.schemas.categorical_association import (
    CategoricalAssociationRequest,
    CategoricalAssociationTargetInput,
)
from app.schemas.correlation import CorrelationMatrixRequest, CorrelationRequest, CorrelationTargetInput
from app.schemas.group_comparison import ComparisonTargetInput, GroupComparisonRequest
from app.schemas.statistical_decision import DecisionVariableInput, StatisticalDecisionRequest
from app.services.advanced_scoring_service import AdvancedScoringService
from app.services.categorical_association_service import CategoricalAssociationService
from app.services.correlation_service import CorrelationService
from app.services.descriptive_service import DescriptiveService
from app.services.dataset_service import DatasetService
from app.services.group_comparison_service import GroupComparisonService
from app.services.normality_service import NormalityService
from app.services.statistical_decision_service import StatisticalDecisionService


ANALYSIS_GOALS = [
    "descriptive_summary",
    "correlation",
    "correlation_matrix",
    "group_comparison",
    "categorical_association",
    "full_form_scan",
]


ASSUMPTION_DESCRIPTIONS = {
    "numeric_variables": "Las variables analizadas deben ser numericas o puntuables.",
    "categorical_variables": "Las variables analizadas deben ser categoricas.",
    "normality": "La distribucion deberia ser compatible con normalidad para rutas parametricas.",
    "group_normality_compatible": "Los grupos deberian mostrar distribuciones compatibles con normalidad.",
    "homogeneous_variances": "Las varianzas de los grupos deberian ser compatibles con homogeneidad.",
    "independent_groups": "Los grupos comparados deben ser independientes entre si.",
    "independent_observations": "Las observaciones deben ser independientes.",
    "valid_contingency_table": "La tabla de contingencia debe tener categorias suficientes para ser interpretable.",
    "ordinal_scale": "Las variables ordinales suelen requerir procedimientos no parametricos.",
    "paired_design": "Las mediciones deben estar emparejadas correctamente.",
    "difference_normality": "La distribucion de las diferencias deberia ser compatible con normalidad.",
}


class AnalysisOrchestratorService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)
        self.descriptive_service = DescriptiveService(db)
        self.normality_service = NormalityService(db)
        self.statistical_decision_service = StatisticalDecisionService(db)
        self.correlation_service = CorrelationService(db)
        self.group_comparison_service = GroupComparisonService(db)
        self.categorical_association_service = CategoricalAssociationService(db)
        self.advanced_scoring_service = AdvancedScoringService(db)

    def _default_options(self, options: AnalysisRequestOptions | None) -> AnalysisRequestOptions:
        return options or AnalysisRequestOptions()

    def _get_form(self, form_id: str) -> Form:
        return self.dataset_service._get_form(form_id)

    def _normalize_target(self, target: AnalysisTargetInput) -> AnalysisTargetRead:
        label = target.label or self._resolve_target_label(target)
        return AnalysisTargetRead(
            target_type=target.target_type,
            target_id=target.target_id,
            role=target.role,
            label=label,
        )

    def _resolve_target_label(self, target: AnalysisTargetInput) -> str:
        if target.target_type == "question":
            question = self.dataset_service._get_question(target.target_id)
            return question.label
        if target.target_type == "dimension":
            dimension = self.db.scalar(
                select(FormDimension).where(FormDimension.id == target.target_id, FormDimension.deleted_at.is_(None))
            )
            if dimension is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dimension not found")
            return dimension.name
        if target.target_type == "instrument":
            instrument = self.db.scalar(
                select(FormInstrument).where(FormInstrument.id == target.target_id, FormInstrument.deleted_at.is_(None))
            )
            if instrument is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found")
            return instrument.name
        variable = self.db.scalar(
            select(ProjectVariable).where(ProjectVariable.id == target.target_id, ProjectVariable.deleted_at.is_(None))
        )
        if variable is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project variable not found")
        return variable.name

    def _to_decision_variable(self, target: AnalysisTargetInput) -> DecisionVariableInput:
        payload: dict[str, Any] = {"role": target.role}
        if target.target_type == "question":
            payload["question_id"] = target.target_id
        elif target.target_type == "dimension":
            payload["dimension_id"] = target.target_id
        elif target.target_type == "instrument":
            payload["instrument_id"] = target.target_id
        else:
            payload["project_variable_id"] = target.target_id
        return DecisionVariableInput(**payload)

    def _to_correlation_target(self, target: AnalysisTargetInput) -> CorrelationTargetInput:
        return CorrelationTargetInput(target_type=target.target_type, target_id=target.target_id, label=target.label)

    def _to_comparison_target(self, target: AnalysisTargetInput) -> ComparisonTargetInput:
        return ComparisonTargetInput(target_type=target.target_type, target_id=target.target_id, label=target.label)

    def _to_categorical_target(self, target: AnalysisTargetInput) -> CategoricalAssociationTargetInput:
        if target.target_type not in {"question", "project_variable"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Categorical association only supports question or project_variable targets",
            )
        return CategoricalAssociationTargetInput(target_type=target.target_type, target_id=target.target_id, label=target.label)

    def _get_target_by_role(self, targets: list[AnalysisTargetInput], role: str) -> AnalysisTargetInput:
        target = next((item for item in targets if item.role == role), None)
        if target is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Missing target role: {role}")
        return target

    def _serialize_model(self, value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if isinstance(value, list):
            return [self._serialize_model(item) for item in value]
        if isinstance(value, dict):
            return {key: self._serialize_model(item) for key, item in value.items()}
        return value

    def _status_from(self, warnings: list[str], *, not_applicable: bool = False, failed: bool = False) -> str:
        if failed:
            return "failed"
        if not_applicable:
            return "not_applicable"
        return "completed_with_warnings" if warnings else "completed"

    def _build_assumptions(
        self,
        checked: Iterable[str],
        warnings: list[str],
        failed: Iterable[str] | None = None,
    ) -> list[AnalysisAssumptionRead]:
        failed_set = set(failed or [])
        warning_text = " ".join(warnings).lower()
        items: list[AnalysisAssumptionRead] = []
        for name in dict.fromkeys(checked):
            status_value = "passed"
            if name in failed_set:
                status_value = "failed"
            elif any(token in warning_text for token in [name, name.replace("_", " ")]):
                status_value = "warning"
            items.append(
                AnalysisAssumptionRead(
                    name=name,
                    status=status_value,
                    description=ASSUMPTION_DESCRIPTIONS.get(name, "Supuesto estadistico revisado por el analisis."),
                    evidence=None,
                )
            )
        return items

    def _base_chart_options(self, chart_types: list[str]) -> dict[str, Any]:
        return {
            "can_change_chart_type": True,
            "available_chart_types": chart_types,
            "can_show_percentages": True,
            "can_show_labels": True,
            "can_export_future": True,
        }

    def build_export_blocks(self, form_id: str) -> list[ExportBlockRead]:
        return [
            ExportBlockRead(
                export_type="excel",
                label="Exportar dataset a Excel",
                available_now=True,
                endpoint=f"/api/v1/forms/{form_id}/exports/excel",
                notes=["Disponible en la fase actual para la base tabular del formulario."],
            ),
            ExportBlockRead(
                export_type="apa_table_future",
                label="Exportar tablas APA 7",
                available_now=False,
                endpoint=None,
                notes=["Se habilitara en una fase posterior a partir de los bloques APA sugeridos."],
            ),
            ExportBlockRead(
                export_type="chart_future",
                label="Exportar graficos premium",
                available_now=False,
                endpoint=None,
                notes=["La salida visual editable se habilitara en una fase posterior."],
            ),
            ExportBlockRead(
                export_type="word_future",
                label="Exportar informe Word",
                available_now=False,
                endpoint=None,
                notes=["La generacion de informe academico se habilitara en una fase posterior."],
            ),
        ]

    def _truncate_result_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = dict(payload)
        if "cells" in result and isinstance(result["cells"], list):
            result["cells"] = {"count": len(result["cells"])}
        if "rows" in result and isinstance(result["rows"], list):
            result["rows"] = {"count": len(result["rows"])}
        if "items" in result and isinstance(result["items"], list):
            result["items"] = {"count": len(result["items"])}
        if "results" in result and isinstance(result["results"], list):
            result["results"] = {"count": len(result["results"])}
        return result

    def store_orchestrated_analysis_run(
        self,
        form: Form,
        request_payload: dict[str, Any],
        result: OrchestratedAnalysisRead,
    ) -> AnalysisRun:
        analysis_run = AnalysisRun(
            project_id=form.project_id,
            form_id=form.id,
            analysis_type="orchestrated_analysis",
            status=result.status,
            params_json=request_payload,
            result_json=self._truncate_result_json(
                {
                    "analysis_goal": result.analysis_goal,
                    "status": result.status,
                    "title": result.title,
                    "executive_summary": result.executive_summary,
                    "main_result": result.main_result,
                    "statistical_result": result.statistical_result,
                    "warnings": result.warnings[:10],
                    "apa_table_blocks": [block.model_dump() for block in result.apa_table_blocks],
                    "chart_blocks": [block.model_dump() for block in result.chart_blocks],
                    "raw_results_summary": result.raw_results_summary,
                }
            ),
        )
        self.db.add(analysis_run)
        self.db.commit()
        self.db.refresh(analysis_run)
        return analysis_run

    def _recent_runs(self, form_id: str, limit: int = 5) -> list[RecentAnalysisRunRead]:
        items = list(
            self.db.scalars(
                select(AnalysisRun)
                .where(AnalysisRun.form_id == form_id)
                .order_by(AnalysisRun.created_at.desc())
                .limit(limit)
            ).all()
        )
        return [
            RecentAnalysisRunRead(
                id=item.id,
                analysis_type=item.analysis_type,
                status=item.status,
                created_at=item.created_at,
                result_preview=item.result_json if isinstance(item.result_json, dict) else None,
            )
            for item in items
        ]

    def _target_descriptive_snapshot(
        self,
        form_id: str,
        target: AnalysisTargetInput,
        *,
        include_discarded: bool,
        decimals: int,
        score_aggregation: str,
    ) -> dict[str, Any]:
        if target.target_type == "question":
            return self.descriptive_service.get_question_descriptive(
                form_id,
                target.target_id,
                include_discarded=include_discarded,
                decimals=decimals,
            ).model_dump()
        if target.target_type == "dimension":
            item = next(
                entry
                for entry in self.descriptive_service.get_dimension_descriptives(
                    form_id,
                    include_discarded=include_discarded,
                    decimals=decimals,
                    score_aggregation=score_aggregation,
                )
                if entry.dimension_id == target.target_id
            )
            return item.model_dump()
        if target.target_type == "instrument":
            item = next(
                entry
                for entry in self.descriptive_service.get_instrument_descriptives(
                    form_id,
                    include_discarded=include_discarded,
                    decimals=decimals,
                    score_aggregation=score_aggregation,
                )
                if entry.instrument_id == target.target_id
            )
            return item.model_dump()
        item = next(
            entry
            for entry in self.descriptive_service.get_project_variable_descriptives(
                form_id,
                include_discarded=include_discarded,
                decimals=decimals,
            )
            if entry.variable_id == target.target_id
        )
        return item.model_dump()

    def _target_normality_snapshot(
        self,
        form_id: str,
        target: AnalysisTargetInput,
        *,
        include_discarded: bool,
        decimals: int,
        score_aggregation: str,
        method: str,
        alpha: float,
    ) -> dict[str, Any]:
        if target.target_type == "question":
            return self.normality_service.get_question_normality(
                form_id,
                target.target_id,
                method=method,
                alpha=alpha,
                decimals=decimals,
                include_discarded=include_discarded,
            ).model_dump()
        if target.target_type == "dimension":
            item = next(
                entry
                for entry in self.normality_service.get_dimension_normality_results(
                    form_id,
                    method=method,
                    alpha=alpha,
                    decimals=decimals,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                )
                if entry.target_id == target.target_id
            )
            return item.model_dump()
        if target.target_type == "instrument":
            item = next(
                entry
                for entry in self.normality_service.get_instrument_normality_results(
                    form_id,
                    method=method,
                    alpha=alpha,
                    decimals=decimals,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                )
                if entry.target_id == target.target_id
            )
            return item.model_dump()
        item = next(
            entry
            for entry in self.normality_service.get_project_variable_normality_results(
                form_id,
                method=method,
                alpha=alpha,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            )
            if entry.target_id == target.target_id
        )
        return item.model_dump()

    def _correlation_target_rows(self, targets: list[AnalysisTargetRead], result: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "Variable 1": result["x_target"]["label"],
                "Variable 2": result["y_target"]["label"],
                "n": result["valid_n"],
                "r/rho": result["coefficient"],
                "p": result["p_value"],
                "Magnitud": result["magnitude"],
            }
        ]

    def build_plain_language_explanation(self, analysis_goal: str, result: dict[str, Any]) -> str:
        if analysis_goal == "correlation":
            coefficient = result.get("coefficient")
            if coefficient is None:
                return "En términos simples, no hubo datos suficientes o adecuados para establecer si ambas variables se relacionan."
            if result.get("significance") == "statistically_significant":
                return "En términos simples, los datos muestran que ambas variables se mueven juntas de manera relevante dentro de la muestra. Esto no significa que una cause la otra, sino que están relacionadas."
            return "En términos simples, los datos no muestran una relación suficientemente clara entre ambas variables dentro de la muestra analizada."
        if analysis_goal == "group_comparison":
            if result.get("classification") == "statistically_significant":
                return "En términos simples, los grupos no se comportaron igual en el resultado evaluado. Aun así, la diferencia debe entenderse como estadística y no como una prueba de causalidad."
            return "En términos simples, los grupos evaluados no mostraron diferencias suficientemente claras en el resultado analizado."
        if analysis_goal == "categorical_association":
            if result.get("classification") == "statistically_significant":
                return "En términos simples, la distribución de una variable cambia según las categorías de la otra, pero esto no implica una relación causal."
            return "En términos simples, no se observó una asociación suficientemente clara entre las variables categóricas evaluadas."
        if analysis_goal == "descriptive_summary":
            return "En términos simples, este resumen muestra cuántas respuestas tiene el formulario, qué tan completa está la base y qué tan lista se encuentra para análisis posteriores."
        if analysis_goal == "correlation_matrix":
            return "En términos simples, la matriz resume qué variables parecen relacionarse entre sí dentro del conjunto analizado, sin afirmar causalidad."
        return "En términos simples, el sistema revisó la calidad de los datos y las rutas de análisis que conviene ejecutar después."

    def build_academic_interpretation(self, analysis_goal: str, result: dict[str, Any]) -> str:
        if analysis_goal in {"correlation", "group_comparison", "categorical_association"} and result.get("interpretation"):
            return str(result["interpretation"])
        if analysis_goal == "descriptive_summary":
            return "Se consolidó un resumen descriptivo del formulario, incluyendo calidad de datos, completitud y descriptivos básicos para orientar análisis posteriores."
        if analysis_goal == "correlation_matrix":
            return "Se consolidó una matriz exploratoria de correlaciones entre los targets seleccionados, con el fin de identificar asociaciones potenciales para su interpretación posterior."
        return "Se consolidó un escaneo general del formulario para identificar rutas analíticas factibles y advertencias de calidad de datos."

    def build_result_blocks(
        self,
        *,
        descriptive_payload: Any = None,
        normality_payload: Any = None,
        decision_payload: Any = None,
        correlation_payload: Any = None,
        comparison_payload: Any = None,
        association_payload: Any = None,
        scoring_payload: Any = None,
        quality_payload: Any = None,
        recommendation_payload: Any = None,
    ) -> list[AnalysisResultBlockRead]:
        blocks: list[AnalysisResultBlockRead] = []
        if quality_payload is not None:
            blocks.append(AnalysisResultBlockRead(block_type="quality", title="Calidad de datos", summary="Resumen de completitud y calidad del formulario.", payload=self._serialize_model(quality_payload)))
        if descriptive_payload is not None:
            blocks.append(AnalysisResultBlockRead(block_type="descriptive", title="Descriptivos", summary="Resumen descriptivo de los targets analizados.", payload=self._serialize_model(descriptive_payload)))
        if normality_payload is not None:
            blocks.append(AnalysisResultBlockRead(block_type="normality", title="Normalidad", summary="Evaluación de supuestos de distribución para los targets relevantes.", payload=self._serialize_model(normality_payload)))
        if decision_payload is not None:
            blocks.append(AnalysisResultBlockRead(block_type="decision", title="Decisión estadística", summary="Ruta estadística recomendada por el sistema.", payload=self._serialize_model(decision_payload)))
        if correlation_payload is not None:
            blocks.append(AnalysisResultBlockRead(block_type="correlation", title="Correlación", summary="Resultado correlacional consolidado.", payload=self._serialize_model(correlation_payload)))
        if comparison_payload is not None:
            blocks.append(AnalysisResultBlockRead(block_type="group_comparison", title="Comparación entre grupos", summary="Resultado comparativo consolidado.", payload=self._serialize_model(comparison_payload)))
        if association_payload is not None:
            blocks.append(AnalysisResultBlockRead(block_type="categorical_association", title="Asociación categórica", summary="Resultado inferencial de tabla cruzada.", payload=self._serialize_model(association_payload)))
        if scoring_payload is not None:
            blocks.append(
                AnalysisResultBlockRead(
                    block_type="scoring",
                    title="Scoring avanzado",
                    summary="Resumen de puntajes, baremos y escalas de control configuradas.",
                    payload=self._serialize_model(scoring_payload),
                )
            )
        if recommendation_payload is not None:
            blocks.append(AnalysisResultBlockRead(block_type="recommendation", title="Recomendaciones", summary="Siguientes análisis sugeridos por el sistema.", payload=self._serialize_model(recommendation_payload)))
        return blocks

    def build_apa_table_blocks(
        self,
        analysis_goal: str,
        *,
        title: str,
        source_result: str,
        rows: list[dict[str, Any]],
        columns: list[str],
    ) -> list[ApaTableBlockRead]:
        if not rows:
            return []
        table_type_map = {
            "descriptive_summary": "descriptives",
            "correlation": "correlation",
            "correlation_matrix": "correlation",
            "group_comparison": "group_comparison",
            "categorical_association": "categorical_association",
            "full_form_scan": "descriptives",
            "advanced_scoring": "scoring_summary",
            "score_band_distribution": "score_band_distribution",
            "control_scale_flags": "control_scale_flags",
        }
        return [
            ApaTableBlockRead(
                table_type=table_type_map.get(analysis_goal, "descriptives"),
                suggested_title=title,
                source_result=source_result,
                columns=columns,
                rows=rows,
                notes=["Tabla pendiente de formateo APA 7 en fase futura."],
                ready_for_apa=False,
            )
        ]

    def build_chart_blocks(self, analysis_goal: str, *, x_target: str | None = None, y_target: str | None = None, group_target: str | None = None, data_source: str) -> list[ChartBlockRead]:
        if analysis_goal == "descriptive_summary":
            return [
                ChartBlockRead(chart_type="bar", suggested_title="Frecuencias principales del formulario", x_target=None, y_target=None, group_target=None, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["bar", "grouped_bar", "pie", "donut"])),
                ChartBlockRead(chart_type="histogram", suggested_title="Distribuciones numéricas principales", x_target=None, y_target=None, group_target=None, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["histogram", "boxplot"])),
            ]
        if analysis_goal == "correlation":
            return [
                ChartBlockRead(chart_type="scatter", suggested_title="Relación entre variables seleccionadas", x_target=x_target, y_target=y_target, group_target=None, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["scatter", "heatmap"])),
            ]
        if analysis_goal == "correlation_matrix":
            return [
                ChartBlockRead(chart_type="heatmap", suggested_title="Matriz de correlaciones", x_target=None, y_target=None, group_target=None, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["heatmap", "scatter"])),
            ]
        if analysis_goal == "group_comparison":
            return [
                ChartBlockRead(chart_type="boxplot", suggested_title="Distribución del outcome por grupo", x_target=None, y_target=y_target, group_target=group_target, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["boxplot", "grouped_bar"])),
                ChartBlockRead(chart_type="grouped_bar", suggested_title="Comparación de medias o puntajes por grupo", x_target=None, y_target=y_target, group_target=group_target, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["grouped_bar", "bar"])),
            ]
        if analysis_goal == "categorical_association":
            return [
                ChartBlockRead(chart_type="grouped_bar", suggested_title="Distribución cruzada de categorías", x_target=x_target, y_target=None, group_target=group_target, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["grouped_bar", "mosaic", "bar"])),
                ChartBlockRead(chart_type="mosaic", suggested_title="Mosaico de asociación categórica", x_target=x_target, y_target=y_target, group_target=None, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["mosaic", "grouped_bar"])),
            ]
        return [
            ChartBlockRead(chart_type="bar", suggested_title="Resumen exploratorio del formulario", x_target=None, y_target=None, group_target=None, data_source=data_source, recommended=True, editable_options=self._base_chart_options(["bar", "histogram", "heatmap"])),
        ]

    def build_recommended_next_steps(self, analysis_goal: str, warnings: list[str], specific_steps: list[str] | None = None) -> list[str]:
        steps = list(specific_steps or [])
        if analysis_goal == "descriptive_summary":
            steps.append("Revisar preguntas con mayor porcentaje de datos faltantes antes de pasar a inferencia.")
        elif analysis_goal == "correlation":
            steps.append("Usar este resultado como base para una tabla APA de correlación en la siguiente fase.")
        elif analysis_goal == "correlation_matrix":
            steps.append("Seleccionar las asociaciones más relevantes para interpretación detallada y futura tabla APA.")
        elif analysis_goal == "group_comparison":
            steps.append("Revisar el tamaño del efecto junto con la significancia antes de redactar conclusiones.")
        elif analysis_goal == "categorical_association":
            steps.append("Revisar frecuencias esperadas y tamaño del efecto antes de redactar la conclusión metodológica.")
        else:
            steps.append("Usar el resumen del scan para priorizar el siguiente análisis inferencial del formulario.")
        if "posthoc_required" in warnings:
            steps.append("Ejecutar comparaciones post hoc en una fase posterior.")
        if "expected_counts_low" in warnings:
            steps.append("Interpretar con cautela la asociación categórica por presencia de frecuencias esperadas bajas.")
        return list(dict.fromkeys(steps))

    def build_executive_summary(self, analysis_goal: str, *, method_used: str | None = None, significance: str | None = None, direction: str | None = None, magnitude: str | None = None, not_applicable_reason: str | None = None, overview: dict[str, Any] | None = None) -> str:
        if not_applicable_reason:
            return not_applicable_reason
        if analysis_goal == "descriptive_summary" and overview is not None:
            return (
                f"Se consolidó un resumen descriptivo del formulario con {overview['included_responses']} respuestas incluidas y "
                f"{overview['total_questions']} preguntas activas. El sistema destacó el nivel de completitud y la calidad general de la base."
            )
        if analysis_goal == "correlation":
            significance_text = "estadísticamente significativo" if significance == "statistically_significant" else "no estadísticamente significativo"
            direction_text = "positiva" if direction == "positive" else "negativa" if direction == "negative" else "sin dirección clara"
            return f"Se evaluó la relación entre dos targets y el sistema aplicó {method_used}. El resultado fue {significance_text}, con una relación {direction_text} de magnitud {magnitude}."
        if analysis_goal == "correlation_matrix":
            return "Se consolidó una matriz exploratoria de correlaciones entre los targets seleccionados para identificar asociaciones potenciales relevantes."
        if analysis_goal == "group_comparison":
            significance_text = "estadísticamente significativa" if significance == "statistically_significant" else "no estadísticamente significativa"
            return f"Se comparó un outcome entre grupos y el sistema aplicó {method_used}. El resultado fue {significance_text} según el criterio configurado."
        if analysis_goal == "categorical_association":
            significance_text = "estadísticamente significativa" if significance == "statistically_significant" else "no estadísticamente significativa"
            return f"Se evaluó la asociación entre dos variables categóricas y el sistema aplicó {method_used}. La asociación resultó {significance_text}."
        return "Se ejecutó un escaneo general del formulario para consolidar calidad de datos, descriptivos y rutas analíticas recomendadas."

    def _ensure_targets(self, request: OrchestratedAnalysisRequest, minimum: int = 0) -> None:
        if len(request.targets) < minimum:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Insufficient targets for requested analysis")

    def run_descriptive_summary(self, form: Form, request: OrchestratedAnalysisRequest) -> OrchestratedAnalysisRead:
        options = self._default_options(request.options)
        overview = self.descriptive_service.get_descriptive_overview(form.id, include_discarded=request.include_discarded)
        completeness = self.dataset_service.build_completeness_summary(form.id)
        report = None
        if options.include_descriptives:
            report = self.descriptive_service.get_form_descriptives(
                form.id,
                include_discarded=request.include_discarded,
                decimals=request.decimals,
                score_aggregation=request.score_aggregation,
            )
        warnings = list(dict.fromkeys([*overview.warnings, *["critical_missingness" for item in completeness.items if item.warning_level == "critical"]]))
        status_value = self._status_from(warnings, not_applicable=overview.included_responses == 0)
        apa_rows = [
            {
                "Indicador": "Respuestas incluidas",
                "Valor": overview.included_responses,
            },
            {
                "Indicador": "Preguntas activas",
                "Valor": overview.total_questions,
            },
            {
                "Indicador": "Preguntas numéricas",
                "Valor": overview.numeric_questions,
            },
            {
                "Indicador": "Preguntas categóricas",
                "Valor": overview.categorical_questions,
            },
        ]
        result = OrchestratedAnalysisRead(
            form_id=form.id,
            project_id=form.project_id,
            analysis_goal=request.analysis_goal,
            status=status_value,
            analysis_run_id=None,
            title="Resumen descriptivo guiado del formulario",
            executive_summary=self.build_executive_summary("descriptive_summary", overview=overview.model_dump(), not_applicable_reason="No fue posible generar un resumen descriptivo util porque el formulario no tiene respuestas incluidas." if overview.included_responses == 0 else None),
            what_was_analyzed="Se revisó el formulario completo, incluyendo calidad de datos, completitud y descriptivos generales de las preguntas activas.",
            main_result=f"El formulario cuenta con {overview.included_responses} respuestas incluidas, {overview.total_questions} preguntas activas y {completeness.total_responses} casos evaluados para completitud.",
            statistical_result=f"Missing cells: {overview.missing_overview['missing_cells']} de {overview.missing_overview['total_cells']} ({overview.missing_overview['missing_percent']}%).",
            academic_interpretation=self.build_academic_interpretation("descriptive_summary", {"overview": overview.model_dump()}),
            plain_language_explanation=self.build_plain_language_explanation("descriptive_summary", {"overview": overview.model_dump()}),
            assumptions=[],
            warnings=warnings,
            recommended_next_steps=self.build_recommended_next_steps("descriptive_summary", warnings),
            result_blocks=self.build_result_blocks(
                quality_payload={"overview": overview.model_dump(), "completeness": completeness.model_dump()},
                descriptive_payload=report.model_dump() if report is not None else None,
                recommendation_payload={"available_next_analyses": ["correlation", "group_comparison", "categorical_association"]},
            ),
            apa_table_blocks=self.build_apa_table_blocks(
                "descriptive_summary",
                title="Resumen descriptivo inicial del formulario",
                source_result="descriptive_summary",
                columns=["Indicador", "Valor"],
                rows=apa_rows,
            ),
            chart_blocks=self.build_chart_blocks("descriptive_summary", data_source="descriptive_summary"),
            export_blocks=self.build_export_blocks(form.id),
            raw_results_summary={
                "overview": overview.model_dump(),
                "completeness": {
                    "total_responses": completeness.total_responses,
                    "critical_items": sum(1 for item in completeness.items if item.warning_level == "critical"),
                },
            },
        )
        return result

    def run_correlation_analysis(self, form: Form, request: OrchestratedAnalysisRequest) -> OrchestratedAnalysisRead:
        self._ensure_targets(request, minimum=2)
        x_target = self._get_target_by_role(request.targets, "x")
        y_target = self._get_target_by_role(request.targets, "y")
        options = self._default_options(request.options)

        correlation = self.correlation_service.run_pair_correlation(
            form.id,
            CorrelationRequest(
                x=self._to_correlation_target(x_target),
                y=self._to_correlation_target(y_target),
                method=options.force_method or request.method,
                alpha=request.alpha,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
                store_result=False,
            ),
        ).result
        decision = self.statistical_decision_service.make_decision(
            form.id,
            StatisticalDecisionRequest(
                analysis_goal="correlation",
                variables=[self._to_decision_variable(x_target), self._to_decision_variable(y_target)],
                alpha=request.alpha,
                normality_method="auto",
                score_aggregation=request.score_aggregation,
                include_discarded=request.include_discarded,
                store_result=False,
            ),
        )
        descriptive_payload = None
        if options.include_descriptives:
            descriptive_payload = [
                self._target_descriptive_snapshot(
                    form.id,
                    target,
                    include_discarded=request.include_discarded,
                    decimals=request.decimals,
                    score_aggregation=request.score_aggregation,
                )
                for target in [x_target, y_target]
            ]
        normality_payload = None
        if options.include_normality:
            normality_payload = correlation.normality_context
        warnings = list(dict.fromkeys([*decision.warnings, *correlation.warnings]))
        status_value = self._status_from(warnings, not_applicable=correlation.classification == "not_applicable")
        x_label = self._normalize_target(x_target).label
        y_label = self._normalize_target(y_target).label
        result = OrchestratedAnalysisRead(
            form_id=form.id,
            project_id=form.project_id,
            analysis_goal=request.analysis_goal,
            status=status_value,
            analysis_run_id=None,
            title=f"Analisis guiado de correlacion: {x_label} vs {y_label}",
            executive_summary=self.build_executive_summary(
                "correlation",
                method_used=correlation.method_used,
                significance=correlation.significance,
                direction=correlation.direction,
                magnitude=correlation.magnitude,
                not_applicable_reason="No fue posible ejecutar el análisis solicitado porque una de las variables no cuenta con datos numéricos suficientes." if correlation.classification == "not_applicable" else None,
            ),
            what_was_analyzed=f"Se evaluó la relación entre {x_label} y {y_label} usando el flujo guiado del orquestador.",
            main_result=correlation.interpretation,
            statistical_result=f"Metodo: {correlation.method_used}. Coeficiente: {correlation.coefficient}. p = {correlation.p_value}. n = {correlation.valid_n}.",
            academic_interpretation=self.build_academic_interpretation("correlation", correlation.model_dump()),
            plain_language_explanation=self.build_plain_language_explanation("correlation", correlation.model_dump()),
            assumptions=self._build_assumptions(correlation.assumptions, warnings, decision.assumptions_failed),
            warnings=warnings,
            recommended_next_steps=self.build_recommended_next_steps("correlation", warnings, decision.required_next_steps),
            result_blocks=self.build_result_blocks(
                descriptive_payload=descriptive_payload,
                normality_payload=normality_payload,
                decision_payload=decision.model_dump(),
                correlation_payload=correlation.model_dump(),
            ),
            apa_table_blocks=self.build_apa_table_blocks(
                "correlation",
                title=f"Correlacion entre {x_label} y {y_label}",
                source_result="correlation",
                columns=["Variable 1", "Variable 2", "n", "r/rho", "p", "Magnitud"],
                rows=self._correlation_target_rows([self._normalize_target(x_target), self._normalize_target(y_target)], correlation.model_dump()),
            ),
            chart_blocks=self.build_chart_blocks("correlation", x_target=x_label, y_target=y_label, data_source="correlation"),
            export_blocks=self.build_export_blocks(form.id),
            raw_results_summary={
                "decision": {
                    "recommended_test": decision.recommended_test,
                    "route": decision.route,
                },
                "correlation": {
                    "method_used": correlation.method_used,
                    "valid_n": correlation.valid_n,
                    "coefficient": correlation.coefficient,
                    "p_value": correlation.p_value,
                    "classification": correlation.classification,
                },
            },
        )
        return result

    def run_correlation_matrix_analysis(self, form: Form, request: OrchestratedAnalysisRequest) -> OrchestratedAnalysisRead:
        self._ensure_targets(request, minimum=2)
        options = self._default_options(request.options)
        matrix = self.correlation_service.run_correlation_matrix(
            form.id,
            CorrelationMatrixRequest(
                targets=[self._to_correlation_target(target) for target in request.targets],
                method=options.force_method or request.method,
                alpha=request.alpha,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
                store_result=False,
            ),
        )
        normality_payload = None
        if options.include_normality:
            normality_payload = [
                self._target_normality_snapshot(
                    form.id,
                    target,
                    include_discarded=request.include_discarded,
                    decimals=request.decimals,
                    score_aggregation=request.score_aggregation,
                    method="auto",
                    alpha=request.alpha,
                )
                for target in request.targets
            ]
        significant_pairs = [
            cell for cell in matrix.cells
            if cell.row_target_id != cell.column_target_id and cell.significance == "statistically_significant"
        ]
        warnings = list(dict.fromkeys(matrix.warnings))
        status_value = self._status_from(warnings)
        rows = [
            {
                "Variable 1": cell.row_label,
                "Variable 2": cell.column_label,
                "n": cell.valid_n,
                "r/rho": cell.coefficient,
                "p": cell.p_value,
                "Magnitud": cell.magnitude,
            }
            for cell in matrix.cells
            if cell.row_target_id != cell.column_target_id
        ]
        result = OrchestratedAnalysisRead(
            form_id=form.id,
            project_id=form.project_id,
            analysis_goal=request.analysis_goal,
            status=status_value,
            analysis_run_id=None,
            title="Analisis guiado de matriz de correlaciones",
            executive_summary=self.build_executive_summary("correlation_matrix"),
            what_was_analyzed=f"Se analizó una matriz de correlaciones entre {len(request.targets)} targets seleccionados del formulario.",
            main_result=f"Se generaron {len(matrix.cells)} celdas de correlación, con {len(significant_pairs)} asociaciones significativas fuera de la diagonal.",
            statistical_result=f"Metodo solicitado: {matrix.method_requested}. Pares significativos detectados: {len(significant_pairs)}.",
            academic_interpretation=self.build_academic_interpretation("correlation_matrix", {"significant_pairs": len(significant_pairs)}),
            plain_language_explanation=self.build_plain_language_explanation("correlation_matrix", {"significant_pairs": len(significant_pairs)}),
            assumptions=[],
            warnings=warnings,
            recommended_next_steps=self.build_recommended_next_steps("correlation_matrix", warnings),
            result_blocks=self.build_result_blocks(
                normality_payload=normality_payload,
                correlation_payload=matrix.model_dump(),
                recommendation_payload={"significant_pairs": len(significant_pairs)},
            ),
            apa_table_blocks=self.build_apa_table_blocks(
                "correlation_matrix",
                title="Matriz exploratoria de correlaciones",
                source_result="correlation_matrix",
                columns=["Variable 1", "Variable 2", "n", "r/rho", "p", "Magnitud"],
                rows=rows[: min(len(rows), 20)],
            ),
            chart_blocks=self.build_chart_blocks("correlation_matrix", data_source="correlation_matrix"),
            export_blocks=self.build_export_blocks(form.id),
            raw_results_summary={
                "target_count": len(matrix.targets),
                "cell_count": len(matrix.cells),
                "significant_pairs": len(significant_pairs),
            },
        )
        return result

    def run_group_comparison_analysis(self, form: Form, request: OrchestratedAnalysisRequest) -> OrchestratedAnalysisRead:
        self._ensure_targets(request, minimum=2)
        outcome_target = self._get_target_by_role(request.targets, "outcome")
        group_target = self._get_target_by_role(request.targets, "group")
        options = self._default_options(request.options)

        decision = self.statistical_decision_service.make_decision(
            form.id,
            StatisticalDecisionRequest(
                analysis_goal="comparison_independent_groups",
                variables=[self._to_decision_variable(outcome_target), self._to_decision_variable(group_target)],
                alpha=request.alpha,
                normality_method="auto",
                score_aggregation=request.score_aggregation,
                include_discarded=request.include_discarded,
                store_result=False,
            ),
        )
        comparison = self.group_comparison_service.run_group_comparison(
            form.id,
            GroupComparisonRequest(
                outcome=self._to_comparison_target(outcome_target),
                group=self._to_comparison_target(group_target),
                method=options.force_method or request.method,
                alpha=request.alpha,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
                store_result=False,
            ),
        ).result
        descriptive_payload = comparison.groups if options.include_descriptives else None
        warnings = list(dict.fromkeys([*decision.warnings, *comparison.warnings]))
        status_value = self._status_from(warnings, not_applicable=comparison.classification == "not_applicable")
        outcome_label = self._normalize_target(outcome_target).label
        group_label = self._normalize_target(group_target).label
        apa_rows = [
            {
                "Grupo": item.group_label,
                "n": item.n,
                "Media": item.mean,
                "DE": item.standard_deviation,
                "Mediana": item.median,
            }
            for item in comparison.groups
        ]
        result = OrchestratedAnalysisRead(
            form_id=form.id,
            project_id=form.project_id,
            analysis_goal=request.analysis_goal,
            status=status_value,
            analysis_run_id=None,
            title=f"Analisis guiado de comparación: {outcome_label} por {group_label}",
            executive_summary=self.build_executive_summary(
                "group_comparison",
                method_used=comparison.method_used,
                significance=comparison.classification,
                not_applicable_reason="No fue posible ejecutar la comparación porque el outcome o la agrupación no cumplen los requisitos mínimos." if comparison.classification == "not_applicable" else None,
            ),
            what_was_analyzed=f"Se comparó {outcome_label} según los grupos definidos por {group_label}.",
            main_result=comparison.interpretation,
            statistical_result=f"Metodo: {comparison.method_used}. Estadistico: {comparison.statistic}. p = {comparison.p_value}. n = {comparison.valid_n}.",
            academic_interpretation=self.build_academic_interpretation("group_comparison", comparison.model_dump()),
            plain_language_explanation=self.build_plain_language_explanation("group_comparison", comparison.model_dump()),
            assumptions=self._build_assumptions(comparison.assumptions, warnings),
            warnings=warnings,
            recommended_next_steps=self.build_recommended_next_steps("group_comparison", warnings, comparison.required_next_steps),
            result_blocks=self.build_result_blocks(
                descriptive_payload=descriptive_payload,
                normality_payload=comparison.normality_by_group,
                decision_payload=decision.model_dump(),
                comparison_payload=comparison.model_dump(),
            ),
            apa_table_blocks=self.build_apa_table_blocks(
                "group_comparison",
                title=f"Comparación de {outcome_label} según {group_label}",
                source_result="group_comparison",
                columns=["Grupo", "n", "Media", "DE", "Mediana"],
                rows=apa_rows,
            ),
            chart_blocks=self.build_chart_blocks("group_comparison", y_target=outcome_label, group_target=group_label, data_source="group_comparison"),
            export_blocks=self.build_export_blocks(form.id),
            raw_results_summary={
                "method_used": comparison.method_used,
                "group_count": comparison.group_count,
                "valid_n": comparison.valid_n,
                "p_value": comparison.p_value,
                "classification": comparison.classification,
            },
        )
        return result

    def run_categorical_association_analysis(self, form: Form, request: OrchestratedAnalysisRequest) -> OrchestratedAnalysisRead:
        self._ensure_targets(request, minimum=2)
        row_target = self._get_target_by_role(request.targets, "row")
        column_target = self._get_target_by_role(request.targets, "column")
        options = self._default_options(request.options)
        descriptive_crosstab = None
        if options.include_descriptives and row_target.target_type == "question" and column_target.target_type == "question":
            descriptive_crosstab = self.descriptive_service.get_crosstab(
                form.id,
                row_question_id=row_target.target_id,
                column_question_id=column_target.target_id,
                include_discarded=request.include_discarded,
                decimals=request.decimals,
            )
        association = self.categorical_association_service.run_categorical_association(
            form.id,
            CategoricalAssociationRequest(
                row=self._to_categorical_target(row_target),
                column=self._to_categorical_target(column_target),
                method=options.force_method or request.method,
                alpha=request.alpha,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                store_result=False,
            ),
        ).result
        warnings = list(dict.fromkeys(association.warnings))
        status_value = self._status_from(warnings, not_applicable=association.classification == "not_applicable")
        row_label = self._normalize_target(row_target).label
        column_label = self._normalize_target(column_target).label
        apa_rows = [
            {
                "Fila": cell.row_value,
                "Columna": cell.column_value,
                "Frecuencia": cell.observed,
                "% fila": cell.row_percent,
                "% columna": cell.column_percent,
                "% total": cell.total_percent,
            }
            for cell in association.cells
        ]
        result = OrchestratedAnalysisRead(
            form_id=form.id,
            project_id=form.project_id,
            analysis_goal=request.analysis_goal,
            status=status_value,
            analysis_run_id=None,
            title=f"Analisis guiado de asociación: {row_label} y {column_label}",
            executive_summary=self.build_executive_summary(
                "categorical_association",
                method_used=association.method_used,
                significance=association.classification,
                not_applicable_reason="No fue posible ejecutar la asociación porque alguna variable no es categórica o no tiene categorías suficientes." if association.classification == "not_applicable" else None,
            ),
            what_was_analyzed=f"Se evaluó la asociación categórica entre {row_label} y {column_label}.",
            main_result=association.interpretation,
            statistical_result=f"Metodo: {association.method_used}. Estadistico: {association.statistic}. p = {association.p_value}. n = {association.valid_n}.",
            academic_interpretation=self.build_academic_interpretation("categorical_association", association.model_dump()),
            plain_language_explanation=self.build_plain_language_explanation("categorical_association", association.model_dump()),
            assumptions=self._build_assumptions(association.assumptions, warnings),
            warnings=warnings,
            recommended_next_steps=self.build_recommended_next_steps("categorical_association", warnings, association.required_next_steps),
            result_blocks=self.build_result_blocks(
                descriptive_payload=descriptive_crosstab.model_dump() if descriptive_crosstab is not None else None,
                association_payload=association.model_dump(),
            ),
            apa_table_blocks=self.build_apa_table_blocks(
                "categorical_association",
                title=f"Asociación entre {row_label} y {column_label}",
                source_result="categorical_association",
                columns=["Fila", "Columna", "Frecuencia", "% fila", "% columna", "% total"],
                rows=apa_rows,
            ),
            chart_blocks=self.build_chart_blocks("categorical_association", x_target=row_label, y_target=column_label, group_target=column_label, data_source="categorical_association"),
            export_blocks=self.build_export_blocks(form.id),
            raw_results_summary={
                "method_used": association.method_used,
                "valid_n": association.valid_n,
                "p_value": association.p_value,
                "classification": association.classification,
                "effect_size": association.effect_size.model_dump() if association.effect_size is not None else None,
            },
        )
        return result

    def run_full_form_scan(self, form: Form, request: FullScanRequest) -> OrchestratedAnalysisRead:
        options = self._default_options(request.options)
        overview = self.descriptive_service.get_descriptive_overview(form.id, include_discarded=request.include_discarded)
        completeness = self.dataset_service.build_completeness_summary(form.id)
        analysis_options = self.list_analysis_options(form.id)
        scoring_configs = self.advanced_scoring_service._get_scoring_configs(form.id)
        scoring_results = self.advanced_scoring_service.get_form_score_results(form.id)
        warnings = list(dict.fromkeys([*overview.warnings, *scoring_results.warnings]))
        result_blocks = self.build_result_blocks(
            quality_payload={"overview": overview.model_dump(), "completeness": completeness.model_dump()},
            scoring_payload=scoring_results.model_dump() if (scoring_results.scored_responses or scoring_results.control_flags) else None,
            recommendation_payload={
                "available_targets": analysis_options.available_targets,
                "recommended_workflows": [item.model_dump() for item in analysis_options.recommended_workflows],
            },
        )
        raw_summary: dict[str, Any] = {
            "overview": overview.model_dump(),
            "available_targets": {key: len(value) for key, value in analysis_options.available_targets.items()},
        }
        if scoring_results.scored_responses or scoring_results.control_flags:
            raw_summary["scoring"] = scoring_results.model_dump()

        numeric_targets = analysis_options.available_targets["numeric"][: options.max_targets]
        pairwise_limit = (len(numeric_targets) * (len(numeric_targets) - 1)) // 2
        if len(numeric_targets) >= 2 and pairwise_limit <= options.max_pairwise_tests:
            matrix_request = OrchestratedAnalysisRequest(
                analysis_goal="correlation_matrix",
                targets=[
                    AnalysisTargetInput(target_type=item.target_type, target_id=item.target_id, role="target", label=item.label)
                    for item in numeric_targets
                ],
                method="auto",
                alpha=request.alpha,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
                store_result=False,
                options=AnalysisRequestOptions(
                    max_targets=options.max_targets,
                    max_pairwise_tests=options.max_pairwise_tests,
                    include_normality=False,
                    include_descriptives=False,
                    include_recommendations=True,
                ),
            )
            matrix_result = self.run_correlation_matrix_analysis(form, matrix_request)
            result_blocks.extend(matrix_result.result_blocks)
            raw_summary["correlation_matrix"] = matrix_result.raw_results_summary
        elif len(numeric_targets) >= 2:
            warnings.append("pairwise_limit_reached")
            raw_summary["correlation_matrix"] = {"skipped": True, "reason": "pairwise_limit_reached"}

        if len(analysis_options.available_targets["categorical"]) >= 2:
            result_blocks.append(
                AnalysisResultBlockRead(
                    block_type="recommendation",
                    title="Asociaciones categoricas posibles",
                    summary="El formulario dispone de variables categoricas suficientes para ejecutar asociaciones categoricas puntuales.",
                    payload={"target_count": len(analysis_options.available_targets["categorical"])},
                )
            )
        if analysis_options.available_targets["numeric"] and analysis_options.available_targets["categorical"]:
            result_blocks.append(
                AnalysisResultBlockRead(
                    block_type="recommendation",
                    title="Comparaciones entre grupos posibles",
                    summary="El formulario dispone de outcomes numericos y agrupaciones categoricas potenciales para comparaciones entre grupos.",
                    payload={
                        "outcomes": len(analysis_options.available_targets["numeric"]),
                        "groups": len(analysis_options.available_targets["categorical"]),
                    },
                )
            )
        if scoring_configs and scoring_results.scored_responses == 0:
            result_blocks.append(
                AnalysisResultBlockRead(
                    block_type="recommendation",
                    title="Scoring avanzado pendiente",
                    summary="Existen configuraciones de scoring, pero aun no se han almacenado puntajes suficientes para resumir baremos o escalas de control.",
                    payload={"config_count": len(scoring_configs)},
                )
            )

        apa_table_blocks = self.build_apa_table_blocks(
            "full_form_scan",
            title="Resumen exploratorio inicial del formulario",
            source_result="full_form_scan",
            columns=["Indicador", "Valor"],
            rows=[
                {"Indicador": "Respuestas incluidas", "Valor": overview.included_responses},
                {"Indicador": "Targets numericos", "Valor": len(analysis_options.available_targets["numeric"])},
                {"Indicador": "Targets categoricos", "Valor": len(analysis_options.available_targets["categorical"])},
            ],
        )
        if scoring_results.scored_responses > 0:
            apa_table_blocks.extend(
                self.build_apa_table_blocks(
                    "advanced_scoring",
                    title="Resumen de puntajes configurados",
                    source_result="advanced_scoring",
                    columns=["Indicador", "Valor"],
                    rows=[
                        {"Indicador": "Respuestas puntuadas", "Valor": scoring_results.scored_responses},
                        {"Indicador": "Respuestas validas", "Valor": scoring_results.valid_responses},
                        {"Indicador": "Respuestas con advertencia", "Valor": scoring_results.warning_responses},
                        {"Indicador": "Respuestas invalidas", "Valor": scoring_results.invalid_responses},
                    ],
                )
            )

        chart_blocks = self.build_chart_blocks("full_form_scan", data_source="full_form_scan")
        if scoring_results.scored_responses > 0:
            chart_blocks.extend(
                [
                    ChartBlockRead(
                        chart_type="donut",
                        suggested_title="Distribucion por baremos",
                        x_target=None,
                        y_target=None,
                        group_target=None,
                        data_source="advanced_scoring",
                        recommended=True,
                        editable_options=self._base_chart_options(["donut", "bar", "grouped_bar"]),
                    ),
                    ChartBlockRead(
                        chart_type="bar",
                        suggested_title="Comparacion de niveles interpretativos",
                        x_target=None,
                        y_target="Frecuencia",
                        group_target=None,
                        data_source="advanced_scoring",
                        recommended=True,
                        editable_options=self._base_chart_options(["bar", "horizontal_bar", "donut"]),
                    ),
                ]
            )

        status_value = self._status_from(warnings, not_applicable=overview.included_responses == 0)
        executive_summary = (
            "No fue posible ejecutar un escaneo util porque el formulario no tiene respuestas incluidas."
            if overview.included_responses == 0
            else (
                f"Se consolido un escaneo general del formulario con {overview.included_responses} respuestas incluidas. "
                f"Ademas, el sistema detecto {len(scoring_configs)} configuraciones de scoring y {scoring_results.scored_responses} respuestas con puntajes avanzados calculados."
                if scoring_configs
                else self.build_executive_summary("full_form_scan")
            )
        )
        main_result = (
            f"El formulario tiene {overview.included_responses} respuestas incluidas y rutas disponibles para descriptivos, correlacion, comparacion de grupos y asociacion categorica segun los targets detectados. "
            f"Tambien existen {scoring_results.scored_responses} respuestas con scoring avanzado calculado."
            if scoring_results.scored_responses
            else f"El formulario tiene {overview.included_responses} respuestas incluidas y rutas disponibles para descriptivos, correlacion, comparacion de grupos y asociacion categorica segun los targets detectados."
        )
        result = OrchestratedAnalysisRead(
            form_id=form.id,
            project_id=form.project_id,
            analysis_goal="full_form_scan",
            status=status_value,
            analysis_run_id=None,
            title="Escaneo general guiado del formulario",
            executive_summary=executive_summary,
            what_was_analyzed="Se reviso la calidad general del formulario, su completitud y las rutas analiticas que podrian ejecutarse a continuacion.",
            main_result=main_result,
            statistical_result=f"Targets numericos detectados: {len(analysis_options.available_targets['numeric'])}. Targets categoricos detectados: {len(analysis_options.available_targets['categorical'])}. Respuestas puntuadas: {scoring_results.scored_responses}. Invalidas por control: {scoring_results.invalid_responses}.",
            academic_interpretation=self.build_academic_interpretation("full_form_scan", raw_summary),
            plain_language_explanation=self.build_plain_language_explanation("full_form_scan", raw_summary),
            assumptions=[],
            warnings=warnings,
            recommended_next_steps=self.build_recommended_next_steps("full_form_scan", warnings),
            result_blocks=result_blocks,
            apa_table_blocks=apa_table_blocks,
            chart_blocks=chart_blocks,
            export_blocks=self.build_export_blocks(form.id),
            raw_results_summary=raw_summary,
        )
        return result

    def run_orchestrated_analysis(self, form_id: str, request: OrchestratedAnalysisRequest) -> OrchestratedAnalysisRead:
        form = self._get_form(form_id)
        if request.analysis_goal == "descriptive_summary":
            result = self.run_descriptive_summary(form, request)
        elif request.analysis_goal == "correlation":
            result = self.run_correlation_analysis(form, request)
        elif request.analysis_goal == "correlation_matrix":
            result = self.run_correlation_matrix_analysis(form, request)
        elif request.analysis_goal == "group_comparison":
            result = self.run_group_comparison_analysis(form, request)
        elif request.analysis_goal == "categorical_association":
            result = self.run_categorical_association_analysis(form, request)
        else:
            result = self.run_full_form_scan(
                form,
                FullScanRequest(
                    alpha=request.alpha,
                    decimals=request.decimals,
                    include_discarded=request.include_discarded,
                    score_aggregation=request.score_aggregation,
                    store_result=request.store_result,
                    options=request.options,
                ),
            )
        if request.store_result:
            analysis_run = self.store_orchestrated_analysis_run(form, request.model_dump(), result)
            result.analysis_run_id = analysis_run.id
        return result

    def list_analysis_options(self, form_id: str) -> AnalysisOptionsRead:
        form = self._get_form(form_id)
        comparison_options = self.group_comparison_service.get_comparison_options(form_id)
        categorical_options = self.categorical_association_service.list_categorical_association_options(form_id)

        numeric_targets = [
            AnalysisTargetRead(target_type=item.target_type, target_id=item.target_id, role="target", label=item.label)
            for item in comparison_options.outcomes
        ]
        categorical_targets = [
            AnalysisTargetRead(target_type=item.target_type, target_id=item.target_id, role="target", label=item.label)
            for item in categorical_options.categorical_targets
        ]
        scored_targets = [item for item in numeric_targets if item.target_type in {"dimension", "instrument", "project_variable"} or item.label]

        return AnalysisOptionsRead(
            form_id=form.id,
            goals=ANALYSIS_GOALS,
            available_targets={
                "numeric": numeric_targets,
                "categorical": categorical_targets,
                "scored": scored_targets,
                "all": list({(item.target_type, item.target_id): item for item in [*numeric_targets, *categorical_targets]}.values()),
            },
            recommended_workflows=[
                AnalysisWorkflowRead(analysis_goal="descriptive_summary", title="Resumen descriptivo", description="Ideal para revisar calidad de datos, completitud y estado general del formulario.", required_roles=[]),
                AnalysisWorkflowRead(analysis_goal="correlation", title="Relación entre dos variables", description="Usa dos targets numéricos o puntuados con roles x e y.", required_roles=["x", "y"]),
                AnalysisWorkflowRead(analysis_goal="correlation_matrix", title="Matriz de correlaciones", description="Usa varios targets numéricos o puntuados para un análisis exploratorio conjunto.", required_roles=["target"]),
                AnalysisWorkflowRead(analysis_goal="group_comparison", title="Comparación entre grupos", description="Usa un outcome numérico y una variable categórica de agrupación.", required_roles=["outcome", "group"]),
                AnalysisWorkflowRead(analysis_goal="categorical_association", title="Asociación categórica", description="Usa dos variables categóricas con roles row y column.", required_roles=["row", "column"]),
                AnalysisWorkflowRead(analysis_goal="full_form_scan", title="Escaneo completo", description="Revisa automáticamente qué rutas analíticas son viables en el formulario.", required_roles=[]),
            ],
        )

    def get_analysis_summary(self, form_id: str) -> AnalysisSummaryRead:
        form = self._get_form(form_id)
        overview = self.descriptive_service.get_descriptive_overview(form_id, include_discarded=False)
        completeness = self.dataset_service.build_completeness_summary(form_id)
        options = self.list_analysis_options(form_id)
        critical_items = sum(1 for item in completeness.items if item.warning_level == "critical")
        warnings = list(dict.fromkeys([*overview.warnings, *("critical_missingness" for item in completeness.items if item.warning_level == "critical")]))
        return AnalysisSummaryRead(
            form_id=form.id,
            project_id=form.project_id,
            total_responses=overview.total_responses,
            included_responses=overview.included_responses,
            data_quality={
                "missing_percent": overview.missing_overview["missing_percent"],
                "critical_items": critical_items,
                "total_questions": overview.total_questions,
            },
            available_analyses=options.goals,
            recent_analysis_runs=self._recent_runs(form_id),
            warnings=warnings,
        )
