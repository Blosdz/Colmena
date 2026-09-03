from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.analysis_run import AnalysisRun
from app.models.control_scale import ControlScale
from app.models.form import Form
from app.models.form_answer import FormAnswer
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.models.form_response import FormResponse
from app.models.project import Project
from app.models.response_control_flag import ResponseControlFlag
from app.models.response_score import ResponseScore
from app.models.score_band import ScoreBand
from app.models.scoring_config import ScoringConfig
from app.schemas.dataset import DatasetColumnRead, DatasetRead
from app.schemas.scoring import (
    BaremoLevelRead,
    BaremoResolutionRead,
    ControlScaleRead,
    ControlScaleSummaryRead,
    ResponseControlFlagRead,
    ResponseScoreRead,
    ScoredDatasetRead,
    ScoringConfigRead,
    ScoringBandDistributionRead,
    ScoringOptionsRead,
    ScoringPreviewRead,
    ScoringResultsRead,
    ScoringRunRead,
    ScoringRunRequest,
    VariableBaremoRead,
)
from app.scoring.band_engine import build_band_interpretation, resolve_score_band, validate_bands_no_overlap
from app.scoring.baremo_engine import (
    compute_equal_range_baremo,
    compute_mean_sd_baremo,
    compute_percentile_baremo,
    levels_from_score_bands,
    resolve_level_for_score,
)
from app.scoring.control_scale_engine import evaluate_control_scale
from app.scoring.scoring_engine import compute_response_score
from app.scoring.scoring_warnings import control_scale_invalid, control_scale_warning, no_bands_configured, overlapping_bands
from app.services.dataset_service import DatasetService
from app.services.descriptive_service import DescriptiveService


class AdvancedScoringService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)
        self.descriptive_service = DescriptiveService(db)

    def _get_form(self, form_id: str) -> Form:
        form = self.db.scalar(
            select(Form)
            .options(
                selectinload(Form.project).selectinload(Project.variables),
                selectinload(Form.instruments).selectinload(FormInstrument.dimensions),
                selectinload(Form.questions).selectinload(FormQuestion.options),
                selectinload(Form.responses).selectinload(FormResponse.answers),
            )
            .where(Form.id == form_id, Form.deleted_at.is_(None))
        )
        if form is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
        return form

    def _get_response(self, response_id: str) -> FormResponse:
        response = self.db.scalar(
            select(FormResponse)
            .options(
                selectinload(FormResponse.answers).selectinload(FormAnswer.question),
                selectinload(FormResponse.scores),
                selectinload(FormResponse.control_flags),
            )
            .where(FormResponse.id == response_id, FormResponse.deleted_at.is_(None))
        )
        if response is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form response not found")
        return response

    def _get_scoring_configs(self, form_id: str) -> list[ScoringConfig]:
        return list(
            self.db.scalars(
                select(ScoringConfig)
                .options(selectinload(ScoringConfig.score_bands))
                .where(
                    ScoringConfig.form_id == form_id,
                    ScoringConfig.deleted_at.is_(None),
                    ScoringConfig.is_active.is_(True),
                )
                .order_by(ScoringConfig.created_at.asc())
            ).all()
        )

    def _get_control_scales(self, form_id: str) -> list[ControlScale]:
        return list(
            self.db.scalars(
                select(ControlScale)
                .options(selectinload(ControlScale.items))
                .where(
                    ControlScale.form_id == form_id,
                    ControlScale.deleted_at.is_(None),
                    ControlScale.is_active.is_(True),
                )
                .order_by(ControlScale.created_at.asc())
            ).all()
        )

    def _active_questions(self, form: Form) -> list[FormQuestion]:
        return [question for question in form.questions if question.deleted_at is None]

    def _answer_map(self, response: FormResponse) -> dict[str, Any]:
        return {answer.question_id: answer for answer in response.answers}

    def _options_by_question_id(self, questions: list[FormQuestion]) -> dict[str, dict[str, FormQuestionOption]]:
        return {
            question.id: {
                option.id: option
                for option in question.options
                if option.deleted_at is None
            }
            for question in questions
        }

    def store_response_score(self, payload: dict[str, Any]) -> ResponseScore:
        existing = self.db.scalar(
            select(ResponseScore).where(
                ResponseScore.response_id == payload["response_id"],
                ResponseScore.scoring_config_id == payload["scoring_config_id"],
            )
        )
        if existing is None:
            existing = ResponseScore(**payload)
            self.db.add(existing)
        else:
            for field, value in payload.items():
                setattr(existing, field, value)
        self.db.flush()
        return existing

    def store_response_control_flag(self, payload: dict[str, Any]) -> ResponseControlFlag:
        existing = self.db.scalar(
            select(ResponseControlFlag).where(
                ResponseControlFlag.response_id == payload["response_id"],
                ResponseControlFlag.control_scale_id == payload["control_scale_id"],
            )
        )
        if existing is None:
            existing = ResponseControlFlag(**payload)
            self.db.add(existing)
        else:
            for field, value in payload.items():
                setattr(existing, field, value)
        self.db.flush()
        return existing

    def _serialize_score_result(self, score: ResponseScore | dict[str, Any]) -> ResponseScoreRead:
        if isinstance(score, dict):
            now = datetime.now(timezone.utc)
            payload = {
                "id": score.get("id", f"preview-score-{score.get('response_id', 'na')}-{score.get('scoring_config_id', 'na')}"),
                "created_at": score.get("created_at", now),
                "updated_at": score.get("updated_at", now),
                **score,
            }
            return ResponseScoreRead(**payload)
        return ResponseScoreRead.model_validate(score)

    def _serialize_flag_result(self, flag: ResponseControlFlag | dict[str, Any]) -> ResponseControlFlagRead:
        if isinstance(flag, dict):
            now = datetime.now(timezone.utc)
            payload = {
                "id": flag.get("id", f"preview-flag-{flag.get('response_id', 'na')}-{flag.get('control_scale_id', 'na')}"),
                "created_at": flag.get("created_at", now),
                "updated_at": flag.get("updated_at", now),
                **flag,
            }
            return ResponseControlFlagRead(**payload)
        return ResponseControlFlagRead.model_validate(flag)

    def run_scoring_for_response(
        self,
        response_id: str,
        *,
        recalculate: bool = True,
        store_result: bool = True,
    ) -> tuple[list[ResponseScoreRead], list[ResponseControlFlagRead], list[str]]:
        response = self._get_response(response_id)
        form = self._get_form(response.form_id)
        configs = self._get_scoring_configs(form.id)
        control_scales = self._get_control_scales(form.id)
        questions = self._active_questions(form)
        answers = self._answer_map(response)
        options_by_question_id = self._options_by_question_id(questions)
        warnings: list[str] = []

        flag_results: list[dict[str, Any]] = []
        for control_scale in control_scales:
            result = evaluate_control_scale(response, control_scale, answers)
            payload = {
                "project_id": response.project_id,
                "form_id": response.form_id,
                "response_id": response.id,
                "control_scale_id": control_scale.id,
                **result,
            }
            flag_results.append(payload)
            if payload["flag_status"] == "warning":
                warnings.append(control_scale_warning())
            if payload["flag_status"] == "invalid":
                warnings.append(control_scale_invalid())

        overall_validity = "valid"
        if any(flag["flag_status"] == "invalid" for flag in flag_results):
            overall_validity = "invalid"
        elif any(flag["flag_status"] == "warning" for flag in flag_results):
            overall_validity = "warning"

        score_results: list[dict[str, Any]] = []
        for config in configs:
            result = compute_response_score(response, config, answers, questions, options_by_question_id)
            band_warnings = validate_bands_no_overlap(config.score_bands)
            if band_warnings:
                warnings.extend(band_warnings)
            band = resolve_score_band(result["final_score"], config.score_bands)
            interpretation = build_band_interpretation(result["final_score"], band) if config.interpretation_enabled else None
            if config.interpretation_enabled and not config.score_bands:
                result["warnings_json"] = [*(result["warnings_json"] or []), no_bands_configured()]
            result.update(
                {
                    "band_id": band.id if band is not None else None,
                    "band_label": band.label if band is not None else None,
                    "interpretation": interpretation,
                    "validity_status": overall_validity if result["final_score"] is not None else "warning",
                    "warnings_json": list(dict.fromkeys([*(result["warnings_json"] or []), *band_warnings])),
                }
            )
            score_results.append(result)

        if store_result:
            if recalculate:
                existing_scores = list(self.db.scalars(select(ResponseScore).where(ResponseScore.response_id == response.id)).all())
                existing_flags = list(self.db.scalars(select(ResponseControlFlag).where(ResponseControlFlag.response_id == response.id)).all())
                for item in existing_scores:
                    self.db.delete(item)
                for item in existing_flags:
                    self.db.delete(item)
                self.db.flush()
            stored_scores = [self.store_response_score(item) for item in score_results]
            stored_flags = [self.store_response_control_flag(item) for item in flag_results]
            self.db.commit()
            return (
                [self._serialize_score_result(item) for item in stored_scores],
                [self._serialize_flag_result(item) for item in stored_flags],
                list(dict.fromkeys(warnings)),
            )
        return (
            [self._serialize_score_result(item) for item in score_results],
            [self._serialize_flag_result(item) for item in flag_results],
            list(dict.fromkeys(warnings)),
        )

    def preview_scoring(self, form_id: str, include_discarded: bool = False) -> ScoringPreviewRead:
        form = self._get_form(form_id)
        responses = [
            response
            for response in form.responses
            if response.deleted_at is None and (include_discarded or response.status != "discarded")
        ]
        warnings: list[str] = []
        score_results: list[ResponseScoreRead] = []
        control_flags: list[ResponseControlFlagRead] = []
        for response in responses[:10]:
            response_scores, response_flags, response_warnings = self.run_scoring_for_response(response.id, store_result=False)
            score_results.extend(response_scores)
            control_flags.extend(response_flags)
            warnings.extend(response_warnings)
        return ScoringPreviewRead(
            form_id=form.id,
            warnings=list(dict.fromkeys(warnings)),
            score_results=score_results,
            control_flags=control_flags,
        )

    def run_scoring_for_form(self, form_id: str, request: ScoringRunRequest) -> ScoringRunRead:
        form = self._get_form(form_id)
        responses = [
            response
            for response in form.responses
            if response.deleted_at is None and (request.include_discarded or response.status != "discarded")
        ]
        warnings: list[str] = []
        score_results: list[ResponseScoreRead] = []
        control_flags: list[ResponseControlFlagRead] = []
        for response in responses:
            response_scores, response_flags, response_warnings = self.run_scoring_for_response(
                response.id,
                recalculate=request.recalculate,
                store_result=request.store_result,
            )
            score_results.extend(response_scores)
            control_flags.extend(response_flags)
            warnings.extend(response_warnings)

        valid_responses = len({item.response_id for item in score_results if item.validity_status == "valid"})
        warning_responses = len({item.response_id for item in score_results if item.validity_status == "warning"})
        invalid_responses = len({item.response_id for item in score_results if item.validity_status == "invalid"})
        analysis_run = None
        if request.store_result:
            analysis_run = AnalysisRun(
                project_id=form.project_id,
                form_id=form.id,
                analysis_type="advanced_scoring",
                status="completed_with_warnings" if warnings else "completed",
                params_json=request.model_dump(),
                result_json={
                    "total_responses": len(responses),
                    "scored_responses": len({item.response_id for item in score_results}),
                    "valid_responses": valid_responses,
                    "warning_responses": warning_responses,
                    "invalid_responses": invalid_responses,
                    "warnings": list(dict.fromkeys(warnings)),
                },
            )
            self.db.add(analysis_run)
            self.db.commit()
            self.db.refresh(analysis_run)

        return ScoringRunRead(
            analysis_run_id=analysis_run.id if analysis_run is not None else None,
            form_id=form.id,
            project_id=form.project_id,
            total_responses=len(responses),
            scored_responses=len({item.response_id for item in score_results}),
            valid_responses=valid_responses,
            warning_responses=warning_responses,
            invalid_responses=invalid_responses,
            warnings=list(dict.fromkeys(warnings)),
            score_results=score_results,
            control_flags=control_flags,
        )

    def get_response_scores(self, response_id: str) -> list[ResponseScoreRead]:
        response = self._get_response(response_id)
        items = list(
            self.db.scalars(
                select(ResponseScore)
                .where(ResponseScore.response_id == response.id)
                .order_by(ResponseScore.created_at.asc())
            ).all()
        )
        return [ResponseScoreRead.model_validate(item) for item in items]

    def summarize_bands_distribution(self, form_id: str) -> list[ScoringBandDistributionRead]:
        configs = self._get_scoring_configs(form_id)
        scores = list(self.db.scalars(select(ResponseScore).where(ResponseScore.form_id == form_id)).all())
        grouped: dict[tuple[str, str], list[ResponseScore]] = defaultdict(list)
        for score in scores:
            grouped[(score.scoring_config_id, score.band_label or "Sin clasificar")].append(score)
        total_by_config: dict[str, int] = defaultdict(int)
        for score in scores:
            total_by_config[score.scoring_config_id] += 1
        config_by_id = {config.id: config for config in configs}
        band_lookup: dict[tuple[str, str], ScoreBand | None] = {}
        for config in configs:
            for band in config.score_bands:
                if band.deleted_at is None:
                    band_lookup[(config.id, band.label)] = band
        rows: list[ScoringBandDistributionRead] = []
        for (config_id, label), items in grouped.items():
            total = total_by_config.get(config_id, 0)
            band = band_lookup.get((config_id, label))
            rows.append(
                ScoringBandDistributionRead(
                    scoring_config_id=config_id,
                    scoring_config_name=config_by_id.get(config_id).name if config_id in config_by_id else config_id,
                    level=label,
                    n=len(items),
                    percent=round((len(items) / total) * 100, 3) if total else 0.0,
                    interpretation=getattr(band, "interpretation", None),
                )
            )
        return sorted(rows, key=lambda item: (item.scoring_config_name.lower(), item.level.lower()))

    def _summarize_control_flags(self, form_id: str) -> list[ControlScaleSummaryRead]:
        scales = {scale.id: scale for scale in self._get_control_scales(form_id)}
        flags = list(self.db.scalars(select(ResponseControlFlag).where(ResponseControlFlag.form_id == form_id)).all())
        grouped: dict[tuple[str, str], list[ResponseControlFlag]] = defaultdict(list)
        totals: dict[str, int] = defaultdict(int)
        for flag in flags:
            grouped[(flag.control_scale_id, flag.flag_status)].append(flag)
            totals[flag.control_scale_id] += 1
        rows: list[ControlScaleSummaryRead] = []
        for (control_scale_id, flag_status), items in grouped.items():
            total = totals.get(control_scale_id, 0)
            rows.append(
                ControlScaleSummaryRead(
                    control_scale_id=control_scale_id,
                    name=scales.get(control_scale_id).name if control_scale_id in scales else control_scale_id,
                    flag_status=flag_status,
                    n=len(items),
                    percent=round((len(items) / total) * 100, 3) if total else 0.0,
                )
            )
        return sorted(rows, key=lambda item: (item.name.lower(), item.flag_status))

    def get_control_flag_summary(self, form_id: str) -> list[ControlScaleSummaryRead]:
        return self._summarize_control_flags(form_id)

    def get_form_score_results(self, form_id: str) -> ScoringResultsRead:
        form = self._get_form(form_id)
        scores = list(self.db.scalars(select(ResponseScore).where(ResponseScore.form_id == form.id)).all())
        response_ids = {score.response_id for score in scores}
        valid_responses = len({score.response_id for score in scores if score.validity_status == "valid"})
        warning_responses = len({score.response_id for score in scores if score.validity_status == "warning"})
        invalid_responses = len({score.response_id for score in scores if score.validity_status == "invalid"})
        warnings: list[str] = []
        if not form.responses:
            warnings.append("no_responses")
        if any("overlapping_bands" in (score.warnings_json or []) for score in scores):
            warnings.append(overlapping_bands())
        return ScoringResultsRead(
            form_id=form.id,
            total_responses=len([response for response in form.responses if response.deleted_at is None]),
            scored_responses=len(response_ids),
            valid_responses=valid_responses,
            warning_responses=warning_responses,
            invalid_responses=invalid_responses,
            band_distribution=self.summarize_bands_distribution(form.id),
            control_flags=self._summarize_control_flags(form.id),
            warnings=list(dict.fromkeys(warnings)),
        )

    def _variable_label_for_config(self, config: ScoringConfig) -> str:
        if config.project_variable is not None:
            return config.project_variable.name
        if config.dimension is not None:
            return config.dimension.name
        if config.instrument is not None:
            return config.instrument.name
        return config.name

    def resolve_variable_baremos(
        self,
        form_id: str,
        levels_count: int = 3,
        baremo_method: str = "equal_range",
    ) -> BaremoResolutionRead:
        form = self._get_form(form_id)
        configs = self._get_scoring_configs(form.id)
        scores = list(self.db.scalars(select(ResponseScore).where(ResponseScore.form_id == form.id)).all())
        warnings: list[str] = []
        if not configs:
            warnings.append("no_scoring_configs")

        active_responses = [
            response
            for response in form.responses
            if response.deleted_at is None and response.status != "discarded"
        ]
        if configs and not scores and active_responses:
            for response in active_responses:
                self.run_scoring_for_response(response.id, store_result=True)
            scores = list(self.db.scalars(select(ResponseScore).where(ResponseScore.form_id == form.id)).all())
            warnings.append("scores_computed_during_resolution")

        items: list[VariableBaremoRead] = []
        for config in configs:
            config_scores = [
                float(score.final_score)
                for score in scores
                if score.scoring_config_id == config.id and score.final_score is not None
            ]
            config_warnings: list[str] = []
            score_min = float(config.score_min) if config.score_min is not None else (min(config_scores) if config_scores else None)
            score_max = float(config.score_max) if config.score_max is not None else (max(config_scores) if config_scores else None)
            if config.score_min is None or config.score_max is None:
                if config_scores:
                    config_warnings.append("theoretical_range_missing_used_observed")

            band_levels = levels_from_score_bands(config.score_bands)
            levels = []
            baremo_source = "unavailable"
            if band_levels:
                levels = band_levels
                baremo_source = "configured_bands"
            elif baremo_method == "percentile" and len(config_scores) >= 2:
                levels = compute_percentile_baremo(config_scores, levels_count)
                if levels:
                    baremo_source = "percentile_formula"
                    config_warnings.append("baremo_computed_with_percentile_formula")
            elif baremo_method == "mean_sd" and len(config_scores) >= 2:
                levels = compute_mean_sd_baremo(config_scores, levels_count)
                if levels:
                    baremo_source = "mean_sd_formula"
                    config_warnings.append("baremo_computed_with_mean_sd_formula")
                else:
                    config_warnings.append("baremo_mean_sd_zero_variance")

            if not levels and score_min is not None and score_max is not None and score_min < score_max:
                # Puntajes en escala continua 0-100 → cortes continuos (33.3 / 66.6),
                # nunca la variante de rango entero pensada para sumas de ítems.
                levels = compute_equal_range_baremo(
                    score_min, score_max, levels_count, aggregation_method="mean"
                )
                baremo_source = "equal_range_formula"
                config_warnings.append("baremo_computed_with_equal_range_formula")
            elif not levels:
                baremo_source = "unavailable"
                config_warnings.append("baremo_range_unavailable")

            total = len(config_scores)
            level_reads = [
                BaremoLevelRead(
                    **level,
                    n=sum(1 for value in config_scores if level["min_value"] <= value <= level["max_value"]),
                    percent=round(
                        (sum(1 for value in config_scores if level["min_value"] <= value <= level["max_value"]) / total) * 100,
                        3,
                    )
                    if total
                    else 0.0,
                )
                for level in levels
            ]

            mean_score = round(sum(config_scores) / total, 3) if total else None
            sd_score = None
            if total > 1:
                mean_raw = sum(config_scores) / total
                sd_score = round((sum((value - mean_raw) ** 2 for value in config_scores) / (total - 1)) ** 0.5, 3)
            mean_level = resolve_level_for_score(mean_score, levels)

            items.append(
                VariableBaremoRead(
                    scoring_config_id=config.id,
                    scoring_config_name=config.name,
                    variable_label=self._variable_label_for_config(config),
                    scoring_level=config.scoring_level,
                    score_min=score_min,
                    score_max=score_max,
                    baremo_source=baremo_source,
                    valid_n=total,
                    mean_score=mean_score,
                    sd_score=sd_score,
                    mean_level=mean_level["label"] if mean_level is not None else None,
                    mean_interpretation=mean_level.get("interpretation") if mean_level is not None else None,
                    levels=level_reads,
                    warnings=config_warnings,
                )
            )
            warnings.extend(config_warnings)

        return BaremoResolutionRead(
            form_id=form.id,
            project_id=form.project_id,
            resolved_variables=len(items),
            items=items,
            warnings=list(dict.fromkeys(warnings)),
        )

    def _score_columns_for_response(self, response_id: str) -> dict[str, Any]:
        scores = list(
            self.db.scalars(
                select(ResponseScore)
                .join(ScoringConfig, ScoringConfig.id == ResponseScore.scoring_config_id)
                .where(ResponseScore.response_id == response_id)
            ).all()
        )
        rows: dict[str, Any] = {}
        for score in scores:
            config = self.db.scalar(select(ScoringConfig).where(ScoringConfig.id == score.scoring_config_id))
            if config is None:
                continue
            code = config.code or config.id
            rows[f"score_{code}"] = score.final_score
            rows[f"band_{code}"] = score.band_label
            rows[f"interpretation_{code}"] = score.interpretation
            rows[f"validity_{code}"] = score.validity_status
        return rows

    def integrate_scores_into_dataset(
        self,
        dataset: DatasetRead,
    ) -> DatasetRead:
        rows = []
        extra_columns: list[DatasetColumnRead] = []
        existing_column_names = {column.name for column in dataset.columns}
        config_items = {config.id: config for config in self._get_scoring_configs(dataset.form_id)}
        for row in dataset.rows:
            response_id = row.get("response_id")
            score_payload = self._score_columns_for_response(str(response_id)) if response_id else {}
            enriched = {**row, **score_payload}
            rows.append(enriched)
        for config in config_items.values():
            code = config.code or config.id
            for column_name, label in [
                (f"score_{code}", f"Puntaje {config.name}"),
                (f"band_{code}", f"Nivel {config.name}"),
                (f"interpretation_{code}", f"Interpretacion {config.name}"),
                (f"validity_{code}", f"Validez {config.name}"),
            ]:
                if column_name not in existing_column_names:
                    extra_columns.append(DatasetColumnRead(name=column_name, label=label, question_id=None, kind="score"))
                    existing_column_names.add(column_name)
        return DatasetRead(
            form_id=dataset.form_id,
            mode=dataset.mode,
            total_rows=dataset.total_rows,
            total_columns=len(dataset.columns) + len(extra_columns),
            columns=[*dataset.columns, *extra_columns],
            rows=rows,
        )

    def get_scored_dataset(self, form_id: str, include_discarded: bool = False) -> ScoredDatasetRead:
        dataset = self.dataset_service.build_form_dataset(
            form_id,
            mode="mixed",
            include_metadata=True,
            include_discarded=include_discarded,
            expand_multiple_choice=False,
            limit=1000,
            offset=0,
        )
        enriched = self.integrate_scores_into_dataset(dataset)
        return ScoredDatasetRead(
            form_id=form_id,
            total_rows=enriched.total_rows,
            columns=[column.name for column in enriched.columns],
            rows=enriched.rows,
            warnings=[],
        )

    def get_scoring_options(self, form_id: str) -> ScoringOptionsRead:
        form = self._get_form(form_id)
        configs = self._get_scoring_configs(form.id)
        control_scales = self._get_control_scales(form.id)
        questions = self._active_questions(form)
        return ScoringOptionsRead(
            form_id=form.id,
            instruments=[
                {"id": instrument.id, "name": instrument.name}
                for instrument in form.instruments
                if instrument.deleted_at is None
            ],
            dimensions=[
                {"id": dimension.id, "name": dimension.name, "instrument_id": dimension.instrument_id}
                for instrument in form.instruments
                if instrument.deleted_at is None
                for dimension in instrument.dimensions
                if dimension.deleted_at is None
            ],
            scored_questions=[
                {"id": question.id, "label": question.label, "code": question.code}
                for question in questions
                if question.is_scored
            ],
            reverse_scored_questions=[
                {"id": question.id, "label": question.label, "code": question.code}
                for question in questions
                if question.is_reverse_scored
            ],
            configs=[ScoringConfigRead.model_validate(item) for item in configs],
            control_scales=[ControlScaleRead.model_validate(item) for item in control_scales],
        )
