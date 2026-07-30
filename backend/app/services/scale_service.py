from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.project import Project
from app.models.scale import Scale, ScaleOption
from app.schemas.scale import ScaleCreate


class ScaleService:
    def __init__(self, db: Session):
        self.db = db

    def _get_scale(self, scale_id: str) -> Scale:
        scale = self.db.scalar(
            select(Scale)
            .options(selectinload(Scale.options))
            .where(Scale.id == scale_id, Scale.deleted_at.is_(None))
        )
        if scale is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scale not found")
        return scale

    def list_scales(self, project_id: str | None) -> tuple[list[Scale], int]:
        """Presets del sistema (project_id NULL) + escalas del proyecto indicado."""
        ownership = Scale.project_id.is_(None)
        if project_id:
            # Validar que el proyecto exista para no devolver silenciosamente solo presets.
            project = self.db.scalar(
                select(Project).where(Project.id == project_id, Project.deleted_at.is_(None))
            )
            if project is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
            ownership = or_(Scale.project_id.is_(None), Scale.project_id == project_id)

        filters = [ownership, Scale.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(Scale)
                .options(selectinload(Scale.options))
                .where(*filters)
                # Presets del sistema primero, luego por nombre.
                .order_by(Scale.project_id.is_(None).desc(), Scale.name.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(Scale).where(*filters)) or 0)
        return items, total

    def get_scale(self, scale_id: str) -> Scale:
        return self._get_scale(scale_id)

    def create_scale(self, project_id: str, payload: ScaleCreate) -> Scale:
        project = self.db.scalar(
            select(Project).where(Project.id == project_id, Project.deleted_at.is_(None))
        )
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        scale = Scale(
            project_id=project_id,
            name=payload.name,
            scale_kind=payload.scale_kind,
            render_style=payload.render_style,
            points=payload.points,
            options=[
                ScaleOption(value=opt.value, label=opt.label, sort_order=opt.sort_order or index)
                for index, opt in enumerate(payload.options)
            ],
        )
        self.db.add(scale)
        self.db.commit()
        self.db.refresh(scale)
        return scale

    def soft_delete_scale(self, scale_id: str) -> dict[str, str]:
        scale = self._get_scale(scale_id)
        if scale.project_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System preset scales cannot be deleted",
            )
        scale.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": scale.id}
