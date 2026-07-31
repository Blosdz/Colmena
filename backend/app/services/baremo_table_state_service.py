from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.baremo_table_state import BaremoTableState
from app.models.form import Form
from app.schemas.baremo_table_state import (
    BaremoTableRow,
    BaremoTableStateDeleteResponse,
    BaremoTableStateListRead,
    BaremoTableStateRead,
    BaremoTableStateSave,
)
from app.services.dataset_service import DatasetService


class BaremoTableStateService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)

    def _get_form(self, form_id: str) -> Form:
        return self.dataset_service._get_form(form_id)

    def _get_record(self, form_id: str, table_key: str) -> BaremoTableState | None:
        return self.db.scalar(
            select(BaremoTableState).where(
                BaremoTableState.form_id == form_id,
                BaremoTableState.table_key == table_key,
            )
        )

    def _to_read(self, record: BaremoTableState) -> BaremoTableStateRead:
        rows = [BaremoTableRow(**row) for row in (record.rows_json or [])]
        return BaremoTableStateRead(
            id=record.id,
            form_id=record.form_id,
            project_id=record.project_id,
            user_id=record.user_id,
            table_key=record.table_key,
            group_kind=record.group_kind,
            title=record.title,
            rows=rows,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def upsert(self, form_id: str, table_key: str, payload: BaremoTableStateSave) -> BaremoTableStateRead:
        form = self._get_form(form_id)
        record = self._get_record(form_id, table_key)
        rows_json = [row.model_dump() for row in payload.rows]

        if record is None:
            record = BaremoTableState(
                form_id=form_id,
                project_id=form.project_id,
                user_id=form.project.user_id if form.project else None,
                table_key=table_key,
                group_kind=payload.group_kind,
                title=payload.title,
                rows_json=rows_json,
            )
            self.db.add(record)
        else:
            record.group_kind = payload.group_kind
            record.title = payload.title
            record.rows_json = rows_json

        self.db.commit()
        self.db.refresh(record)
        return self._to_read(record)

    def list_for_form(self, form_id: str) -> BaremoTableStateListRead:
        self._get_form(form_id)
        records = list(
            self.db.scalars(
                select(BaremoTableState)
                .where(BaremoTableState.form_id == form_id)
                .order_by(BaremoTableState.created_at.asc())
            ).all()
        )
        items = [self._to_read(r) for r in records]
        return BaremoTableStateListRead(form_id=form_id, total=len(items), items=items)

    def delete(self, form_id: str, table_key: str) -> BaremoTableStateDeleteResponse:
        self._get_form(form_id)
        record = self._get_record(form_id, table_key)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baremo table state not found")
        self.db.delete(record)
        self.db.commit()
        return BaremoTableStateDeleteResponse(status="deleted", table_key=table_key)
