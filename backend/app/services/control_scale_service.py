from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.control_scale import ControlScale
from app.models.control_scale_item import ControlScaleItem
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.schemas.scoring import ControlScaleCreate, ControlScaleItemCreate, ControlScaleUpdate
from app.services.dataset_service import DatasetService


class ControlScaleService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)

    def _get_form(self, form_id: str):
        return self.dataset_service._get_form(form_id)

    def _get_control_scale(self, control_scale_id: str) -> ControlScale:
        control_scale = self.db.scalar(
            select(ControlScale)
            .options(selectinload(ControlScale.items))
            .where(ControlScale.id == control_scale_id, ControlScale.deleted_at.is_(None))
        )
        if control_scale is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ControlScale not found")
        return control_scale

    def _get_item(self, item_id: str) -> ControlScaleItem:
        item = self.db.scalar(select(ControlScaleItem).where(ControlScaleItem.id == item_id, ControlScaleItem.deleted_at.is_(None)))
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ControlScaleItem not found")
        return item

    def _validate_control_scale(self, form_id: str, payload: ControlScaleCreate | ControlScaleUpdate) -> None:
        form = self._get_form(form_id)
        data = payload.model_dump(exclude_unset=True)
        instrument_id = data.get("instrument_id")
        if instrument_id is not None:
            instrument = self.db.scalar(
                select(FormInstrument).where(
                    FormInstrument.id == instrument_id,
                    FormInstrument.form_id == form.id,
                    FormInstrument.deleted_at.is_(None),
                )
            )
            if instrument is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found for form")

    def validate_control_scale(self, control_scale: ControlScale) -> list[str]:
        warnings: list[str] = []
        if not any(item.deleted_at is None for item in control_scale.items):
            warnings.append("control_scale_without_items")
        return warnings

    def create_control_scale(self, form_id: str, payload: ControlScaleCreate) -> ControlScale:
        form = self._get_form(form_id)
        self._validate_control_scale(form_id, payload)
        control_scale = ControlScale(project_id=form.project_id, form_id=form.id, **payload.model_dump(exclude={"items"}))
        self.db.add(control_scale)
        self.db.flush()
        for item_payload in payload.items:
            self._create_item(control_scale, item_payload)
        self.db.commit()
        return self._get_control_scale(control_scale.id)

    def _create_item(self, control_scale: ControlScale, payload: ControlScaleItemCreate) -> ControlScaleItem:
        question = self.db.scalar(
            select(FormQuestion).where(
                FormQuestion.id == payload.question_id,
                FormQuestion.form_id == control_scale.form_id,
                FormQuestion.deleted_at.is_(None),
            )
        )
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found for form")
        if payload.expected_option_id is not None:
            option = self.db.scalar(
                select(FormQuestionOption).where(
                    FormQuestionOption.id == payload.expected_option_id,
                    FormQuestionOption.question_id == question.id,
                    FormQuestionOption.deleted_at.is_(None),
                )
            )
            if option is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expected option not found for question")
        item = ControlScaleItem(control_scale_id=control_scale.id, **payload.model_dump())
        self.db.add(item)
        return item

    def list_control_scales(self, form_id: str) -> tuple[list[ControlScale], int]:
        self._get_form(form_id)
        filters = [ControlScale.form_id == form_id, ControlScale.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(ControlScale)
                .options(selectinload(ControlScale.items))
                .where(*filters)
                .order_by(ControlScale.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(ControlScale).where(*filters)) or 0)
        return items, total

    def get_control_scale(self, control_scale_id: str) -> ControlScale:
        return self._get_control_scale(control_scale_id)

    def update_control_scale(self, control_scale_id: str, payload: ControlScaleUpdate) -> ControlScale:
        control_scale = self._get_control_scale(control_scale_id)
        self._validate_control_scale(control_scale.form_id, payload)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(control_scale, field, value)
        self.db.commit()
        return self._get_control_scale(control_scale.id)

    def delete_control_scale(self, control_scale_id: str) -> dict[str, str]:
        control_scale = self._get_control_scale(control_scale_id)
        control_scale.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": control_scale.id}

    def add_control_scale_item(self, control_scale_id: str, payload: ControlScaleItemCreate) -> ControlScaleItem:
        control_scale = self._get_control_scale(control_scale_id)
        item = self._create_item(control_scale, payload)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_control_scale_items(self, control_scale_id: str) -> list[ControlScaleItem]:
        control_scale = self._get_control_scale(control_scale_id)
        return [item for item in control_scale.items if item.deleted_at is None]

    def remove_control_scale_item(self, item_id: str) -> dict[str, str]:
        item = self._get_item(item_id)
        item.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": item.id}
