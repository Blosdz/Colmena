from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, payload: ProjectCreate) -> Project:
        project = Project(**payload.model_dump())
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: str) -> Project:
        statement = select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
        project = self.db.scalar(statement)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    def list_projects(self, limit: int, offset: int, q: str | None) -> tuple[list[Project], int]:
        statement = select(Project).where(Project.deleted_at.is_(None))
        count_statement = select(func.count()).select_from(Project).where(Project.deleted_at.is_(None))

        if q:
            query = f"%{q.strip()}%"
            statement = statement.where(Project.title.ilike(query))
            count_statement = count_statement.where(Project.title.ilike(query))

        statement = statement.order_by(Project.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.scalars(statement).all())
        total = int(self.db.scalar(count_statement) or 0)
        return items, total

    def update_project(self, project_id: str, payload: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(project, field, value)

        self.db.commit()
        self.db.refresh(project)
        return project

    def soft_delete_project(self, project_id: str) -> dict[str, str]:
        project = self.get_project(project_id)
        project.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {
            "status": "deleted",
            "id": project.id,
        }
