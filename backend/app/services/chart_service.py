from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.charts.chart_builder import (
    build_bar_chart,
    build_boxplot_chart,
    build_chart_from_categorical_association,
    build_chart_from_correlation,
    build_chart_from_correlation_matrix,
    build_chart_from_descriptives,
    build_chart_from_frequency_table,
    build_chart_from_group_comparison,
    build_chart_from_orchestrated_result,
    build_donut_chart,
    build_grouped_bar_chart,
    build_heatmap_chart,
    build_histogram_chart,
    build_horizontal_bar_chart,
    build_pie_chart,
    build_scatter_chart,
    build_stacked_bar_chart,
)
from app.charts.chart_export import export_chart_specs_json
from app.charts.chart_recommender import chart_alternatives, recommend_chart_types
from app.charts.chart_theme import CHART_THEMES, get_chart_theme
from app.core.config import get_settings
from app.models.analysis_run import AnalysisRun
from app.models.export_artifact import ExportArtifact
from app.models.form import Form
from app.schemas.analysis_orchestrator import AnalysisTargetInput, OrchestratedAnalysisRequest
from app.schemas.categorical_association import CategoricalAssociationRequest, CategoricalAssociationTargetInput
from app.schemas.chart import (
    ChartBatchRead,
    ChartBatchRequest,
    ChartExportRead,
    ChartExportRequest,
    ChartGenerateRequest,
    ChartOptionsRead,
    ChartRecommendationRead,
    ChartSpecRead,
    ChartTargetInput,
    CompatibleChartAnalysisRunRead,
)
from app.schemas.correlation import CorrelationMatrixRequest, CorrelationRequest, CorrelationTargetInput
from app.schemas.group_comparison import ComparisonTargetInput, GroupComparisonRequest
from app.services.advanced_scoring_service import AdvancedScoringService
from app.services.analysis_orchestrator_service import AnalysisOrchestratorService
from app.services.categorical_association_service import CategoricalAssociationService
from app.services.correlation_service import CorrelationService
from app.services.descriptive_service import DescriptiveService
from app.services.group_comparison_service import GroupComparisonService
from app.services.normality_service import NormalityService
from app.statistics.group_comparison_engine import clean_groups


class ChartService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.exports_dir = self.settings.backend_dir / "data" / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.descriptive_service = DescriptiveService(db)
        self.normality_service = NormalityService(db)
        self.correlation_service = CorrelationService(db)
        self.group_comparison_service = GroupComparisonService(db)
        self.categorical_association_service = CategoricalAssociationService(db)
        self.advanced_scoring_service = AdvancedScoringService(db)
        self.analysis_orchestrator_service = AnalysisOrchestratorService(db)

    def _chart_id(self) -> str:
        return str(uuid.uuid4())

    def _get_form(self, form_id: str) -> Form:
        return self.descriptive_service.dataset_service._get_form(form_id)

    def _get_analysis_run(self, form_id: str, analysis_run_id: str) -> AnalysisRun:
        analysis_run = self.db.scalar(
            select(AnalysisRun).where(AnalysisRun.id == analysis_run_id, AnalysisRun.form_id == form_id)
        )
        if analysis_run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AnalysisRun not found for form")
        return analysis_run

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

    def _theme(self, theme_name: str) -> dict[str, Any]:
        return get_chart_theme(theme_name)

    def _build_targets(self, targets: list[ChartTargetInput] | None) -> list[ChartTargetInput]:
        return targets or []

    def _default_warning_chart(
        self,
        *,
        form: Form,
        chart_type: str,
        title: str,
        theme_name: str,
        source_type: str,
        source_reference: str | None,
        targets: list[ChartTargetInput],
        warning: str,
        description: str,
    ) -> ChartSpecRead:
        theme = self._theme(theme_name)
        builder = build_bar_chart if chart_type in {"bar", "horizontal_bar"} else build_histogram_chart
        if chart_type in {"bar", "horizontal_bar"}:
            return builder(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=title,
                source_type=source_type,
                source_reference=source_reference,
                targets=targets,
                labels=[],
                values=[],
                text=[],
                theme=theme,
                warnings=[warning],
                description=description,
            )
        return builder(
            chart_id=self._chart_id(),
            form_id=form.id,
            project_id=form.project_id,
            title=title,
            source_type=source_type,
            source_reference=source_reference,
            targets=targets,
            values=[],
            theme=theme,
            warnings=[warning],
            description=description,
            xaxis_title="Valor",
        )

    def _categorical_labels(self, values: list[str]) -> list[str]:
        return [str(item) for item in values]

    def _get_target_by_role(self, targets: list[ChartTargetInput], role: str) -> ChartTargetInput:
        target = next((item for item in targets if item.role == role), None)
        if target is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Missing chart target role: {role}")
        return target

    def _series_for_numeric_target(
        self,
        form_id: str,
        target: ChartTargetInput,
        *,
        include_discarded: bool,
        score_aggregation: str,
    ) -> tuple[str, pd.Series | None]:
        form, dataframe, mapping = self.normality_service._get_form_context(form_id, include_discarded=include_discarded)
        resolved = self.correlation_service.resolve_correlation_target(
            form,
            dataframe,
            mapping,
            CorrelationTargetInput(target_type=target.target_type, target_id=target.target_id, label=target.label),
            score_aggregation=score_aggregation,
            request_method="auto",
            alpha=0.05,
            include_discarded=include_discarded,
        )
        return resolved.label, resolved.series

    def _frequency_target(self, form: Form, targets: list[ChartTargetInput]) -> ChartTargetInput:
        if targets:
            return targets[0]
        options = self.categorical_association_service.list_categorical_association_options(form.id)
        if not options.categorical_targets:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No categorical targets available")
        target = options.categorical_targets[0]
        return ChartTargetInput(target_type=target.target_type, target_id=target.target_id, role="target", label=target.label)

    def generate_live_frequency_chart(self, form_id: str, request: ChartGenerateRequest) -> ChartSpecRead:
        form = self._get_form(form_id)
        target = self._frequency_target(form, self._build_targets(request.targets))
        if target.target_type != "question":
            return self._default_warning_chart(
                form=form,
                chart_type=request.chart_type or "bar",
                title="Grafico no aplicable",
                theme_name=request.theme,
                source_type="live",
                source_reference=None,
                targets=[target],
                warning="variable_not_categorical",
                description="No fue posible generar un grafico de frecuencias con el target seleccionado.",
            )
        question = self.descriptive_service.get_question_descriptive(
            form_id,
            target.target_id,
            include_discarded=request.include_discarded,
            decimals=request.decimals,
        )
        labels = [item.label or item.value or "" for item in question.frequencies]
        values = [item.frequency for item in question.frequencies]
        percent_values = [item.percent for item in question.frequencies]
        if not labels:
            return self._default_warning_chart(
                form=form,
                chart_type=request.chart_type or "bar",
                title=f"Distribucion de {question.label}",
                theme_name=request.theme,
                source_type="live",
                source_reference=question.question_id,
                targets=[target],
                warning="no_responses",
                description="No hay datos suficientes para construir el grafico solicitado.",
            )
        chart_type = request.chart_type or recommend_chart_types("frequencies", labels=labels)[0]
        warnings = list(question.warnings)
        if chart_type not in {"bar", "horizontal_bar", "pie", "donut"}:
            warnings.append("incompatible_chart_type")
            chart_type = recommend_chart_types("frequencies", labels=labels)[0]
        theme = self._theme(request.theme)
        text = None
        if request.options and request.options.get("show_percentages"):
            text = [f"{value} ({percent}%)" if percent is not None else str(value) for value, percent in zip(values, percent_values)]
        description = f"Distribucion de frecuencias para {question.label}."
        if chart_type == "bar":
            return build_chart_from_frequency_table(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=f"Distribucion de {question.label}",
                source_type="live",
                source_reference=question.question_id,
                targets=[target],
                labels=self._categorical_labels(labels),
                values=values,
                text=text,
                theme=theme,
                warnings=warnings,
                description=description,
            )
        if chart_type == "horizontal_bar":
            return build_horizontal_bar_chart(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=f"Distribucion de {question.label}",
                source_type="live",
                source_reference=question.question_id,
                targets=[target],
                labels=self._categorical_labels(labels),
                values=values,
                text=text,
                theme=theme,
                warnings=warnings,
                description=description,
            )
        if chart_type == "pie":
            return build_pie_chart(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=f"Distribucion de {question.label}",
                source_type="live",
                source_reference=question.question_id,
                targets=[target],
                labels=self._categorical_labels(labels),
                values=values,
                theme=theme,
                warnings=warnings,
                description=description,
                chart_type="pie",
            )
        return build_donut_chart(
            chart_id=self._chart_id(),
            form_id=form.id,
            project_id=form.project_id,
            title=f"Distribucion de {question.label}",
            source_type="live",
            source_reference=question.question_id,
            targets=[target],
            labels=self._categorical_labels(labels),
            values=values,
            theme=theme,
            warnings=warnings,
            description=description,
        )

    def generate_live_descriptive_chart(self, form_id: str, request: ChartGenerateRequest) -> ChartSpecRead:
        form = self._get_form(form_id)
        targets = self._build_targets(request.targets)
        if not targets:
            options = self.group_comparison_service.get_comparison_options(form_id)
            if not options.outcomes:
                return self._default_warning_chart(
                    form=form,
                    chart_type=request.chart_type or "histogram",
                    title="Grafico no aplicable",
                    theme_name=request.theme,
                    source_type="live",
                    source_reference=None,
                    targets=[],
                    warning="no_numeric_data",
                    description="No hay targets numericos para generar el grafico solicitado.",
                )
            targets = [ChartTargetInput(target_type=options.outcomes[0].target_type, target_id=options.outcomes[0].target_id, role="target", label=options.outcomes[0].label)]
        target = targets[0]
        label, series = self._series_for_numeric_target(
            form_id,
            target,
            include_discarded=request.include_discarded,
            score_aggregation=request.score_aggregation,
        )
        values = [] if series is None else pd.to_numeric(series, errors="coerce").dropna().tolist()
        if not values:
            return self._default_warning_chart(
                form=form,
                chart_type=request.chart_type or "histogram",
                title=f"Distribucion de {label}",
                theme_name=request.theme,
                source_type="live",
                source_reference=target.target_id,
                targets=[target],
                warning="no_numeric_data",
                description="No hay valores numericos suficientes para construir el grafico.",
            )
        chart_type = request.chart_type or recommend_chart_types("descriptives")[0]
        warnings: list[str] = []
        if chart_type not in {"histogram", "boxplot"}:
            warnings.append("incompatible_chart_type")
            chart_type = "histogram"
        theme = self._theme(request.theme)
        description = f"Distribucion de la variable {label}."
        if chart_type == "boxplot":
            return build_boxplot_chart(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=f"Boxplot de {label}",
                source_type="live",
                source_reference=target.target_id,
                targets=[target],
                y_values=values,
                x_values=None,
                theme=theme,
                warnings=warnings,
                description=description,
                yaxis_title=label,
            )
        return build_chart_from_descriptives(
            chart_id=self._chart_id(),
            form_id=form.id,
            project_id=form.project_id,
            title=f"Histograma de {label}",
            source_type="live",
            source_reference=target.target_id,
            targets=[target],
            values=values,
            theme=theme,
            warnings=warnings,
            description=description,
            xaxis_title=label,
        )

    def generate_live_scoring_chart(self, form_id: str, request: ChartGenerateRequest) -> ChartSpecRead:
        form = self._get_form(form_id)
        distribution = self.advanced_scoring_service.summarize_bands_distribution(form_id)
        if not distribution:
            return self._default_warning_chart(
                form=form,
                chart_type=request.chart_type or "donut",
                title="Distribucion por baremos",
                theme_name=request.theme,
                source_type="live",
                source_reference=None,
                targets=self._build_targets(request.targets),
                warning="no_scoring_results",
                description="No hay resultados de scoring suficientes para construir un grafico por baremos.",
            )

        grouped: dict[str, list[Any]] = {}
        for item in distribution:
            grouped.setdefault(item.scoring_config_name, []).append(item)
        config_name, items = next(iter(grouped.items()))
        labels = [item.level for item in items]
        values = [item.n for item in items]
        percent_text = [f"{item.percent}%" for item in items]
        chart_type = request.chart_type or ("donut" if len(labels) <= 5 else "horizontal_bar")
        warnings: list[str] = []
        if chart_type not in {"bar", "horizontal_bar", "pie", "donut"}:
            warnings.append("incompatible_chart_type")
            chart_type = "donut" if len(labels) <= 5 else "horizontal_bar"
        theme = self._theme(request.theme)
        description = f"Distribucion de niveles interpretativos para {config_name}."
        targets = self._build_targets(request.targets)

        if chart_type == "bar":
            return build_bar_chart(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=f"Niveles de {config_name}",
                source_type="live",
                source_reference="advanced_scoring",
                targets=targets,
                labels=labels,
                values=values,
                text=percent_text if request.options and request.options.get("show_percentages") else None,
                theme=theme,
                warnings=warnings,
                description=description,
            )
        if chart_type == "horizontal_bar":
            return build_horizontal_bar_chart(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=f"Niveles de {config_name}",
                source_type="live",
                source_reference="advanced_scoring",
                targets=targets,
                labels=labels,
                values=values,
                text=percent_text if request.options and request.options.get("show_percentages") else None,
                theme=theme,
                warnings=warnings,
                description=description,
            )
        if chart_type == "pie":
            return build_pie_chart(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=f"Niveles de {config_name}",
                source_type="live",
                source_reference="advanced_scoring",
                targets=targets,
                labels=labels,
                values=values,
                theme=theme,
                warnings=warnings,
                description=description,
                chart_type="pie",
            )
        return build_donut_chart(
            chart_id=self._chart_id(),
            form_id=form.id,
            project_id=form.project_id,
            title=f"Niveles de {config_name}",
            source_type="live",
            source_reference="advanced_scoring",
            targets=targets,
            labels=labels,
            values=values,
            theme=theme,
            warnings=warnings,
            description=description,
        )

    def _correlation_request(self, request: ChartGenerateRequest) -> CorrelationRequest:
        targets = self._build_targets(request.targets)
        if len(targets) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Correlation chart requires x and y targets")
        x_target = self._get_target_by_role(targets, "x")
        y_target = self._get_target_by_role(targets, "y")
        return CorrelationRequest(
            x=CorrelationTargetInput(target_type=x_target.target_type, target_id=x_target.target_id, label=x_target.label),
            y=CorrelationTargetInput(target_type=y_target.target_type, target_id=y_target.target_id, label=y_target.label),
            method=(request.options or {}).get("force_method", request.options.get("method", "auto")) if request.options else "auto",
            alpha=float((request.options or {}).get("alpha", 0.05)),
            decimals=request.decimals,
            include_discarded=request.include_discarded,
            score_aggregation=request.score_aggregation,
            store_result=False,
        )

    def generate_live_correlation_chart(self, form_id: str, request: ChartGenerateRequest) -> ChartSpecRead:
        form = self._get_form(form_id)
        correlation_request = self._correlation_request(request)
        correlation = self.correlation_service.run_pair_correlation(form_id, correlation_request).result
        form_ctx, dataframe, mapping = self.correlation_service._get_context(form_id, include_discarded=request.include_discarded)
        x_resolved = self.correlation_service.resolve_correlation_target(
            form_ctx,
            dataframe,
            mapping,
            correlation_request.x,
            score_aggregation=request.score_aggregation,
            request_method="auto",
            alpha=correlation_request.alpha,
            include_discarded=request.include_discarded,
        )
        y_resolved = self.correlation_service.resolve_correlation_target(
            form_ctx,
            dataframe,
            mapping,
            correlation_request.y,
            score_aggregation=request.score_aggregation,
            request_method="auto",
            alpha=correlation_request.alpha,
            include_discarded=request.include_discarded,
        )
        paired = pd.DataFrame(
            {
                "x": pd.to_numeric(x_resolved.series, errors="coerce") if x_resolved.series is not None else pd.Series(dtype="float"),
                "y": pd.to_numeric(y_resolved.series, errors="coerce") if y_resolved.series is not None else pd.Series(dtype="float"),
            }
        ).dropna()
        if paired.empty:
            return self._default_warning_chart(
                form=form,
                chart_type=request.chart_type or "scatter",
                title="Grafico de correlacion no aplicable",
                theme_name=request.theme,
                source_type="live",
                source_reference=None,
                targets=self._build_targets(request.targets),
                warning="insufficient_n",
                description="No hay pares validos suficientes para construir el grafico de correlacion.",
            )
        theme = self._theme(request.theme)
        chart_type = request.chart_type or "scatter"
        warnings = list(correlation.warnings)
        if chart_type != "scatter":
            warnings.append("incompatible_chart_type")
        return build_chart_from_correlation(
            chart_id=self._chart_id(),
            form_id=form.id,
            project_id=form.project_id,
            title=f"Relacion entre {correlation.x_target.label} y {correlation.y_target.label}",
            source_type="live",
            source_reference=None,
            targets=self._build_targets(request.targets),
            x_values=paired["x"].tolist(),
            y_values=paired["y"].tolist(),
            theme=theme,
            warnings=warnings,
            description="Nube de puntos basada en los pares validos para el analisis correlacional.",
            xaxis_title=correlation.x_target.label,
            yaxis_title=correlation.y_target.label,
        )

    def generate_live_correlation_matrix_chart(self, form_id: str, request: ChartGenerateRequest) -> ChartSpecRead:
        form = self._get_form(form_id)
        targets = self._build_targets(request.targets)
        if len(targets) < 2:
            options = self.group_comparison_service.get_comparison_options(form_id)
            targets = [
                ChartTargetInput(target_type=item.target_type, target_id=item.target_id, role="target", label=item.label)
                for item in options.outcomes[:3]
            ]
        if len(targets) < 2:
            return self._default_warning_chart(
                form=form,
                chart_type="heatmap",
                title="Heatmap no aplicable",
                theme_name=request.theme,
                source_type="live",
                source_reference=None,
                targets=targets,
                warning="no_numeric_data",
                description="No hay suficientes targets numericos para una matriz de correlacion.",
            )
        matrix = self.correlation_service.run_correlation_matrix(
            form_id,
            CorrelationMatrixRequest(
                targets=[
                    CorrelationTargetInput(target_type=item.target_type, target_id=item.target_id, label=item.label)
                    for item in targets
                ],
                method=(request.options or {}).get("method", "auto"),
                alpha=float((request.options or {}).get("alpha", 0.05)),
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
                store_result=False,
            ),
        )
        labels = [item.label for item in matrix.targets]
        lookup = {(cell.row_target_id, cell.column_target_id): cell.coefficient for cell in matrix.cells}
        z_values: list[list[float | None]] = []
        for row_target in matrix.targets:
            row: list[float | None] = []
            for column_target in matrix.targets:
                row.append(lookup.get((row_target.target_id, column_target.target_id)))
            z_values.append(row)
        theme = self._theme(request.theme)
        return build_chart_from_correlation_matrix(
            chart_id=self._chart_id(),
            form_id=form.id,
            project_id=form.project_id,
            title="Heatmap de correlaciones",
            source_type="live",
            source_reference=None,
            targets=targets,
            x_labels=labels,
            y_labels=labels,
            z_values=z_values,
            theme=theme,
            warnings=matrix.warnings,
            description="Matriz visual de coeficientes de correlacion entre targets seleccionados.",
        )

    def _comparison_request(self, form_id: str, request: ChartGenerateRequest) -> GroupComparisonRequest:
        targets = self._build_targets(request.targets)
        if len(targets) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Group comparison chart requires outcome and group targets")
        outcome_target = self._get_target_by_role(targets, "x") if any(item.role == "x" for item in targets) else self._get_target_by_role(targets, "target") if len(targets) == 1 else next((item for item in targets if item.role == "outcome"), None)
        group_target = next((item for item in targets if item.role == "group"), None)
        if outcome_target is None or group_target is None:
            outcome_target = self._get_target_by_role(targets, "outcome")
            group_target = self._get_target_by_role(targets, "group")
        return GroupComparisonRequest(
            outcome=ComparisonTargetInput(target_type=outcome_target.target_type, target_id=outcome_target.target_id, label=outcome_target.label),
            group=ComparisonTargetInput(target_type=group_target.target_type, target_id=group_target.target_id, label=group_target.label),
            method=(request.options or {}).get("method", "auto"),
            alpha=float((request.options or {}).get("alpha", 0.05)),
            decimals=request.decimals,
            include_discarded=request.include_discarded,
            score_aggregation=request.score_aggregation,
            store_result=False,
        )

    def generate_live_group_comparison_chart(self, form_id: str, request: ChartGenerateRequest) -> ChartSpecRead:
        form = self._get_form(form_id)
        comparison_request = self._comparison_request(form_id, request)
        comparison = self.group_comparison_service.run_group_comparison(form_id, comparison_request).result
        chart_type = request.chart_type or recommend_chart_types("group_comparison")[0]
        warnings = list(comparison.warnings)
        theme = self._theme(request.theme)
        if chart_type == "grouped_bar":
            categories = [group.group_label for group in comparison.groups]
            means = [group.mean for group in comparison.groups]
            series = [{"name": "M", "values": means, "text": [str(value) if value is not None else "" for value in means]}]
            return build_grouped_bar_chart(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                chart_type="grouped_bar",
                title=f"Comparacion de {comparison.outcome_target.label} por {comparison.group_target.label}",
                source_type="live",
                source_reference=None,
                targets=self._build_targets(request.targets),
                categories=categories,
                series=series,
                theme=theme,
                warnings=warnings,
                description="Comparacion visual de medias o puntajes agregados por grupo.",
            )

        form_ctx, dataframe, mapping = self.group_comparison_service._get_context(form_id, include_discarded=request.include_discarded)
        outcome_target = self.group_comparison_service.resolve_outcome_target(
            form_ctx,
            dataframe,
            mapping,
            comparison_request.outcome,
            score_aggregation=request.score_aggregation,
        )
        group_target = self.group_comparison_service.resolve_group_target(form_ctx, dataframe, mapping, comparison_request.group)
        paired = clean_groups(
            outcome_target.series if outcome_target.series is not None else pd.Series(dtype="float"),
            group_target.label_series if group_target.label_series is not None else pd.Series(dtype="object"),
        ).dropna(subset=["outcome", "group"])
        return build_chart_from_group_comparison(
            chart_id=self._chart_id(),
            form_id=form.id,
            project_id=form.project_id,
            title=f"Distribucion de {comparison.outcome_target.label} por {comparison.group_target.label}",
            source_type="live",
            source_reference=None,
            targets=self._build_targets(request.targets),
            y_values=pd.to_numeric(paired["outcome"], errors="coerce").dropna().tolist(),
            x_values=paired["group"].astype(str).tolist(),
            theme=theme,
            warnings=warnings,
            description="Distribucion del outcome por grupo con pares validos.",
            yaxis_title=comparison.outcome_target.label,
        )

    def _association_request(self, request: ChartGenerateRequest) -> CategoricalAssociationRequest:
        targets = self._build_targets(request.targets)
        if len(targets) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categorical association chart requires row and column targets")
        row_target = self._get_target_by_role(targets, "row")
        column_target = self._get_target_by_role(targets, "column")
        return CategoricalAssociationRequest(
            row=CategoricalAssociationTargetInput(target_type=row_target.target_type, target_id=row_target.target_id, label=row_target.label),
            column=CategoricalAssociationTargetInput(target_type=column_target.target_type, target_id=column_target.target_id, label=column_target.label),
            method=(request.options or {}).get("method", "auto"),
            alpha=float((request.options or {}).get("alpha", 0.05)),
            decimals=request.decimals,
            include_discarded=request.include_discarded,
            store_result=False,
        )

    def generate_live_categorical_association_chart(self, form_id: str, request: ChartGenerateRequest) -> ChartSpecRead:
        form = self._get_form(form_id)
        association_request = self._association_request(request)
        association = self.categorical_association_service.run_categorical_association(form_id, association_request).result
        chart_type = request.chart_type or recommend_chart_types("categorical_association")[0]
        warnings = list(association.warnings)
        if chart_type not in {"grouped_bar", "stacked_bar"}:
            warnings.append("incompatible_chart_type")
            chart_type = "grouped_bar"
        categories = association.row_categories
        series = []
        for column in association.column_categories:
            values = []
            text = []
            for row in association.row_categories:
                cell = next((item for item in association.cells if item.row_value == row and item.column_value == column), None)
                values.append(cell.observed if cell is not None else 0)
                text.append("" if cell is None else f"{cell.observed} ({cell.row_percent}%)")
            series.append({"name": column, "values": values, "text": text})
        theme = self._theme(request.theme)
        if chart_type == "stacked_bar":
            return build_stacked_bar_chart(
                chart_id=self._chart_id(),
                form_id=form.id,
                project_id=form.project_id,
                title=f"Asociacion entre {association.row_target.label} y {association.column_target.label}",
                source_type="live",
                source_reference=None,
                targets=self._build_targets(request.targets),
                categories=categories,
                series=series,
                theme=theme,
                warnings=warnings,
                description="Distribucion cruzada de categorias por combinacion observada.",
            )
        return build_chart_from_categorical_association(
            chart_id=self._chart_id(),
            form_id=form.id,
            project_id=form.project_id,
            chart_type="grouped_bar",
            title=f"Asociacion entre {association.row_target.label} y {association.column_target.label}",
            source_type="live",
            source_reference=None,
            targets=self._build_targets(request.targets),
            categories=categories,
            series=series,
            theme=theme,
            warnings=warnings,
            description="Distribucion cruzada de categorias por combinacion observada.",
        )

    def generate_chart(self, form_id: str, request: ChartGenerateRequest) -> ChartSpecRead:
        self._get_form(form_id)
        if request.source_type == "analysis_run":
            if request.analysis_run_id is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="analysis_run_id is required")
            batch = self.generate_from_analysis_run(
                form_id,
                request.analysis_run_id,
                theme=request.theme,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
            )
            return batch.charts[0]
        if request.source_type == "orchestrated":
            if request.analysis_run_id is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="analysis_run_id is required")
            batch = self.generate_from_orchestrated_run(
                form_id,
                request.analysis_run_id,
                theme=request.theme,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
            )
            return batch.charts[0]

        analysis_goal = (request.analysis_goal or "").strip().lower()
        if analysis_goal == "frequencies":
            return self.generate_live_frequency_chart(form_id, request)
        if analysis_goal in {"descriptives", "normality"}:
            return self.generate_live_descriptive_chart(form_id, request)
        if analysis_goal == "correlation":
            return self.generate_live_correlation_chart(form_id, request)
        if analysis_goal == "correlation_matrix":
            return self.generate_live_correlation_matrix_chart(form_id, request)
        if analysis_goal == "group_comparison":
            return self.generate_live_group_comparison_chart(form_id, request)
        if analysis_goal == "categorical_association":
            return self.generate_live_categorical_association_chart(form_id, request)
        if analysis_goal == "advanced_scoring":
            return self.generate_live_scoring_chart(form_id, request)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported chart analysis_goal")

    def _charts_from_analysis_run_request(
        self,
        form_id: str,
        analysis_run: AnalysisRun,
        *,
        theme: str,
        decimals: int,
        include_discarded: bool,
        score_aggregation: str,
    ) -> list[ChartSpecRead]:
        params = analysis_run.params_json if isinstance(analysis_run.params_json, dict) else {}
        if analysis_run.analysis_type == "correlation":
            if "targets" in params:
                chart = self.generate_live_correlation_matrix_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="heatmap",
                        source_type="live",
                        analysis_goal="correlation_matrix",
                        targets=[ChartTargetInput.model_validate(item | {"role": "target"}) for item in params.get("targets", [])],
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                        options=params,
                    ),
                )
                return [chart]
            chart = self.generate_live_correlation_chart(
                form_id,
                ChartGenerateRequest(
                    chart_type="scatter",
                    source_type="live",
                    analysis_goal="correlation",
                    targets=[
                        ChartTargetInput(
                            target_type=params["x"]["target_type"],
                            target_id=params["x"]["target_id"],
                            role="x",
                            label=params["x"].get("label"),
                        ),
                        ChartTargetInput(
                            target_type=params["y"]["target_type"],
                            target_id=params["y"]["target_id"],
                            role="y",
                            label=params["y"].get("label"),
                        ),
                    ],
                    theme=theme,
                    decimals=decimals,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                    options=params,
                ),
            )
            return [chart]
        if analysis_run.analysis_type == "group_comparison":
            chart_a = self.generate_live_group_comparison_chart(
                form_id,
                ChartGenerateRequest(
                    chart_type="boxplot",
                    source_type="live",
                    analysis_goal="group_comparison",
                    targets=[
                        ChartTargetInput(target_type=params["outcome"]["target_type"], target_id=params["outcome"]["target_id"], role="outcome", label=params["outcome"].get("label")),
                        ChartTargetInput(target_type=params["group"]["target_type"], target_id=params["group"]["target_id"], role="group", label=params["group"].get("label")),
                    ],
                    theme=theme,
                    decimals=decimals,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                    options=params,
                ),
            )
            chart_b = self.generate_live_group_comparison_chart(
                form_id,
                ChartGenerateRequest(
                    chart_type="grouped_bar",
                    source_type="live",
                    analysis_goal="group_comparison",
                    targets=[
                        ChartTargetInput(target_type=params["outcome"]["target_type"], target_id=params["outcome"]["target_id"], role="outcome", label=params["outcome"].get("label")),
                        ChartTargetInput(target_type=params["group"]["target_type"], target_id=params["group"]["target_id"], role="group", label=params["group"].get("label")),
                    ],
                    theme=theme,
                    decimals=decimals,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                    options=params,
                ),
            )
            return [chart_a, chart_b]
        if analysis_run.analysis_type == "categorical_association":
            chart = self.generate_live_categorical_association_chart(
                form_id,
                ChartGenerateRequest(
                    chart_type="grouped_bar",
                    source_type="live",
                    analysis_goal="categorical_association",
                    targets=[
                        ChartTargetInput(target_type=params["row"]["target_type"], target_id=params["row"]["target_id"], role="row", label=params["row"].get("label")),
                        ChartTargetInput(target_type=params["column"]["target_type"], target_id=params["column"]["target_id"], role="column", label=params["column"].get("label")),
                    ],
                    theme=theme,
                    decimals=decimals,
                    include_discarded=include_discarded,
                    score_aggregation=score_aggregation,
                    options=params,
                ),
            )
            return [chart]
        if analysis_run.analysis_type == "normality":
            request = ChartGenerateRequest(
                chart_type="histogram",
                source_type="live",
                analysis_goal="normality",
                theme=theme,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            )
            return [self.generate_live_descriptive_chart(form_id, request)]
        if analysis_run.analysis_type == "advanced_scoring":
            return [
                self.generate_live_scoring_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="donut",
                        source_type="live",
                        analysis_goal="advanced_scoring",
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                        options={"show_percentages": True},
                    ),
                )
            ]
        if analysis_run.analysis_type == "descriptive":
            charts = [
                self.generate_live_descriptive_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="histogram",
                        source_type="live",
                        analysis_goal="descriptives",
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                    ),
                )
            ]
            return charts
        if analysis_run.analysis_type == "orchestrated_analysis":
            return self.generate_from_orchestrated_run(
                form_id,
                analysis_run.id,
                theme=theme,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            ).charts
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported AnalysisRun type for chart generation")

    def generate_from_analysis_run(
        self,
        form_id: str,
        analysis_run_id: str,
        *,
        theme: str,
        decimals: int,
        include_discarded: bool,
        score_aggregation: str,
    ) -> ChartBatchRead:
        form = self._get_form(form_id)
        analysis_run = self._get_analysis_run(form_id, analysis_run_id)
        charts = self._charts_from_analysis_run_request(
            form_id,
            analysis_run,
            theme=theme,
            decimals=decimals,
            include_discarded=include_discarded,
            score_aggregation=score_aggregation,
        )
        for chart in charts:
            chart.source_type = "analysis_run"
            chart.source_reference = analysis_run.id
        warnings = [warning for chart in charts for warning in chart.warnings]
        return ChartBatchRead(
            form_id=form.id,
            project_id=form.project_id,
            total_charts=len(charts),
            charts=charts,
            warnings=list(dict.fromkeys(warnings)),
        )

    def generate_from_orchestrated_run(
        self,
        form_id: str,
        analysis_run_id: str,
        *,
        theme: str,
        decimals: int,
        include_discarded: bool,
        score_aggregation: str,
    ) -> ChartBatchRead:
        form = self._get_form(form_id)
        analysis_run = self._get_analysis_run(form_id, analysis_run_id)
        if analysis_run.analysis_type != "orchestrated_analysis":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AnalysisRun is not orchestrated_analysis")
        params = analysis_run.params_json if isinstance(analysis_run.params_json, dict) else {}
        if not params:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AnalysisRun does not contain orchestrator params")
        regenerated = self.analysis_orchestrator_service.run_orchestrated_analysis(
            form_id,
            OrchestratedAnalysisRequest.model_validate({**params, "store_result": False}),
        )
        charts: list[ChartSpecRead] = []
        base_theme = self._theme(theme)
        for index, block in enumerate(regenerated.chart_blocks):
            chart_type = block.chart_type
            target_payloads: list[ChartTargetInput] = []
            for item in params.get("targets", []):
                try:
                    target_payloads.append(ChartTargetInput.model_validate(item))
                except Exception:
                    continue
            if regenerated.analysis_goal == "correlation_matrix" and chart_type == "heatmap":
                charts.append(
                    self.generate_live_correlation_matrix_chart(
                        form_id,
                        ChartGenerateRequest(
                            chart_type="heatmap",
                            source_type="live",
                            analysis_goal="correlation_matrix",
                            targets=target_payloads,
                            theme=theme,
                            decimals=decimals,
                            include_discarded=include_discarded,
                            score_aggregation=score_aggregation,
                            options=params,
                        ),
                    )
                )
                continue
            if regenerated.analysis_goal == "correlation" and chart_type == "scatter":
                charts.append(
                    self.generate_live_correlation_chart(
                        form_id,
                        ChartGenerateRequest(
                            chart_type="scatter",
                            source_type="live",
                            analysis_goal="correlation",
                            targets=target_payloads,
                            theme=theme,
                            decimals=decimals,
                            include_discarded=include_discarded,
                            score_aggregation=score_aggregation,
                            options=params,
                        ),
                    )
                )
                continue
            if regenerated.analysis_goal == "group_comparison":
                target_chart_type = "grouped_bar" if chart_type == "grouped_bar" else "boxplot"
                charts.append(
                    self.generate_live_group_comparison_chart(
                        form_id,
                        ChartGenerateRequest(
                            chart_type=target_chart_type,
                            source_type="live",
                            analysis_goal="group_comparison",
                            targets=target_payloads,
                            theme=theme,
                            decimals=decimals,
                            include_discarded=include_discarded,
                            score_aggregation=score_aggregation,
                            options=params,
                        ),
                    )
                )
                continue
            if regenerated.analysis_goal == "categorical_association":
                target_chart_type = "stacked_bar" if chart_type == "mosaic" else "grouped_bar"
                charts.append(
                    self.generate_live_categorical_association_chart(
                        form_id,
                        ChartGenerateRequest(
                            chart_type=target_chart_type,
                            source_type="live",
                            analysis_goal="categorical_association",
                            targets=target_payloads,
                            theme=theme,
                            decimals=decimals,
                            include_discarded=include_discarded,
                            score_aggregation=score_aggregation,
                            options=params,
                        ),
                    )
                )
                continue
            if regenerated.analysis_goal in {"descriptive_summary", "full_form_scan"}:
                chart_kind = "histogram" if chart_type == "histogram" else "bar"
                source_description = "Resumen exploratorio del formulario." if regenerated.analysis_goal == "full_form_scan" else "Resumen descriptivo del formulario."
                charts.append(
                    build_chart_from_orchestrated_result(
                        chart_id=self._chart_id(),
                        form_id=form.id,
                        project_id=form.project_id,
                        chart_type=chart_kind,
                        title=block.suggested_title,
                        source_reference=analysis_run_id,
                        targets=target_payloads,
                        data={"summary": regenerated.raw_results_summary},
                        encoding={"source": "raw_results_summary"},
                        plotly_data=[],
                        plotly_layout={"title": {"text": block.suggested_title}, "paper_bgcolor": base_theme["background"]},
                        plotly_config={"responsive": True},
                        theme=base_theme,
                        warnings=["chart_block_requires_live_selection"],
                        description=source_description,
                    )
                )
                continue
            charts.append(
                build_chart_from_orchestrated_result(
                    chart_id=self._chart_id(),
                    form_id=form.id,
                    project_id=form.project_id,
                    chart_type="bar",
                    title=block.suggested_title,
                    source_reference=f"{analysis_run_id}:{index}",
                    targets=target_payloads,
                    data={"chart_block": block.model_dump()},
                    encoding={"source": "chart_block"},
                    plotly_data=[],
                    plotly_layout={"title": {"text": block.suggested_title}, "paper_bgcolor": base_theme["background"]},
                    plotly_config={"responsive": True},
                    theme=base_theme,
                    warnings=["chart_block_requires_live_selection"],
                    description="Bloque visual sugerido por el orquestador.",
                )
            )
        for chart in charts:
            chart.source_type = "orchestrated"
            chart.source_reference = analysis_run_id
        warnings = [warning for chart in charts for warning in chart.warnings]
        return ChartBatchRead(
            form_id=form.id,
            project_id=form.project_id,
            total_charts=len(charts),
            charts=charts,
            warnings=list(dict.fromkeys(warnings)),
        )

    def generate_recommended_charts(
        self,
        form_id: str,
        *,
        theme: str,
        decimals: int,
        include_discarded: bool,
        score_aggregation: str,
        max_charts: int,
    ) -> ChartBatchRead:
        form = self._get_form(form_id)
        charts: list[ChartSpecRead] = []
        categorical_options = self.categorical_association_service.list_categorical_association_options(form_id, include_discarded=include_discarded)
        comparison_options = self.group_comparison_service.get_comparison_options(form_id, include_discarded=include_discarded)
        scoring_results = self.advanced_scoring_service.get_form_score_results(form_id)
        if categorical_options.categorical_targets and len(charts) < max_charts:
            charts.append(
                self.generate_live_frequency_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type=None,
                        source_type="live",
                        analysis_goal="frequencies",
                        targets=[ChartTargetInput(target_type=categorical_options.categorical_targets[0].target_type, target_id=categorical_options.categorical_targets[0].target_id, role="target", label=categorical_options.categorical_targets[0].label)],
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                        options={"show_percentages": True},
                    ),
                )
            )
        if comparison_options.outcomes and len(charts) < max_charts:
            first_numeric = comparison_options.outcomes[0]
            charts.append(
                self.generate_live_descriptive_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="histogram",
                        source_type="live",
                        analysis_goal="descriptives",
                        targets=[ChartTargetInput(target_type=first_numeric.target_type, target_id=first_numeric.target_id, role="target", label=first_numeric.label)],
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                    ),
                )
            )
        if len(comparison_options.outcomes) >= 2 and len(charts) < max_charts:
            charts.append(
                self.generate_live_correlation_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="scatter",
                        source_type="live",
                        analysis_goal="correlation",
                        targets=[
                            ChartTargetInput(target_type=comparison_options.outcomes[0].target_type, target_id=comparison_options.outcomes[0].target_id, role="x", label=comparison_options.outcomes[0].label),
                            ChartTargetInput(target_type=comparison_options.outcomes[1].target_type, target_id=comparison_options.outcomes[1].target_id, role="y", label=comparison_options.outcomes[1].label),
                        ],
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                    ),
                )
            )
        if len(comparison_options.outcomes) >= 1 and len(comparison_options.groups) >= 1 and len(charts) < max_charts:
            charts.append(
                self.generate_live_group_comparison_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="boxplot",
                        source_type="live",
                        analysis_goal="group_comparison",
                        targets=[
                            ChartTargetInput(target_type=comparison_options.outcomes[0].target_type, target_id=comparison_options.outcomes[0].target_id, role="outcome", label=comparison_options.outcomes[0].label),
                            ChartTargetInput(target_type=comparison_options.groups[0].target_type, target_id=comparison_options.groups[0].target_id, role="group", label=comparison_options.groups[0].label),
                        ],
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                    ),
                )
            )
        if len(categorical_options.categorical_targets) >= 2 and len(charts) < max_charts:
            charts.append(
                self.generate_live_categorical_association_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="grouped_bar",
                        source_type="live",
                        analysis_goal="categorical_association",
                        targets=[
                            ChartTargetInput(target_type=categorical_options.categorical_targets[0].target_type, target_id=categorical_options.categorical_targets[0].target_id, role="row", label=categorical_options.categorical_targets[0].label),
                            ChartTargetInput(target_type=categorical_options.categorical_targets[1].target_type, target_id=categorical_options.categorical_targets[1].target_id, role="column", label=categorical_options.categorical_targets[1].label),
                        ],
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                    ),
                )
            )
        if scoring_results.scored_responses > 0 and len(charts) < max_charts:
            charts.append(
                self.generate_live_scoring_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="donut",
                        source_type="live",
                        analysis_goal="advanced_scoring",
                        theme=theme,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                        options={"show_percentages": True},
                    ),
                )
            )
        warnings = [warning for chart in charts for warning in chart.warnings]
        return ChartBatchRead(
            form_id=form.id,
            project_id=form.project_id,
            total_charts=len(charts),
            charts=charts[:max_charts],
            warnings=list(dict.fromkeys(warnings)),
        )

    def generate_chart_batch(self, form_id: str, request: ChartBatchRequest) -> ChartBatchRead:
        form = self._get_form(form_id)
        if request.source_type == "analysis_run":
            charts: list[ChartSpecRead] = []
            warnings: list[str] = []
            for run_id in request.analysis_run_ids or []:
                batch = self.generate_from_analysis_run(
                    form_id,
                    run_id,
                    theme=request.theme,
                    decimals=request.decimals,
                    include_discarded=request.include_discarded,
                    score_aggregation=request.score_aggregation,
                )
                charts.extend(batch.charts)
                warnings.extend(batch.warnings)
            return ChartBatchRead(
                form_id=form.id,
                project_id=form.project_id,
                total_charts=len(charts),
                charts=charts,
                warnings=list(dict.fromkeys(warnings)),
            )
        if request.source_type == "orchestrated":
            charts = []
            warnings = []
            for run_id in request.analysis_run_ids or []:
                batch = self.generate_from_orchestrated_run(
                    form_id,
                    run_id,
                    theme=request.theme,
                    decimals=request.decimals,
                    include_discarded=request.include_discarded,
                    score_aggregation=request.score_aggregation,
                )
                charts.extend(batch.charts)
                warnings.extend(batch.warnings)
            return ChartBatchRead(
                form_id=form.id,
                project_id=form.project_id,
                total_charts=len(charts),
                charts=charts,
                warnings=list(dict.fromkeys(warnings)),
            )

        if not request.chart_types:
            max_charts = int((request.options or {}).get("max_charts", 10))
            return self.generate_recommended_charts(
                form_id,
                theme=request.theme,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
                max_charts=max_charts,
            )

        charts: list[ChartSpecRead] = []
        warnings: list[str] = []
        for chart_type in request.chart_types:
            if chart_type in {"bar", "horizontal_bar", "pie", "donut"}:
                chart = self.generate_live_frequency_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type=chart_type,
                        source_type="live",
                        analysis_goal="frequencies",
                        theme=request.theme,
                        decimals=request.decimals,
                        include_discarded=request.include_discarded,
                        score_aggregation=request.score_aggregation,
                        options=request.options,
                    ),
                )
            elif chart_type in {"histogram", "boxplot"}:
                chart = self.generate_live_descriptive_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type=chart_type,
                        source_type="live",
                        analysis_goal="descriptives",
                        theme=request.theme,
                        decimals=request.decimals,
                        include_discarded=request.include_discarded,
                        score_aggregation=request.score_aggregation,
                        options=request.options,
                    ),
                )
            elif chart_type == "scatter":
                chart = self.generate_recommended_charts(
                    form_id,
                    theme=request.theme,
                    decimals=request.decimals,
                    include_discarded=request.include_discarded,
                    score_aggregation=request.score_aggregation,
                    max_charts=10,
                ).charts[0]
            elif chart_type == "heatmap":
                chart = self.generate_live_correlation_matrix_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type="heatmap",
                        source_type="live",
                        analysis_goal="correlation_matrix",
                        theme=request.theme,
                        decimals=request.decimals,
                        include_discarded=request.include_discarded,
                        score_aggregation=request.score_aggregation,
                        options=request.options,
                    ),
                )
            elif chart_type in {"grouped_bar", "stacked_bar"}:
                chart = self.generate_live_categorical_association_chart(
                    form_id,
                    ChartGenerateRequest(
                        chart_type=chart_type,
                        source_type="live",
                        analysis_goal="categorical_association",
                        theme=request.theme,
                        decimals=request.decimals,
                        include_discarded=request.include_discarded,
                        score_aggregation=request.score_aggregation,
                        options=request.options,
                    ),
                )
            else:
                continue
            charts.append(chart)
            warnings.extend(chart.warnings)
        return ChartBatchRead(
            form_id=form.id,
            project_id=form.project_id,
            total_charts=len(charts),
            charts=charts,
            warnings=list(dict.fromkeys(warnings)),
        )

    def list_chart_options(self, form_id: str) -> ChartOptionsRead:
        form = self._get_form(form_id)
        comparison_options = self.group_comparison_service.get_comparison_options(form_id)
        categorical_options = self.categorical_association_service.list_categorical_association_options(form_id)
        scoring_results = self.advanced_scoring_service.get_form_score_results(form_id)
        analysis_runs = list(
            self.db.scalars(
                select(AnalysisRun)
                .where(AnalysisRun.form_id == form_id)
                .order_by(AnalysisRun.created_at.desc())
                .limit(20)
            ).all()
        )
        numeric_targets = [
            ChartTargetInput(target_type=item.target_type, target_id=item.target_id, role="target", label=item.label)
            for item in comparison_options.outcomes
        ]
        categorical_targets = [
            ChartTargetInput(target_type=item.target_type, target_id=item.target_id, role="target", label=item.label)
            for item in categorical_options.categorical_targets
        ]
        recommendations = [
            ChartRecommendationRead(chart_type="bar", analysis_goal="frequencies", reason="Adecuado para preguntas categoricas con varias categorias."),
            ChartRecommendationRead(chart_type="donut", analysis_goal="frequencies", reason="Adecuado para distribuciones simples con pocas categorias."),
            ChartRecommendationRead(chart_type="histogram", analysis_goal="descriptives", reason="Adecuado para observar la forma de una variable numerica."),
            ChartRecommendationRead(chart_type="scatter", analysis_goal="correlation", reason="Adecuado para explorar la asociacion entre dos variables numericas."),
            ChartRecommendationRead(chart_type="heatmap", analysis_goal="correlation_matrix", reason="Adecuado para resumir matrices de correlacion."),
            ChartRecommendationRead(chart_type="boxplot", analysis_goal="group_comparison", reason="Adecuado para comparar distribuciones de un outcome por grupos."),
            ChartRecommendationRead(chart_type="grouped_bar", analysis_goal="categorical_association", reason="Adecuado para mostrar tablas cruzadas y distribuciones por categorias."),
        ]
        if scoring_results.scored_responses > 0:
            recommendations.extend(
                [
                    ChartRecommendationRead(chart_type="donut", analysis_goal="advanced_scoring", reason="Adecuado para resumir niveles interpretativos o baremos del instrumento."),
                    ChartRecommendationRead(chart_type="bar", analysis_goal="advanced_scoring", reason="Adecuado para comparar frecuencias por nivel de baremo."),
                ]
            )
        return ChartOptionsRead(
            form_id=form.id,
            available_chart_types=sorted(
                [
                    "bar",
                    "horizontal_bar",
                    "grouped_bar",
                    "stacked_bar",
                    "pie",
                    "donut",
                    "histogram",
                    "boxplot",
                    "scatter",
                    "heatmap",
                    "line",
                    "mosaic_future",
                ]
            ),
            available_themes=sorted(CHART_THEMES.keys()),
            recommended_charts=recommendations,
            available_targets={
                "numeric": numeric_targets,
                "categorical": categorical_targets,
                "all": list({(item.target_type, item.target_id): item for item in [*numeric_targets, *categorical_targets]}.values()),
            },
            analysis_runs=[
                CompatibleChartAnalysisRunRead(id=item.id, analysis_type=item.analysis_type, created_at=item.created_at)
                for item in analysis_runs
            ],
        )

    def export_chart_specs(self, form_id: str, request: ChartExportRequest) -> ChartExportRead:
        form = self._get_form(form_id)
        batch = self.generate_chart_batch(
            form_id,
            ChartBatchRequest(
                source_type=request.source_type,
                analysis_run_ids=request.analysis_run_ids,
                chart_types=request.chart_types,
                theme=request.theme,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
                options=request.options,
            ),
        )
        file_name, file_path = export_chart_specs_json(
            exports_dir=self.exports_dir,
            form_id=form.id,
            payload=batch.model_dump(mode="json"),
        )
        artifact = self._build_export_artifact(
            form=form,
            artifact_type="chart_spec_json",
            file_name=file_name,
            file_path=file_path,
            mime_type="application/json",
            metadata_json={
                "source_type": request.source_type,
                "chart_types": request.chart_types,
                "analysis_run_ids": request.analysis_run_ids,
                "chart_count": batch.total_charts,
            },
        )
        return ChartExportRead(
            artifact_id=artifact.id,
            file_name=file_name,
            file_path=file_path.as_posix(),
            mime_type="application/json",
            chart_count=batch.total_charts,
            created_at=artifact.created_at,
        )
