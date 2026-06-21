from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_variable import ProjectVariable
from app.schemas.project_variable import ProjectVariableCreate, ProjectVariableUpdate


class ProjectVariableService:
    def __init__(self, db: Session):
        self.db = db

    def _get_project(self, project_id: str) -> Project:
        project = self.db.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.deleted_at.is_(None),
            )
        )
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def _get_variable(self, variable_id: str) -> ProjectVariable:
        variable = self.db.scalar(
            select(ProjectVariable).where(
                ProjectVariable.id == variable_id,
                ProjectVariable.deleted_at.is_(None),
            )
        )
        if variable is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project variable not found")
        return variable

    def create_variable(self, project_id: str, payload: ProjectVariableCreate) -> ProjectVariable:
        self._get_project(project_id)
        variable = ProjectVariable(project_id=project_id, **payload.model_dump())
        self.db.add(variable)
        self.db.commit()
        self.db.refresh(variable)
        return variable

    def list_variables(self, project_id: str) -> tuple[list[ProjectVariable], int]:
        self._get_project(project_id)
        filters = [
            ProjectVariable.project_id == project_id,
            ProjectVariable.deleted_at.is_(None),
        ]
        items = list(
            self.db.scalars(
                select(ProjectVariable)
                .where(*filters)
                .order_by(ProjectVariable.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(ProjectVariable).where(*filters)) or 0)
        return items, total

    def get_variable(self, variable_id: str) -> ProjectVariable:
        return self._get_variable(variable_id)

    def update_variable(self, variable_id: str, payload: ProjectVariableUpdate) -> ProjectVariable:
        variable = self._get_variable(variable_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(variable, field, value)
        self.db.commit()
        self.db.refresh(variable)
        return variable

    def soft_delete_variable(self, variable_id: str) -> dict[str, str]:
        variable = self._get_variable(variable_id)
        variable.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": variable.id}
