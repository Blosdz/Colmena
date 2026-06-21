from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.chart_editor_state import ChartEditorState
from app.models.form import Form
from app.schemas.chart_editor_state import (
    ChartEditorStateDeleteResponse,
    ChartEditorStateListRead,
    ChartEditorStateRead,
    ChartEditorStateSave,
)
from app.services.dataset_service import DatasetService


class ChartEditorStateService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)

    def _get_form(self, form_id: str) -> Form:
        return self.dataset_service._get_form(form_id)

    def _get_record(self, form_id: str, chart_id: str) -> ChartEditorState | None:
        return self.db.scalar(
            select(ChartEditorState).where(
                ChartEditorState.form_id == form_id,
                ChartEditorState.chart_id == chart_id,
            )
        )

    def _to_read(self, record: ChartEditorState) -> ChartEditorStateRead:
        return ChartEditorStateRead(
            id=record.id,
            storage_key=record.storage_key,
            form_id=record.form_id,
            chart_id=record.chart_id,
            project_id=record.project_id,
            graphs_json=record.graphs_json,
            metadata_json=record.metadata_json,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def upsert(self, form_id: str, chart_id: str, payload: ChartEditorStateSave) -> ChartEditorStateRead:
        form = self._get_form(form_id)
        record = self._get_record(form_id, chart_id)

        if record is None:
            record = ChartEditorState(
                storage_key=payload.storage_key,
                form_id=form_id,
                chart_id=chart_id,
                project_id=form.project_id,
                graphs_json=payload.graphs_json,
                metadata_json=payload.metadata_json,
            )
            self.db.add(record)
        else:
            record.storage_key = payload.storage_key
            record.graphs_json = payload.graphs_json
            record.metadata_json = payload.metadata_json

        self.db.commit()
        self.db.refresh(record)
        return self._to_read(record)

    def get(self, form_id: str, chart_id: str) -> ChartEditorStateRead:
        self._get_form(form_id)
        record = self._get_record(form_id, chart_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart editor state not found")
        return self._to_read(record)

    def list_for_form(self, form_id: str) -> ChartEditorStateListRead:
        self._get_form(form_id)
        records = list(
            self.db.scalars(
                select(ChartEditorState)
                .where(ChartEditorState.form_id == form_id)
                .order_by(ChartEditorState.updated_at.desc())
            ).all()
        )
        items = [self._to_read(r) for r in records]
        return ChartEditorStateListRead(form_id=form_id, total=len(items), items=items)

    def delete(self, form_id: str, chart_id: str) -> ChartEditorStateDeleteResponse:
        self._get_form(form_id)
        record = self._get_record(form_id, chart_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart editor state not found")
        self.db.delete(record)
        self.db.commit()
        return ChartEditorStateDeleteResponse(status="deleted", chart_id=chart_id)
