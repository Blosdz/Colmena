from __future__ import annotations

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.response import Response, ResponseSelectedOption, ResponseSession


def valid_session_ids(study_id: int) -> Select:
    """Sesiones que cuentan como dato publicable/analizable: completadas por
    el respondiente y validadas como VALID (ver ResponseService.complete_session).
    Único punto de verdad para "n" entre scoring, telemetría y exports."""
    return select(ResponseSession.id).where(
        ResponseSession.study_id == study_id,
        ResponseSession.status == "COMPLETED",
        ResponseSession.validation_status == "VALID",
    )


class ResponseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_session(self, session_id: int) -> ResponseSession | None:
        return await self.session.get(ResponseSession, session_id)

    async def create_session(self, response_session: ResponseSession) -> ResponseSession:
        self.session.add(response_session)
        await self.session.flush()
        return response_session

    async def get_response(self, response_session_id: int, question_id: int) -> Response | None:
        stmt = select(Response).where(
            Response.response_session_id == response_session_id,
            Response.question_id == question_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def add_response(self, response: Response) -> Response:
        self.session.add(response)
        await self.session.flush()
        return response

    async def replace_selected_options(self, response_id: int, option_ids: list[int]) -> None:
        await self.session.execute(
            delete(ResponseSelectedOption).where(
                ResponseSelectedOption.response_id == response_id
            )
        )
        self.session.add_all([
            ResponseSelectedOption(response_id=response_id, option_id=option_id)
            for option_id in option_ids
        ])

    async def list_by_session(self, response_session_id: int) -> list[Response]:
        stmt = select(Response).where(Response.response_session_id == response_session_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_by_study(self, study_id: int) -> list[Response]:
        stmt = select(Response).where(Response.study_id == study_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_sessions_by_study(self, study_id: int) -> list[ResponseSession]:
        stmt = select(ResponseSession).where(ResponseSession.study_id == study_id)
        return list((await self.session.execute(stmt)).scalars().all())
