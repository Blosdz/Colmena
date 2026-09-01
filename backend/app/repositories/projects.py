from __future__ import annotations

from sqlalchemy import Select, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user import OrganizationMembership


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, project_id: int) -> Project | None:
        return await self.session.get(Project, project_id)

    def list_stmt(self, owner_user_id: int) -> Select:
        organization_access = exists(
            select(OrganizationMembership.organization_id).where(
                OrganizationMembership.organization_id == Project.organization_id,
                OrganizationMembership.user_id == owner_user_id,
            )
        )
        return (
            select(Project)
            .where(
                or_(
                    Project.owner_user_id == owner_user_id,
                    (Project.project_type == "CENSO") & organization_access,
                )
            )
            .order_by(Project.created_at.desc())
        )

    async def create(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
