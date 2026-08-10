from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.chart_palette import ChartPalette
from app.models.form import Form
from app.schemas.chart_palette import (
    ChartPaletteDeleteResponse,
    ChartPaletteRead,
    ChartPaletteSave,
)
from app.services.dataset_service import DatasetService


class ChartPaletteService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)

    def _get_form(self, form_id: str) -> Form:
        return self.dataset_service._get_form(form_id)

    def _get_record(self, form_id: str, chart_key: str) -> ChartPalette | None:
        return self.db.scalar(
            select(ChartPalette).where(
                ChartPalette.form_id == form_id,
                ChartPalette.chart_key == chart_key,
            )
        )

    def _to_read(self, record: ChartPalette) -> ChartPaletteRead:
        return ChartPaletteRead(
            id=record.id,
            form_id=record.form_id,
            chart_key=record.chart_key,
            project_id=record.project_id,
            colors=record.colors,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def upsert(self, form_id: str, chart_key: str, payload: ChartPaletteSave) -> ChartPaletteRead:
        form = self._get_form(form_id)
        record = self._get_record(form_id, chart_key)

        if record is None:
            record = ChartPalette(
                form_id=form_id,
                chart_key=chart_key,
                project_id=form.project_id,
                colors=payload.colors,
            )
            self.db.add(record)
        else:
            record.colors = payload.colors

        self.db.commit()
        self.db.refresh(record)
        return self._to_read(record)

    def get(self, form_id: str, chart_key: str) -> ChartPaletteRead:
        self._get_form(form_id)
        record = self._get_record(form_id, chart_key)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart palette not found")
        return self._to_read(record)

    def delete(self, form_id: str, chart_key: str) -> ChartPaletteDeleteResponse:
        self._get_form(form_id)
        record = self._get_record(form_id, chart_key)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart palette not found")
        self.db.delete(record)
        self.db.commit()
        return ChartPaletteDeleteResponse(status="deleted", chart_key=chart_key)
