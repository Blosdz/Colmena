from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analysis_run import AnalysisRun
from app.models.export_artifact import ExportArtifact
from app.models.form import Form
from app.models.response_score import ResponseScore
from app.schemas.analysis_orchestrator import AnalysisTargetInput, FullScanRequest, OrchestratedAnalysisRequest
from app.schemas.apa_table import (
    ApaTableBatchRead,
    ApaTableBatchRequest,
    ApaTableExportRead,
    ApaTableOptionsRead,
    ApaTableRead,
    ApaTableRecommendationRead,
    ApaTableRequest,
    CompatibleAnalysisRunRead,
)
from app.schemas.categorical_association import CategoricalAssociationRequest, CategoricalAssociationTargetInput
from app.schemas.correlation import CorrelationMatrixRequest, CorrelationRequest, CorrelationTargetInput
from app.schemas.group_comparison import ComparisonTargetInput, GroupComparisonRequest
from app.schemas.normality import NormalityRunRequest
from app.services.analysis_orchestrator_service import AnalysisOrchestratorService
from app.services.advanced_scoring_service import AdvancedScoringService
from app.services.categorical_association_service import CategoricalAssociationService
from app.services.correlation_service import CorrelationService
from app.statistics.correlation_engine import correlation_magnitude_label
from app.services.dataset_service import DatasetService
from app.services.descriptive_service import DescriptiveService
from app.services.group_comparison_service import GroupComparisonService
from app.services.normality_service import NormalityService
from app.tables.apa_table_builder import (
    build_categorical_association_table,
    build_control_scale_flags_table,
    build_correlation_matrix_table,
    build_correlation_table,
    build_descriptive_table,
    build_frequency_table,
    build_from_orchestrated_analysis,
    build_group_comparison_table,
    build_normality_table,
    build_score_band_distribution_table,
    build_scoring_summary_table,
    build_table_title,
)


class ApaTableService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.exports_dir = self.settings.backend_dir / "data" / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_service = DatasetService(db)
        self.descriptive_service = DescriptiveService(db)
        self.normality_service = NormalityService(db)
        self.advanced_scoring_service = AdvancedScoringService(db)
        self.correlation_service = CorrelationService(db)
        self.group_comparison_service = GroupComparisonService(db)
        self.categorical_association_service = CategoricalAssociationService(db)
        self.analysis_orchestrator_service = AnalysisOrchestratorService(db)

    def _get_form(self, form_id: str) -> Form:
        return self.dataset_service._get_form(form_id)

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

    def _all_questions(self, form: Form) -> list[Any]:
        return sorted(
            (question for question in form.questions if question.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )

    def _categorical_questions(self, form: Form) -> list[Any]:
        items: list[Any] = []
        for question in self._all_questions(form):
            if question.question_type in {"single_choice", "dropdown", "boolean", "likert"}:
                items.append(question)
        return items

    def _numeric_questions(self, form: Form) -> list[Any]:
        items: list[Any] = []
        for question in self._all_questions(form):
            if question.question_type == "number" or question.is_scored:
                items.append(question)
        return items

    def _value_from_result(self, result: dict[str, Any], *keys: str) -> Any:
        current: Any = result
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def _target_type_from_options(self, options: dict[str, Any], key: str, default: str = "question") -> str:
        value = options.get(key)
        if isinstance(value, dict):
            return str(value.get("target_type", default))
        return str(options.get(f"{key}_type", default))

    def _target_id_from_options(self, options: dict[str, Any], key: str) -> str | None:
        value = options.get(key)
        if isinstance(value, dict):
            return value.get("target_id")
        return options.get(f"{key}_id")

    def _frequency_question_ids(self, form: Form, request: ApaTableRequest) -> list[str]:
        options = request.options or {}
        question_ids = options.get("question_ids") or request.target_ids or []
        if question_ids:
            return [str(item) for item in question_ids]
        first = next((question.id for question in self._categorical_questions(form)), None)
        return [first] if first else []

    def _descriptive_question_ids(self, form: Form, request: ApaTableRequest) -> list[str]:
        options = request.options or {}
        question_ids = options.get("question_ids") or request.target_ids or []
        if question_ids:
            return [str(item) for item in question_ids]
        return [question.id for question in self._numeric_questions(form)]

    def _build_empty_table(self, table_type: str, form_id: str, title: str, warning: str) -> ApaTableRead:
        builder_map = {
            "frequencies": lambda: build_frequency_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
                include_variable_column=False,
            ),
            "descriptives": lambda: build_descriptive_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "normality": lambda: build_normality_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "correlation": lambda: build_correlation_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "correlation_matrix": lambda: build_correlation_matrix_table(
                title=title,
                columns_labels=[],
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "group_comparison": lambda: build_group_comparison_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "categorical_association": lambda: build_categorical_association_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "scoring_summary": lambda: build_scoring_summary_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "score_band_distribution": lambda: build_score_band_distribution_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "control_scale_flags": lambda: build_control_scale_flags_table(
                title=title,
                rows=[],
                warnings=[warning],
                source={"form_id": form_id, "source_type": "live"},
                decimals=3,
            ),
            "orchestrated_summary": lambda: build_from_orchestrated_analysis(
                table_type="orchestrated_summary",
                title=title,
                rows=[],
                columns=[],
                source={"form_id": form_id, "source_type": "orchestrated"},
                warnings=[warning],
                decimals=3,
                source_result=None,
            ),
        }
        return builder_map[table_type]()

    def generate_live_frequency_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        form = self._get_form(form_id)
        question_ids = self._frequency_question_ids(form, request)
        if not question_ids:
            return self._build_empty_table("frequencies", form_id, build_table_title("frequencies"), "no_categorical_data")

        rows: list[dict[str, Any]] = []
        selected_questions: list[Any] = []
        for question_id in question_ids:
            question = self.descriptive_service.get_question_descriptive(
                form_id,
                question_id,
                include_discarded=request.include_discarded,
                decimals=request.decimals,
            )
            if not question.frequencies:
                continue
            selected_questions.append(question)
            for frequency in question.frequencies:
                row = {
                    "category": frequency.label or frequency.value or "",
                    "n": frequency.frequency,
                    "percent": frequency.percent,
                    "valid_percent": frequency.valid_percent,
                    "cumulative_percent": frequency.cumulative_percent,
                }
                if len(question_ids) > 1:
                    row["variable"] = question.label
                rows.append(row)

        if not rows:
            return self._build_empty_table("frequencies", form_id, build_table_title("frequencies"), "all_values_missing")

        title_context = selected_questions[0].label if len(selected_questions) == 1 else "variables categoricas"
        warnings = list(dict.fromkeys(item for question in selected_questions for item in question.warnings))
        return build_frequency_table(
            title=build_table_title("frequencies", title_context),
            rows=rows,
            warnings=warnings,
            source={"form_id": form_id, "source_type": "live", "question_ids": question_ids},
            decimals=request.decimals,
            include_variable_column=len(question_ids) > 1,
        )

    def generate_live_descriptive_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        report = self.descriptive_service.get_form_descriptives(
            form_id,
            include_discarded=request.include_discarded,
            decimals=request.decimals,
            score_aggregation=request.score_aggregation,
        )
        selected_ids = set(self._descriptive_question_ids(self._get_form(form_id), request))
        rows: list[dict[str, Any]] = []
        warnings = list(report.overview.warnings)
        for question in report.questions:
            if question.question_id not in selected_ids or question.numeric is None:
                continue
            rows.append(
                {
                    "variable": question.label,
                    "n": question.numeric.valid_n,
                    "mean": question.numeric.mean,
                    "sd": question.numeric.standard_deviation,
                    "median": question.numeric.median,
                    "minimum": question.numeric.minimum,
                    "maximum": question.numeric.maximum,
                    "skewness": question.numeric.skewness,
                    "kurtosis": question.numeric.kurtosis,
                }
            )
            warnings.extend(question.warnings)

        if not rows:
            return self._build_empty_table("descriptives", form_id, build_table_title("descriptives"), "no_numeric_data")

        return build_descriptive_table(
            title=build_table_title("descriptives", "variables numericas"),
            rows=rows,
            warnings=list(dict.fromkeys(warnings)),
            source={"form_id": form_id, "source_type": "live", "question_ids": list(selected_ids)},
            decimals=request.decimals,
        )

    def generate_live_normality_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        report = self.normality_service.get_normality_report(
            form_id,
            method=(request.options or {}).get("method", "auto"),
            alpha=(request.options or {}).get("alpha", 0.05),
            decimals=request.decimals,
            include_discarded=request.include_discarded,
            score_aggregation=request.score_aggregation,
        )
        selected_ids = set(request.target_ids or [])
        rows: list[dict[str, Any]] = []
        for result in report.results:
            if selected_ids and result.target_id not in selected_ids:
                continue
            rows.append(
                {
                    "variable": result.target_name,
                    "n": result.valid_n,
                    "test": result.method,
                    "statistic": result.statistic,
                    "p_value": result.p_value,
                    "decision": result.classification,
                }
            )

        if not rows:
            return self._build_empty_table("normality", form_id, build_table_title("normality"), "no_numeric_data")

        return build_normality_table(
            title=build_table_title("normality", "targets aplicables"),
            rows=rows,
            warnings=report.warnings,
            source={"form_id": form_id, "source_type": "live"},
            decimals=request.decimals,
        )

    def _correlation_request_from_options(self, request: ApaTableRequest) -> CorrelationRequest:
        options = request.options or {}
        x_id = self._target_id_from_options(options, "x")
        y_id = self._target_id_from_options(options, "y")
        if x_id is None or y_id is None:
            if request.target_ids and len(request.target_ids) >= 2:
                x_id, y_id = request.target_ids[:2]
            else:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Correlation table requires x and y targets")
        return CorrelationRequest(
            x=CorrelationTargetInput(target_type=self._target_type_from_options(options, "x"), target_id=str(x_id)),
            y=CorrelationTargetInput(target_type=self._target_type_from_options(options, "y"), target_id=str(y_id)),
            method=str(options.get("method", "auto")),
            alpha=float(options.get("alpha", 0.05)),
            decimals=request.decimals,
            include_discarded=request.include_discarded,
            score_aggregation=request.score_aggregation,
            store_result=False,
        )

    def generate_live_correlation_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        correlation = self.correlation_service.run_pair_correlation(form_id, self._correlation_request_from_options(request)).result
        row = {
            "variable_1": correlation.x_target.label,
            "variable_2": correlation.y_target.label,
            "n": correlation.valid_n,
            "method": correlation.method_used,
            "coefficient": correlation.coefficient,
            "p_value": correlation.p_value,
            "magnitude": correlation_magnitude_label(correlation.magnitude),
        }
        return build_correlation_table(
            title=build_table_title("correlation", f"{correlation.x_target.label} y {correlation.y_target.label}"),
            rows=[row],
            warnings=correlation.warnings,
            source={"form_id": form_id, "source_type": "live"},
            decimals=request.decimals,
        )

    def _correlation_matrix_request_from_options(self, form_id: str, request: ApaTableRequest) -> CorrelationMatrixRequest:
        options = request.options or {}
        raw_targets = options.get("targets")
        targets: list[CorrelationTargetInput] = []
        if isinstance(raw_targets, list) and raw_targets:
            for item in raw_targets:
                targets.append(
                    CorrelationTargetInput(
                        target_type=str(item.get("target_type", "question")),
                        target_id=str(item["target_id"]),
                        label=item.get("label"),
                    )
                )
        elif request.target_ids:
            target_type = str(options.get("target_type", "question"))
            targets = [CorrelationTargetInput(target_type=target_type, target_id=str(item)) for item in request.target_ids]
        else:
            numeric_targets = self.group_comparison_service.get_comparison_options(form_id).outcomes
            targets = [CorrelationTargetInput(target_type=item.target_type, target_id=item.target_id, label=item.label) for item in numeric_targets[:3]]
        return CorrelationMatrixRequest(
            targets=targets,
            method=str(options.get("method", "auto")),
            alpha=float(options.get("alpha", 0.05)),
            decimals=request.decimals,
            include_discarded=request.include_discarded,
            score_aggregation=request.score_aggregation,
            store_result=False,
        )

    def generate_live_correlation_matrix_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        matrix = self.correlation_service.run_correlation_matrix(form_id, self._correlation_matrix_request_from_options(form_id, request))
        labels = [target.label for target in matrix.targets]
        lookup = {(cell.row_target_id, cell.column_target_id): cell for cell in matrix.cells}
        rows: list[dict[str, Any]] = []
        for row_target in matrix.targets:
            row: dict[str, Any] = {"variable": row_target.label}
            for column_target in matrix.targets:
                cell = lookup.get((row_target.target_id, column_target.target_id))
                row[column_target.label] = None if cell is None else cell.coefficient
            rows.append(row)
        return build_correlation_matrix_table(
            title=build_table_title("correlation_matrix", "targets seleccionados"),
            columns_labels=labels,
            rows=rows,
            warnings=matrix.warnings,
            source={"form_id": form_id, "source_type": "live"},
            decimals=request.decimals,
        )

    def _comparison_request_from_options(self, form_id: str, request: ApaTableRequest) -> GroupComparisonRequest:
        options = request.options or {}
        outcome_id = self._target_id_from_options(options, "outcome")
        group_id = self._target_id_from_options(options, "group")
        if outcome_id is None or group_id is None:
            comparison_options = self.group_comparison_service.get_comparison_options(form_id)
            if outcome_id is None and comparison_options.outcomes:
                outcome_id = comparison_options.outcomes[0].target_id
            if group_id is None and comparison_options.groups:
                group_id = comparison_options.groups[0].target_id
        if outcome_id is None or group_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Group comparison table requires outcome and group targets")
        return GroupComparisonRequest(
            outcome=ComparisonTargetInput(target_type=self._target_type_from_options(options, "outcome"), target_id=str(outcome_id)),
            group=ComparisonTargetInput(target_type=self._target_type_from_options(options, "group"), target_id=str(group_id)),
            method=str(options.get("method", "auto")),
            alpha=float(options.get("alpha", 0.05)),
            decimals=request.decimals,
            include_discarded=request.include_discarded,
            score_aggregation=request.score_aggregation,
            store_result=False,
        )

    def generate_live_group_comparison_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        comparison = self.group_comparison_service.run_group_comparison(
            form_id,
            self._comparison_request_from_options(form_id, request),
        ).result
        rows: list[dict[str, Any]] = []
        effect_size_text = ""
        if comparison.effect_size is not None:
            effect_size_text = f"{comparison.effect_size.name} = {comparison.effect_size.value} ({comparison.effect_size.magnitude})"
        for index, group in enumerate(comparison.groups):
            rows.append(
                {
                    "group": group.group_label,
                    "n": group.n,
                    "mean": group.mean,
                    "sd": group.standard_deviation,
                    "statistic": comparison.statistic if index == 0 else None,
                    "degrees_of_freedom": comparison.degrees_of_freedom if index == 0 else None,
                    "p_value": comparison.p_value if index == 0 else None,
                    "effect_size": effect_size_text if index == 0 else "",
                }
            )
        return build_group_comparison_table(
            title=build_table_title(
                "group_comparison",
                f"{comparison.outcome_target.label} segun {comparison.group_target.label}",
            ),
            rows=rows,
            warnings=comparison.warnings,
            source={"form_id": form_id, "source_type": "live"},
            decimals=request.decimals,
        )

    def _categorical_request_from_options(self, form_id: str, request: ApaTableRequest) -> CategoricalAssociationRequest:
        options = request.options or {}
        row_id = self._target_id_from_options(options, "row")
        column_id = self._target_id_from_options(options, "column")
        if row_id is None or column_id is None:
            association_options = self.categorical_association_service.list_categorical_association_options(form_id)
            if row_id is None and association_options.categorical_targets:
                row_id = association_options.categorical_targets[0].target_id
            if column_id is None and len(association_options.categorical_targets) >= 2:
                column_id = association_options.categorical_targets[1].target_id
        if row_id is None or column_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categorical association table requires row and column targets")
        return CategoricalAssociationRequest(
            row=CategoricalAssociationTargetInput(target_type=self._target_type_from_options(options, "row"), target_id=str(row_id)),
            column=CategoricalAssociationTargetInput(target_type=self._target_type_from_options(options, "column"), target_id=str(column_id)),
            method=str(options.get("method", "auto")),
            alpha=float(options.get("alpha", 0.05)),
            decimals=request.decimals,
            include_discarded=request.include_discarded,
            store_result=False,
        )

    def generate_live_categorical_association_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        association = self.categorical_association_service.run_categorical_association(
            form_id,
            self._categorical_request_from_options(form_id, request),
        ).result
        effect_size_text = ""
        if association.effect_size is not None:
            effect_size_text = f"{association.effect_size.name} = {association.effect_size.value} ({association.effect_size.magnitude})"
        rows = [
            {
                "categories": f"{cell.row_value} x {cell.column_value}",
                "n": cell.observed,
                "row_percent": cell.row_percent,
                "column_percent": cell.column_percent,
                "statistic": association.statistic if index == 0 else None,
                "degrees_of_freedom": association.degrees_of_freedom if index == 0 else None,
                "p_value": association.p_value if index == 0 else None,
                "effect_size": effect_size_text if index == 0 else "",
            }
            for index, cell in enumerate(association.cells)
        ]
        return build_categorical_association_table(
            title=build_table_title(
                "categorical_association",
                f"{association.row_target.label} y {association.column_target.label}",
            ),
            rows=rows,
            warnings=association.warnings,
            source={"form_id": form_id, "source_type": "live"},
            decimals=request.decimals,
        )

    def generate_live_scoring_summary_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        results = self.advanced_scoring_service.get_form_score_results(form_id)
        configs = self.advanced_scoring_service._get_scoring_configs(form_id)
        scores = list(self.db.scalars(select(ResponseScore).where(ResponseScore.form_id == form_id)).all())
        rows: list[dict[str, Any]] = []
        warnings = list(results.warnings)
        for config in configs:
            config_scores = [score.final_score for score in scores if score.scoring_config_id == config.id and score.final_score is not None]
            if not config_scores:
                continue
            band_counts: dict[str, int] = {}
            for score in scores:
                if score.scoring_config_id != config.id or not score.band_label:
                    continue
                band_counts[score.band_label] = band_counts.get(score.band_label, 0) + 1
            predominant = max(band_counts.items(), key=lambda item: item[1])[0] if band_counts else ""
            series = pd.Series(config_scores)
            rows.append(
                {
                    "score_name": config.name,
                    "n": len(config_scores),
                    "mean": float(series.mean()),
                    "sd": float(series.std(ddof=1)) if len(config_scores) > 1 else 0.0,
                    "minimum": float(series.min()),
                    "maximum": float(series.max()),
                    "predominant_level": predominant,
                }
            )
        if not rows:
            return self._build_empty_table("scoring_summary", form_id, build_table_title("scoring_summary"), "no_scoring_results")
        return build_scoring_summary_table(
            title=build_table_title("scoring_summary", "puntajes configurados"),
            rows=rows,
            warnings=warnings,
            source={"form_id": form_id, "source_type": "live"},
            decimals=request.decimals,
        )

    def generate_live_score_band_distribution_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        distribution = self.advanced_scoring_service.summarize_bands_distribution(form_id)
        rows = [
            {
                "level": f"{item.scoring_config_name}: {item.level}",
                "n": item.n,
                "percent": item.percent,
                "interpretation": item.interpretation,
            }
            for item in distribution
        ]
        if not rows:
            return self._build_empty_table("score_band_distribution", form_id, build_table_title("score_band_distribution"), "no_scoring_results")
        return build_score_band_distribution_table(
            title=build_table_title("score_band_distribution", "rangos interpretativos"),
            rows=rows,
            warnings=[],
            source={"form_id": form_id, "source_type": "live"},
            decimals=request.decimals,
        )

    def generate_live_control_scale_flags_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        flags = self.advanced_scoring_service.get_control_flag_summary(form_id)
        rows = [
            {
                "control_scale": item.name,
                "status": item.flag_status,
                "n": item.n,
                "percent": item.percent,
            }
            for item in flags
        ]
        if not rows:
            return self._build_empty_table("control_scale_flags", form_id, build_table_title("control_scale_flags"), "no_control_flags")
        return build_control_scale_flags_table(
            title=build_table_title("control_scale_flags", "escalas de control"),
            rows=rows,
            warnings=[],
            source={"form_id": form_id, "source_type": "live"},
            decimals=request.decimals,
        )

    def generate_from_orchestrated_analysis(self, form_id: str, analysis_run_id: str, *, decimals: int) -> ApaTableBatchRead:
        form = self._get_form(form_id)
        analysis_run = self._get_analysis_run(form_id, analysis_run_id)
        if analysis_run.analysis_type != "orchestrated_analysis":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AnalysisRun is not orchestrated_analysis")

        result_json = analysis_run.result_json if isinstance(analysis_run.result_json, dict) else {}
        apa_blocks = result_json.get("apa_table_blocks")
        if not isinstance(apa_blocks, list):
            params = analysis_run.params_json if isinstance(analysis_run.params_json, dict) else {}
            request = OrchestratedAnalysisRequest.model_validate({**params, "store_result": False})
            regenerated = self.analysis_orchestrator_service.run_orchestrated_analysis(form_id, request)
            apa_blocks = [block.model_dump() for block in regenerated.apa_table_blocks]

        tables: list[ApaTableRead] = []
        warnings: list[str] = []
        for block in apa_blocks:
            tables.append(
                build_from_orchestrated_analysis(
                    table_type=block.get("table_type", "orchestrated_summary"),
                    title=block.get("suggested_title") or build_table_title("orchestrated_summary"),
                    rows=block.get("rows", []),
                    columns=block.get("columns", []),
                    source={"form_id": form_id, "source_type": "orchestrated", "analysis_run_id": analysis_run_id},
                    warnings=block.get("notes", []) or [],
                    decimals=decimals,
                    source_result=block.get("source_result"),
                )
            )
            warnings.extend(block.get("notes", []))
        return ApaTableBatchRead(
            form_id=form.id,
            project_id=form.project_id,
            total_tables=len(tables),
            tables=tables,
            warnings=list(dict.fromkeys(warnings)),
        )

    def _request_from_analysis_run(self, analysis_run: AnalysisRun, *, form_id: str, decimals: int, include_discarded: bool, score_aggregation: str) -> ApaTableRequest:
        params = analysis_run.params_json if isinstance(analysis_run.params_json, dict) else {}
        if analysis_run.analysis_type == "descriptive":
            return ApaTableRequest(
                table_type="descriptives",
                source_type="live",
                form_id=form_id,
                options=params,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            )
        if analysis_run.analysis_type == "normality":
            return ApaTableRequest(
                table_type="normality",
                source_type="live",
                form_id=form_id,
                options=params,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            )
        if analysis_run.analysis_type == "correlation":
            table_type = "correlation_matrix" if "targets" in params else "correlation"
            return ApaTableRequest(
                table_type=table_type,
                source_type="live",
                form_id=form_id,
                options=params,
                target_ids=params.get("target_ids"),
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            )
        if analysis_run.analysis_type == "group_comparison":
            return ApaTableRequest(
                table_type="group_comparison",
                source_type="live",
                form_id=form_id,
                options=params,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            )
        if analysis_run.analysis_type == "categorical_association":
            return ApaTableRequest(
                table_type="categorical_association",
                source_type="live",
                form_id=form_id,
                options=params,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            )
        if analysis_run.analysis_type == "advanced_scoring":
            return ApaTableRequest(
                table_type="scoring_summary",
                source_type="live",
                form_id=form_id,
                options=params,
                decimals=decimals,
                include_discarded=include_discarded,
                score_aggregation=score_aggregation,
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported AnalysisRun type for APA table generation")

    def generate_from_analysis_run(
        self,
        form_id: str,
        analysis_run_id: str,
        *,
        decimals: int,
        include_discarded: bool,
        score_aggregation: str,
    ) -> ApaTableBatchRead:
        form = self._get_form(form_id)
        analysis_run = self._get_analysis_run(form_id, analysis_run_id)
        if analysis_run.analysis_type == "orchestrated_analysis":
            return self.generate_from_orchestrated_analysis(form_id, analysis_run_id, decimals=decimals)
        if analysis_run.analysis_type == "advanced_scoring":
            tables = [
                self.generate_apa_table(
                    form_id,
                    ApaTableRequest(
                        table_type=table_type,
                        source_type="live",
                        form_id=form_id,
                        decimals=decimals,
                        include_discarded=include_discarded,
                        score_aggregation=score_aggregation,
                    ),
                )
                for table_type in ["scoring_summary", "score_band_distribution", "control_scale_flags"]
            ]
            warnings = [warning for table in tables for warning in table.warnings]
            return ApaTableBatchRead(
                form_id=form.id,
                project_id=form.project_id,
                total_tables=len(tables),
                tables=tables,
                warnings=list(dict.fromkeys(warnings)),
            )
        request = self._request_from_analysis_run(
            analysis_run,
            form_id=form_id,
            decimals=decimals,
            include_discarded=include_discarded,
            score_aggregation=score_aggregation,
        )
        table = self.generate_apa_table(form_id, request)
        return ApaTableBatchRead(
            form_id=form.id,
            project_id=form.project_id,
            total_tables=1,
            tables=[table],
            warnings=table.warnings,
        )

    def generate_apa_table(self, form_id: str, request: ApaTableRequest) -> ApaTableRead:
        self._get_form(form_id)
        if request.source_type == "analysis_run":
            if not request.analysis_run_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="analysis_run_id is required for source_type analysis_run")
            batch = self.generate_from_analysis_run(
                form_id,
                request.analysis_run_id,
                decimals=request.decimals,
                include_discarded=request.include_discarded,
                score_aggregation=request.score_aggregation,
            )
            return batch.tables[0]
        if request.source_type == "orchestrated":
            if not request.analysis_run_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="analysis_run_id is required for source_type orchestrated")
            batch = self.generate_from_orchestrated_analysis(form_id, request.analysis_run_id, decimals=request.decimals)
            return batch.tables[0]

        if request.table_type == "frequencies":
            return self.generate_live_frequency_table(form_id, request)
        if request.table_type == "descriptives":
            return self.generate_live_descriptive_table(form_id, request)
        if request.table_type == "normality":
            return self.generate_live_normality_table(form_id, request)
        if request.table_type == "correlation":
            return self.generate_live_correlation_table(form_id, request)
        if request.table_type == "correlation_matrix":
            return self.generate_live_correlation_matrix_table(form_id, request)
        if request.table_type == "group_comparison":
            return self.generate_live_group_comparison_table(form_id, request)
        if request.table_type == "categorical_association":
            return self.generate_live_categorical_association_table(form_id, request)
        if request.table_type == "scoring_summary":
            return self.generate_live_scoring_summary_table(form_id, request)
        if request.table_type == "score_band_distribution":
            return self.generate_live_score_band_distribution_table(form_id, request)
        if request.table_type == "control_scale_flags":
            return self.generate_live_control_scale_flags_table(form_id, request)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported live APA table type")

    def generate_apa_tables_batch(self, form_id: str, request: ApaTableBatchRequest) -> ApaTableBatchRead:
        form = self._get_form(form_id)
        tables: list[ApaTableRead] = []
        warnings: list[str] = []
        for table_type in request.table_types:
            table = self.generate_apa_table(
                form_id,
                ApaTableRequest(
                    table_type=table_type,
                    source_type="live",
                    form_id=form_id,
                    options=request.options,
                    decimals=request.decimals,
                    include_discarded=request.include_discarded,
                    score_aggregation=request.score_aggregation,
                ),
            )
            tables.append(table)
            warnings.extend(table.warnings)
        return ApaTableBatchRead(
            form_id=form.id,
            project_id=form.project_id,
            total_tables=len(tables),
            tables=tables,
            warnings=list(dict.fromkeys(warnings)),
        )

    def export_apa_tables(self, form_id: str, request: ApaTableBatchRequest, *, export_format: str) -> ApaTableExportRead:
        form = self._get_form(form_id)
        batch = self.generate_apa_tables_batch(form_id, request)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if export_format == "markdown":
            file_name = f"form_{form.id}_apa_tables_{timestamp}.md"
            file_path = self.exports_dir / file_name
            content = "\n\n---\n\n".join(table.markdown for table in batch.tables)
            file_path.write_text(content, encoding="utf-8")
            mime_type = "text/markdown"
            artifact_type = "apa_table_markdown"
        elif export_format == "html":
            file_name = f"form_{form.id}_apa_tables_{timestamp}.html"
            file_path = self.exports_dir / file_name
            content = "<html><body>\n" + "\n<hr/>\n".join(table.html for table in batch.tables) + "\n</body></html>"
            file_path.write_text(content, encoding="utf-8")
            mime_type = "text/html"
            artifact_type = "apa_table_html"
        elif export_format == "json":
            file_name = f"form_{form.id}_apa_tables_{timestamp}.json"
            file_path = self.exports_dir / file_name
            file_path.write_text(json.dumps(batch.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
            mime_type = "application/json"
            artifact_type = "apa_table_json"
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported export format")

        artifact = self._build_export_artifact(
            form=form,
            artifact_type=artifact_type,
            file_name=file_name,
            file_path=file_path,
            mime_type=mime_type,
            metadata_json={
                "table_types": request.table_types,
                "format": export_format,
                "table_count": batch.total_tables,
            },
        )
        return ApaTableExportRead(
            artifact_id=artifact.id,
            file_name=file_name,
            file_path=file_path.as_posix(),
            mime_type=mime_type,
            table_count=batch.total_tables,
            created_at=artifact.created_at,
        )

    def list_apa_table_options(self, form_id: str) -> ApaTableOptionsRead:
        form = self._get_form(form_id)
        comparison_options = self.group_comparison_service.get_comparison_options(form_id)
        categorical_options = self.categorical_association_service.list_categorical_association_options(form_id)
        analysis_runs = list(
            self.db.scalars(
                select(AnalysisRun)
                .where(AnalysisRun.form_id == form_id)
                .order_by(AnalysisRun.created_at.desc())
                .limit(20)
            ).all()
        )
        recommendations: list[ApaTableRecommendationRead] = []
        if self._categorical_questions(form):
            recommendations.append(ApaTableRecommendationRead(table_type="frequencies", reason="El formulario contiene preguntas categoricas aptas para tablas de frecuencias."))
        if self._numeric_questions(form):
            recommendations.extend(
                [
                    ApaTableRecommendationRead(table_type="descriptives", reason="El formulario contiene variables numericas o puntuadas."),
                    ApaTableRecommendationRead(table_type="normality", reason="Hay targets numericos aptos para resumen de normalidad."),
                ]
            )
        if len(comparison_options.outcomes) >= 1 and len(comparison_options.groups) >= 1:
            recommendations.append(ApaTableRecommendationRead(table_type="group_comparison", reason="Existen outcomes numericos y agrupaciones categoricas compatibles."))
        if len(categorical_options.categorical_targets) >= 2:
            recommendations.append(ApaTableRecommendationRead(table_type="categorical_association", reason="Existen al menos dos variables categoricas para asociacion inferencial."))
        if len(self._numeric_questions(form)) >= 2:
            recommendations.extend(
                [
                    ApaTableRecommendationRead(table_type="correlation", reason="Existen al menos dos variables numericas o puntuadas para correlacion por pares."),
                    ApaTableRecommendationRead(table_type="correlation_matrix", reason="Existen suficientes targets numericos para una matriz de correlaciones."),
                ]
            )
        scoring_results = self.advanced_scoring_service.get_form_score_results(form_id)
        if scoring_results.scored_responses > 0:
            recommendations.extend(
                [
                    ApaTableRecommendationRead(table_type="scoring_summary", reason="Existen puntajes avanzados calculados para resumir instrumentos, dimensiones o variables configuradas."),
                    ApaTableRecommendationRead(table_type="score_band_distribution", reason="Existen baremos asignados y distribuciones por nivel interpretativo."),
                ]
            )
        if scoring_results.control_flags:
            recommendations.append(
                ApaTableRecommendationRead(table_type="control_scale_flags", reason="Existen escalas de control evaluadas con estados de advertencia o invalidez.")
            )

        return ApaTableOptionsRead(
            form_id=form.id,
            table_types=[
                "frequencies",
                "descriptives",
                "normality",
                "correlation",
                "correlation_matrix",
                "group_comparison",
                "categorical_association",
                "scoring_summary",
                "score_band_distribution",
                "control_scale_flags",
                "orchestrated_summary",
            ],
            analysis_runs=[
                CompatibleAnalysisRunRead(id=item.id, analysis_type=item.analysis_type, created_at=item.created_at)
                for item in analysis_runs
            ],
            recommendations=recommendations,
        )
