"""Control de rol elevado sobre un proyecto (E-09).

Primer consumidor real de `ProjectMember` (existe en el modelo desde antes,
pero ningún servicio lo consultaba). Deliberadamente acotado: no se
retrofit­ea autenticación a ningún otro endpoint del backend en esta
corrección — sólo protege `include_points` en spearman-matrix.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMember
from app.models.user import User

ELEVATED_ROLE_CODES = {"OWNER", "ADMIN", "ANALYST"}


async def user_has_elevated_role(session: AsyncSession, project_id: int, user: User) -> bool:
    project = await session.get(Project, project_id)
    if project is not None and project.owner_user_id == user.id:
        return True
    stmt = select(ProjectMember.role_code).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user.id
    )
    role_code = (await session.execute(stmt)).scalar_one_or_none()
    return role_code in ELEVATED_ROLE_CODES
