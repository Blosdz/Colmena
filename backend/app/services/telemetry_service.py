from __future__ import annotations

import statistics
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.construct import Construct, ConstructItem
from app.models.study import Study
from app.models.variable import Variable
from app.repositories.responses import ResponseRepository
from app.repositories.studies import StudyRepository
from app.schemas.telemetry import (
    ProjectTelemetry,
    StudyTelemetry,
    TelemetrySeriesPoint,
    VariableTelemetry,
)
from app.services.invitation_service import InvitationService


class TelemetryService:
    """Participación de encuestas (harness §25 aproximado): agrega
    `response_sessions` ya persistidas — no ejecuta ningún cálculo de
    scoring/estadística, sólo conteos y promedios operativos."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.study_repo = StudyRepository(session)
        self.response_repo = ResponseRepository(session)

    async def _require_study(self, study_id: int) -> Study:
        study = await self.study_repo.get(study_id)
        if study is None:
            raise NotFoundError(f"Estudio {study_id} no encontrado")
        return study

    async def _participation_funnel(
        self, study: Study, started_count: int, valid_count: int
    ) -> tuple[int | None, int | None, float | None, float | None]:
        """Convocados/no-respondió/tasas, sólo si hay una población objetivo
        contable: estudios con `requires_invitation` e invitaciones emitidas.
        En estudios de enlace público InvitationService.summary() da 0 aunque
        haya cientos de respuestas, así que ahí no hay denominador confiable
        y se devuelve None en vez de fabricar una tasa."""
        if not study.requires_invitation:
            return None, None, None, None
        summary = await InvitationService(self.session).summary(study.id)
        invited_count = summary["total"]
        if not invited_count:
            return None, None, None, None
        not_responded_count = max(invited_count - started_count, 0)
        return (
            invited_count,
            not_responded_count,
            started_count / invited_count,
            valid_count / invited_count,
        )

    @staticmethod
    def _question_ids_by_root(
        constructs: list[Construct], links: list[ConstructItem]
    ) -> dict[int, set[int]]:
        """Agrupa preguntas en la variable raíz que contiene su dimensión."""
        constructs_by_id = {construct.id: construct for construct in constructs}
        question_ids_by_root: dict[int, set[int]] = {
            construct.id: set()
            for construct in constructs
            if construct.parent_id is None
        }
        for link in links:
            construct = constructs_by_id[link.construct_id]
            visited: set[int] = set()
            while construct.parent_id in constructs_by_id and construct.id not in visited:
                visited.add(construct.id)
                construct = constructs_by_id[construct.parent_id]
            if construct.id in question_ids_by_root and link.item_role != "EXCLUDED":
                question_ids_by_root[construct.id].add(link.question_id)
        return question_ids_by_root

    @staticmethod
    def _variable_coverage(
        session_ids: list[int],
        answered_by_session: dict[int, set[int]],
        question_ids: set[int],
    ) -> tuple[int, int, float | None, float | None]:
        if not question_ids:
            return 0, 0, None, None
        answered_count = 0
        completed_count = 0
        completion_pcts: list[float] = []
        for session_id in session_ids:
            answered = len(answered_by_session.get(session_id, set()).intersection(question_ids))
            if answered:
                answered_count += 1
            if answered == len(question_ids):
                completed_count += 1
            completion_pcts.append(answered / len(question_ids) * 100)

        started_count = len(session_ids)
        return (
            answered_count,
            completed_count,
            (completed_count / started_count) if started_count else None,
            statistics.fmean(completion_pcts) if completion_pcts else None,
        )

    async def get_study_telemetry(self, study_id: int) -> StudyTelemetry:
        study = await self._require_study(study_id)
        sessions = await self.response_repo.list_sessions_by_study(study_id)
        responses = await self.response_repo.list_by_study(study_id)

        started_count = len(sessions)
        completed = [s for s in sessions if s.status == "COMPLETED"]
        abandoned = [s for s in sessions if s.status == "ABANDONED"]
        valid = [s for s in sessions if s.validation_status == "VALID"]
        review = [s for s in sessions if s.validation_status == "REVIEW"]
        excluded = [s for s in sessions if s.validation_status == "EXCLUDED"]

        completion_pcts = [
            float(s.completion_pct) for s in sessions if s.completion_pct is not None
        ]
        durations = [s.duration_seconds for s in completed if s.duration_seconds is not None]
        invited_count, not_responded_count, response_rate, valid_rate = (
            await self._participation_funnel(study, started_count, len(valid))
        )

        by_day: dict = defaultdict(lambda: {"started": 0, "completed": 0})
        for s in sessions:
            day = s.started_at.date()
            by_day[day]["started"] += 1
            if s.completed_at is not None:
                by_day[s.completed_at.date()]["completed"] += 1

        series = [
            TelemetrySeriesPoint(date=day, started=counts["started"], completed=counts["completed"])
            for day, counts in sorted(by_day.items())
        ]

        variables: list[VariableTelemetry] = []
        if study.instrument_version_id is not None:
            constructs = list(
                (
                    await self.session.execute(
                        select(Construct).where(
                            Construct.instrument_version_id == study.instrument_version_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            constructs_by_id = {construct.id: construct for construct in constructs}
            roots = [construct for construct in constructs if construct.parent_id is None]
            links: list[ConstructItem] = []

            if constructs_by_id:
                links = list(
                    (
                        await self.session.execute(
                            select(ConstructItem).where(
                                ConstructItem.construct_id.in_(constructs_by_id)
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
            question_ids_by_root = self._question_ids_by_root(constructs, links)

            research_variable_by_construct: dict[int, Variable] = {}
            if roots:
                research_variables = list(
                    (
                        await self.session.execute(
                            select(Variable).where(
                                Variable.project_id == study.project_id,
                                Variable.construct_id.in_([root.id for root in roots]),
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                research_variable_by_construct = {
                    variable.construct_id: variable for variable in research_variables
                }

            answered_by_session: dict[int, set[int]] = defaultdict(set)
            for response in responses:
                if not response.is_missing:
                    answered_by_session[response.response_session_id].add(response.question_id)

            for root in roots:
                question_ids = question_ids_by_root[root.id]
                if not question_ids:
                    continue
                answered_count, completed_count, completion_rate, avg_completion_pct = (
                    self._variable_coverage(
                        [response_session.id for response_session in sessions],
                        answered_by_session,
                        question_ids,
                    )
                )

                research_variable = research_variable_by_construct.get(root.id)
                variables.append(
                    VariableTelemetry(
                        construct_id=root.id,
                        variable_code=(research_variable.code if research_variable else root.code),
                        variable_name=(research_variable.name if research_variable else root.name),
                        role=(
                            research_variable.role
                            if research_variable
                            else (root.metadata_ or {}).get("role")
                        ),
                        question_count=len(question_ids),
                        sessions_started=started_count,
                        sessions_answered=answered_count,
                        sessions_completed=completed_count,
                        completion_rate=completion_rate,
                        avg_completion_pct=avg_completion_pct,
                    )
                )

        return StudyTelemetry(
            study_id=study.id,
            study_name=study.name,
            instrument_id=study.instrument_id,
            instrument_name=study.instrument_name,
            instrument_version_id=study.instrument_version_id,
            instrument_version_code=study.instrument_version_code,
            started_count=started_count,
            completed_count=len(completed),
            abandoned_count=len(abandoned),
            valid_count=len(valid),
            review_count=len(review),
            excluded_count=len(excluded),
            completion_rate=(len(completed) / started_count) if started_count else None,
            avg_completion_pct=statistics.fmean(completion_pcts) if completion_pcts else None,
            avg_duration_seconds=statistics.fmean(durations) if durations else None,
            median_duration_seconds=statistics.median(durations) if durations else None,
            invited_count=invited_count,
            not_responded_count=not_responded_count,
            response_rate=response_rate,
            valid_rate=valid_rate,
            series=series,
            variables=variables,
        )

    async def get_project_telemetry(self, project_id: int) -> ProjectTelemetry:
        stmt = select(Study).where(Study.project_id == project_id)
        studies = list((await self.session.execute(stmt)).scalars().all())
        return ProjectTelemetry(
            project_id=project_id,
            studies=[await self.get_study_telemetry(study.id) for study in studies],
        )
