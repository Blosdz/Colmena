from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approach import Approach
from app.models.design_type import DesignType
from app.models.type_research import TypeResearch


class CatalogService:
    def __init__(self, db: Session):
        self.db = db

    def _list(self, model) -> list:
        statement = (
            select(model)
            .where(model.deleted_at.is_(None), model.is_active.is_(True))
            .order_by(model.name.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_research_types(self) -> list[TypeResearch]:
        return self._list(TypeResearch)

    def list_design_types(self) -> list[DesignType]:
        return self._list(DesignType)

    def list_approaches(self) -> list[Approach]:
        return self._list(Approach)
