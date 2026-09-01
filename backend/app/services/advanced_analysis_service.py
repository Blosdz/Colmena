"""Análisis sobre puntajes Likert agregados y variables exógenas."""

from __future__ import annotations

import math
import statistics
from datetime import UTC, datetime
from itertools import combinations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analytics.binning import bin_points
from app.analytics.inferential import (
    compute_kruskal_wallis,
    compute_mann_whitney,
    compute_spearman,
)
from app.analytics.multiple_testing import adjust_pvalues_bh
from app.analytics.normality import compute_normality
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InsufficientSampleError,
    NotFoundError,
    ValidationDomainError,
)
from app.models.analysis import AnalysisResult, AnalysisRun
from app.models.censopas import ConstructScore
from app.models.construct import Construct
from app.models.response import Response
from app.models.study import Study
from app.models.user import User
from app.models.variable import Variable
from app.repositories.analytics import AnalyticsRepository
from app.repositories.responses import valid_session_ids
from app.schemas.analytics import (
    ConstructCompareGroupsRequest,
    ConstructCompareGroupsResponse,
    GroupSummaryRead,
    NormalityRequest,
    NormalityResponse,
    NormalityResultRead,
    SpearmanCellRead,
    SpearmanMatrixRequest,
    SpearmanMatrixResponse,
    SpearmanPointBin,
    SpearmanVariableRead,
)
from app.services.authorization_service import user_has_elevated_role


class AdvancedAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AnalyticsRepository(session)

    async def _study(self, study_id: int) -> Study:
        study = await self.session.get(Study, study_id)
        if study is None:
            raise NotFoundError(f"Estudio {study_id} no encontrado")
        return study

    async def _latest_scoring_run(self, study_id: int) -> AnalysisRun:
        stmt = (
            select(AnalysisRun)
            .where(
                AnalysisRun.study_id == study_id,
                AnalysisRun.analysis_type == "LIKERT_SCORING",
                AnalysisRun.status == "COMPLETED",
            )
            .order_by(AnalysisRun.completed_at.desc(), AnalysisRun.id.desc())
        )
        run = (await self.session.execute(stmt)).scalars().first()
        if run is None:
            raise ValidationDomainError(
                "Primero ejecute el scoring Likert del estudio para analizar sus constructos."
            )
        return run

    async def _construct_series(
        self, study_id: int, construct_ids: list[int] | None = None
    ) -> tuple[AnalysisRun, dict[int, tuple[Construct, dict[int, float]]]]:
        run = await self._latest_scoring_run(study_id)
        stmt = (
            select(ConstructScore)
            .where(
                ConstructScore.analysis_run_id == run.id,
                ConstructScore.score_0_100.is_not(None),
            )
            .options(selectinload(ConstructScore.construct))
        )
        if construct_ids:
            stmt = stmt.where(ConstructScore.construct_id.in_(construct_ids))
        scores = list((await self.session.execute(stmt)).scalars().all())
        series: dict[int, tuple[Construct, dict[int, float]]] = {}
        for score in scores:
            if score.construct_id not in series:
                series[score.construct_id] = (score.construct, {})
            series[score.construct_id][1][score.response_session_id] = float(score.score_0_100)
        if construct_ids and set(construct_ids) - set(series):
            missing = sorted(set(construct_ids) - set(series))
            raise NotFoundError(f"No hay puntajes para los constructos {missing} en la última corrida")
        return run, series

    async def _new_run(self, study_id: int, analysis_type: str, parameters: dict) -> AnalysisRun:
        run = AnalysisRun(
            study_id=study_id,
            analysis_type=analysis_type,
            engine="PYTHON",
            engine_version="scipy",
            algorithm_version="analytics-v1",
            parameters=parameters,
            status="RUNNING",
            started_at=datetime.now(UTC),
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def run_normality(
        self, study_id: int, payload: NormalityRequest
    ) -> NormalityResponse:
        study = await self._study(study_id)
        scoring_run, series = await self._construct_series(study_id, payload.construct_ids)
        run = await self._new_run(
            study_id,
            "NORMALITY",
            {
                "construct_ids": payload.construct_ids,
                "histogram_bins": payload.histogram_bins,
                "scoring_run_id": scoring_run.id,
            },
        )
        results: list[NormalityResultRead] = []
        try:
            for construct_id, (construct, values_by_session) in series.items():
                stats = compute_normality(
                    list(values_by_session.values()), payload.histogram_bins
                )
                if study.study_type == "CENSO" and stats["n"] < study.min_publishable_n:
                    stats.update(
                        test=None,
                        statistic=None,
                        p_value=None,
                        status="SUPRIMIDO",
                        mean=None,
                        median=None,
                        standard_deviation=None,
                        minimum=None,
                        maximum=None,
                        histogram=[],
                        warnings=[
                            f"Resultado suprimido por privacidad: n < {study.min_publishable_n}."
                        ],
                    )
                result = NormalityResultRead(
                    construct_id=construct_id,
                    construct_code=construct.code,
                    construct_name=construct.name,
                    **stats,
                )
                results.append(result)
                self.session.add(
                    AnalysisResult(
                        analysis_run_id=run.id,
                        result_code=construct.code,
                        result_type="NORMALITY",
                        construct_id=construct_id,
                        n_valid=result.n,
                        statistic_value=result.statistic,
                        p_value=result.p_value,
                        text_value=result.status,
                        result_data=result.model_dump(mode="json"),
                    )
                )
            run.status = "COMPLETED"
            run.completed_at = datetime.now(UTC)
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            raise exc
        return NormalityResponse(
            analysis_run_id=run.id,
            study_id=study_id,
            note=(
                "La normalidad es complementaria. Las correlaciones entre puntajes Likert "
                "se calculan con Spearman independientemente de este resultado."
            ),
            results=results,
        )

    async def _exogenous_series(
        self, study: Study, variable_ids: list[int]
    ) -> tuple[dict[str, tuple[SpearmanVariableRead, dict[int, float]]], list[str]]:
        series: dict[str, tuple[SpearmanVariableRead, dict[int, float]]] = {}
        excluded: list[str] = []
        for variable_id in variable_ids:
            variable = await self.session.get(Variable, variable_id)
            if variable is None or variable.project_id != study.project_id:
                raise NotFoundError(f"Variable exógena {variable_id} no encontrada en el proyecto")
            if variable.variable_type != "EXOGENOUS" or variable.role != "EXOGENOUS":
                raise ValidationDomainError(f"La variable {variable.code} no es exógena.")
            if variable.measurement_level not in ("ORDINAL", "SCALE", "BINARY"):
                excluded.append(
                    f"{variable.code}: nivel {variable.measurement_level} no es ordenable; "
                    "úselo para segmentación o comparación de grupos."
                )
                continue
            if variable.question_id is None:
                excluded.append(f"{variable.code}: no está vinculada a una pregunta.")
                continue
            stmt = select(
                Response.response_session_id,
                Response.numeric_value,
                Response.raw_code,
                Response.boolean_value,
            ).where(
                Response.study_id == study.id,
                Response.question_id == variable.question_id,
                Response.is_missing.is_(False),
                Response.response_session_id.in_(valid_session_ids(study.id)),
            )
            values: dict[int, float] = {}
            for session_id, numeric_value, raw_code, boolean_value in (
                await self.session.execute(stmt)
            ).all():
                if numeric_value is not None:
                    values[session_id] = float(numeric_value)
                elif boolean_value is not None:
                    values[session_id] = 1.0 if boolean_value else 0.0
                elif raw_code is not None:
                    try:
                        values[session_id] = float(raw_code)
                    except ValueError:
                        continue
            key = f"variable:{variable.id}"
            series[key] = (
                SpearmanVariableRead(
                    key=key,
                    source_type="EXOGENOUS",
                    source_id=variable.id,
                    code=variable.code,
                    label=variable.label or variable.name,
                    measurement_level=variable.measurement_level,
                ),
                values,
            )
        return series, excluded

    @staticmethod
    def _magnitude(rho: float) -> str:
        value = abs(rho)
        if value < 0.1:
            return "DESPRECIABLE"
        if value < 0.3:
            return "DÉBIL"
        if value < 0.5:
            return "MODERADA"
        return "FUERTE"

    async def run_spearman_matrix(
        self,
        study_id: int,
        payload: SpearmanMatrixRequest,
        current_user: User | None = None,
    ) -> SpearmanMatrixResponse:
        study = await self._study(study_id)
        if payload.include_points:
            # E-09: los puntos individuales (aunque agregados en bins) sólo
            # se calculan para un usuario identificado con rol elevado sobre
            # el proyecto del estudio — nunca para un caller anónimo.
            if current_user is None:
                raise AuthenticationError(
                    "Se requiere autenticación para solicitar include_points=true."
                )
            if not await user_has_elevated_role(self.session, study.project_id, current_user):
                raise AuthorizationError(
                    "Su rol no permite solicitar puntos individuales de este estudio."
                )
        scoring_run, constructs = await self._construct_series(study_id, payload.construct_ids)
        all_series: dict[str, tuple[SpearmanVariableRead, dict[int, float]]] = {}
        for construct_id, (construct, values) in constructs.items():
            key = f"construct:{construct_id}"
            all_series[key] = (
                SpearmanVariableRead(
                    key=key,
                    source_type="CONSTRUCT",
                    source_id=construct_id,
                    code=construct.code,
                    label=construct.name,
                    measurement_level="ORDINAL_AGGREGATED",
                ),
                values,
            )
        exogenous, excluded = await self._exogenous_series(
            study, payload.exogenous_variable_ids
        )
        all_series.update(exogenous)
        if len(all_series) < 2:
            raise ValidationDomainError(
                "Seleccione al menos dos constructos o variables ordenables para correlacionar."
            )

        run = await self._new_run(
            study_id,
            "SPEARMAN_MATRIX",
            {
                "construct_ids": payload.construct_ids,
                "exogenous_variable_ids": payload.exogenous_variable_ids,
                "scoring_run_id": scoring_run.id,
                "correction": "BENJAMINI_HOCHBERG",
            },
        )
        cells: list[SpearmanCellRead] = []
        valid_indices: list[int] = []
        p_values: list[float] = []
        keys = list(all_series)
        try:
            for x_key, y_key in combinations(keys, 2):
                _, x_values = all_series[x_key]
                _, y_values = all_series[y_key]
                common = sorted(set(x_values) & set(y_values))
                warnings: list[str] = []
                rho = p_value = None
                privacy_suppressed = (
                    study.study_type == "CENSO"
                    and len(common) < study.min_publishable_n
                )
                if privacy_suppressed:
                    warnings.append(
                        f"Resultado suprimido por privacidad: n < {study.min_publishable_n}."
                    )
                elif len(common) < 3:
                    warnings.append("Se requieren al menos 3 pares válidos.")
                elif len({x_values[item] for item in common}) < 2 or len(
                    {y_values[item] for item in common}
                ) < 2:
                    warnings.append("Una de las series no tiene variabilidad.")
                else:
                    computed = compute_spearman(
                        [x_values[item] for item in common],
                        [y_values[item] for item in common],
                    )
                    if not math.isnan(computed["statistic"]):
                        rho = computed["statistic"]
                        p_value = computed["p_value"]
                cell = SpearmanCellRead(
                    x_key=x_key,
                    y_key=y_key,
                    rho=rho,
                    p_value=p_value,
                    adjusted_p_value=None,
                    n=len(common),
                    magnitude=self._magnitude(rho) if rho is not None else None,
                    significant=False,
                    points_binned=(
                        [
                            SpearmanPointBin(**bucket)
                            for bucket in bin_points(
                                [(x_values[item], y_values[item]) for item in common]
                            )
                        ]
                        if payload.include_points and not privacy_suppressed
                        else []
                    ),
                    warnings=warnings,
                )
                cells.append(cell)
                if p_value is not None:
                    valid_indices.append(len(cells) - 1)
                    p_values.append(p_value)

            adjusted = adjust_pvalues_bh(p_values)
            for index, adjusted_p in zip(valid_indices, adjusted, strict=True):
                cells[index].adjusted_p_value = adjusted_p
                cells[index].significant = adjusted_p < 0.05

            for cell in cells:
                x_variable = all_series[cell.x_key][0]
                y_variable = all_series[cell.y_key][0]
                self.session.add(
                    AnalysisResult(
                        analysis_run_id=run.id,
                        result_code=f"{x_variable.code}_x_{y_variable.code}",
                        result_type="SPEARMAN",
                        n_valid=cell.n,
                        statistic_value=cell.rho,
                        p_value=cell.p_value,
                        adjusted_p_value=cell.adjusted_p_value,
                        effect_size=cell.rho,
                        effect_label=cell.magnitude,
                        # points_binned nunca se persiste, ni siquiera para un
                        # usuario con rol elevado: cierra el bypass de leer
                        # los puntos vía GET /analysis-runs/{id}, que no
                        # aplica ningún control de rol (E-09).
                        result_data=cell.model_dump(mode="json", exclude={"points_binned"}),
                    )
                )
            run.status = "COMPLETED"
            run.completed_at = datetime.now(UTC)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return SpearmanMatrixResponse(
            analysis_run_id=run.id,
            study_id=study_id,
            method="SPEARMAN",
            correction="BENJAMINI_HOCHBERG",
            normality_required=False,
            variables=[item[0] for item in all_series.values()],
            cells=cells,
            excluded=excluded,
        )

    async def compare_construct_groups(
        self, study_id: int, payload: ConstructCompareGroupsRequest
    ) -> ConstructCompareGroupsResponse:
        study = await self._study(study_id)
        scoring_run, series = await self._construct_series(study_id, [payload.construct_id])
        construct, scores = series[payload.construct_id]
        variable = await self.session.get(Variable, payload.group_variable_id)
        if variable is None or variable.project_id != study.project_id:
            raise NotFoundError(f"Variable {payload.group_variable_id} no encontrada")
        if variable.variable_type != "EXOGENOUS" or variable.measurement_level not in (
            "NOMINAL",
            "ORDINAL",
            "BINARY",
        ):
            raise ValidationDomainError(
                "La variable de grupo debe ser exógena y nominal, ordinal o binaria."
            )
        stmt = select(
            Response.response_session_id, Response.raw_code, Response.text_value
        ).where(
            Response.study_id == study_id,
            Response.question_id == variable.question_id,
            Response.is_missing.is_(False),
            Response.response_session_id.in_(valid_session_ids(study_id)),
        )
        group_by_session = {
            session_id: raw_code if raw_code is not None else text_value
            for session_id, raw_code, text_value in (await self.session.execute(stmt)).all()
            if raw_code is not None or text_value is not None
        }
        groups: dict[str, list[float]] = {}
        for session_id, score in scores.items():
            if session_id in group_by_session:
                groups.setdefault(group_by_session[session_id], []).append(score)
        if len(groups) < 2:
            raise InsufficientSampleError("Se requieren al menos dos grupos con puntajes válidos.")

        run = await self._new_run(
            study_id,
            "CONSTRUCT_COMPARE_GROUPS",
            {
                "construct_id": payload.construct_id,
                "group_variable_id": payload.group_variable_id,
                "scoring_run_id": scoring_run.id,
            },
        )
        group_summaries: list[GroupSummaryRead] = []
        suppressed = any(len(values) < study.min_publishable_n for values in groups.values())
        for code, values in sorted(groups.items()):
            cell_suppressed = len(values) < study.min_publishable_n
            group_summaries.append(
                GroupSummaryRead(
                    code=code,
                    n=len(values),
                    suppressed=cell_suppressed,
                    mean=None if cell_suppressed else statistics.fmean(values),
                    median=None if cell_suppressed else statistics.median(values),
                )
            )
        method = None
        computed = None
        warnings: list[str] = []
        if suppressed:
            warnings.append(
                f"Se suprimió la comparación porque al menos un grupo tiene menos de "
                f"{study.min_publishable_n} casos."
            )
        elif any(len(values) < 2 for values in groups.values()):
            warnings.append("Cada grupo necesita al menos dos valores para la prueba.")
        elif len(groups) == 2:
            method = "MANN_WHITNEY"
            computed = compute_mann_whitney(*[groups[key] for key in sorted(groups)])
        else:
            method = "KRUSKAL_WALLIS"
            computed = compute_kruskal_wallis([groups[key] for key in sorted(groups)])

        response = ConstructCompareGroupsResponse(
            analysis_run_id=run.id,
            study_id=study_id,
            construct_id=construct.id,
            group_variable_id=variable.id,
            method=method,
            statistic=computed["statistic"] if computed else None,
            p_value=computed["p_value"] if computed else None,
            effect_size=computed["effect_size"] if computed else None,
            effect_label=computed["effect_label"] if computed else None,
            suppressed=suppressed,
            groups=group_summaries,
            warnings=warnings,
        )
        self.session.add(
            AnalysisResult(
                analysis_run_id=run.id,
                result_code=f"{construct.code}_by_{variable.code}",
                result_type=method or "GROUP_COMPARISON_SUPPRESSED",
                construct_id=construct.id,
                n_valid=sum(len(values) for values in groups.values()),
                statistic_value=response.statistic,
                p_value=response.p_value,
                effect_size=response.effect_size,
                effect_label=response.effect_label,
                result_data=response.model_dump(mode="json"),
            )
        )
        run.status = "COMPLETED"
        run.completed_at = datetime.now(UTC)
        await self.session.commit()
        return response
