from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.approach import Approach
from app.models.design_type import DesignType
from app.models.project import Project
from app.models.project_demographics import ProjectDemographics
from app.models.type_research import TypeResearch
from app.schemas.project import ProjectCreate, ProjectUpdate

_CATALOG_BY_FIELD = {
    "type_research_id": TypeResearch,
    "design_type_id": DesignType,
    "approach_id": Approach,
}


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_catalog(self, field: str, value: str | None) -> None:
        if value is None:
            return
        model = _CATALOG_BY_FIELD[field]
        exists = self.db.scalar(
            select(model.id).where(model.id == value, model.deleted_at.is_(None))
        )
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} '{value}' no existe en el catalogo.",
            )

    def _load(self, project_id: str) -> Project | None:
        statement = (
            select(Project)
            .where(Project.id == project_id, Project.deleted_at.is_(None))
            .options(
                selectinload(Project.type_research),
                selectinload(Project.design_type),
                selectinload(Project.approach),
                selectinload(Project.demographics),
            )
        )
        return self.db.scalar(statement)

    def create_project(self, payload: ProjectCreate, user_id: str) -> Project:
        data = payload.model_dump()
        demographics = data.pop("demographics", None)

        for field in _CATALOG_BY_FIELD:
            self._validate_catalog(field, data.get(field))

        project = Project(user_id=user_id, **data)
        if demographics is not None:
            project.demographics = ProjectDemographics(
                **{k: v for k, v in demographics.items() if v is not None}
            )
        self.db.add(project)
        self.db.commit()
        return self._load(project.id)

    def get_project(self, project_id: str) -> Project:
        project = self._load(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    def list_projects(self, limit: int, offset: int, q: str | None) -> tuple[list[Project], int]:
        statement = (
            select(Project)
            .where(Project.deleted_at.is_(None))
            .options(
                selectinload(Project.type_research),
                selectinload(Project.design_type),
                selectinload(Project.approach),
                selectinload(Project.demographics),
            )
        )
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
        demographics = update_data.pop("demographics", None)

        for field in _CATALOG_BY_FIELD:
            if field in update_data:
                self._validate_catalog(field, update_data[field])

        for field, value in update_data.items():
            setattr(project, field, value)

        if demographics is not None:
            if project.demographics is None:
                project.demographics = ProjectDemographics(
                    **{k: v for k, v in demographics.items() if v is not None}
                )
            else:
                for field, value in demographics.items():
                    if value is not None:
                        setattr(project.demographics, field, value)

        self.db.commit()
        return self._load(project.id)

    def soft_delete_project(self, project_id: str) -> dict[str, str]:
        project = self.get_project(project_id)
        project.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {
            "status": "deleted",
            "id": project.id,
        }
