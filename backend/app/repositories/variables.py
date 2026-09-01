from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.variable import Variable


class VariableRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, variable_id: int) -> Variable | None:
        return await self.session.get(Variable, variable_id)

    def list_by_project_stmt(self, project_id: int) -> Select:
        return (
            select(Variable)
            .where(Variable.project_id == project_id)
            .order_by(Variable.created_at.desc())
        )

    async def get_by_project_and_code(self, project_id: int, code: str) -> Variable | None:
        stmt = select(Variable).where(
            Variable.project_id == project_id, Variable.code == code
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, variable: Variable) -> Variable:
        self.session.add(variable)
        await self.session.flush()
        return variable

    async def delete(self, variable: Variable) -> None:
        await self.session.delete(variable)
