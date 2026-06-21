from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.project_variable import ProjectVariable
from app.models.score_band import ScoreBand
from app.models.scoring_config import ScoringConfig
from app.schemas.scoring import (
    ScoreBandCreate,
    ScoreBandUpdate,
    ScoringConfigCreate,
    ScoringConfigUpdate,
)
from app.scoring.band_engine import validate_bands_no_overlap
from app.services.dataset_service import DatasetService


class ScoringConfigService:
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)

    def _get_form(self, form_id: str):
        return self.dataset_service._get_form(form_id)

    def _get_scoring_config(self, config_id: str) -> ScoringConfig:
        config = self.db.scalar(
            select(ScoringConfig)
            .options(selectinload(ScoringConfig.score_bands))
            .where(ScoringConfig.id == config_id, ScoringConfig.deleted_at.is_(None))
        )
        if config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ScoringConfig not found")
        return config

    def _get_band(self, band_id: str) -> ScoreBand:
        band = self.db.scalar(select(ScoreBand).where(ScoreBand.id == band_id, ScoreBand.deleted_at.is_(None)))
        if band is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ScoreBand not found")
        return band

    def _validate_scope(self, form_id: str, payload: ScoringConfigCreate | ScoringConfigUpdate) -> None:
        form = self._get_form(form_id)
        data = payload.model_dump(exclude_unset=True)
        scoring_level = data.get("scoring_level")
        instrument_id = data.get("instrument_id")
        dimension_id = data.get("dimension_id")
        project_variable_id = data.get("project_variable_id")

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
        if dimension_id is not None:
            dimension = self.db.scalar(
                select(FormDimension)
                .join(FormInstrument, FormInstrument.id == FormDimension.instrument_id)
                .where(
                    FormDimension.id == dimension_id,
                    FormInstrument.form_id == form.id,
                    FormDimension.deleted_at.is_(None),
                    FormInstrument.deleted_at.is_(None),
                )
            )
            if dimension is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dimension not found for form")
        if project_variable_id is not None:
            variable = self.db.scalar(
                select(ProjectVariable).where(
                    ProjectVariable.id == project_variable_id,
                    ProjectVariable.project_id == form.project_id,
                    ProjectVariable.deleted_at.is_(None),
                )
            )
            if variable is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project variable not found for form")

        if scoring_level == "instrument" and not instrument_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="instrument_id is required for instrument scoring")
        if scoring_level == "dimension" and not dimension_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="dimension_id is required for dimension scoring")
        if scoring_level == "project_variable" and not project_variable_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="project_variable_id is required for project_variable scoring")

    def validate_scoring_config(self, config: ScoringConfig) -> list[str]:
        warnings: list[str] = []
        if config.score_bands:
            warnings.extend(validate_bands_no_overlap(config.score_bands))
        return list(dict.fromkeys(warnings))

    def create_scoring_config(self, form_id: str, payload: ScoringConfigCreate) -> ScoringConfig:
        form = self._get_form(form_id)
        self._validate_scope(form_id, payload)
        data = payload.model_dump(exclude={"bands"})
        config = ScoringConfig(project_id=form.project_id, form_id=form.id, **data)
        self.db.add(config)
        self.db.flush()
        for band_payload in payload.bands:
            self.db.add(ScoreBand(scoring_config_id=config.id, **band_payload.model_dump()))
        self.db.commit()
        return self._get_scoring_config(config.id)

    def list_scoring_configs(self, form_id: str) -> tuple[list[ScoringConfig], int]:
        self._get_form(form_id)
        filters = [ScoringConfig.form_id == form_id, ScoringConfig.deleted_at.is_(None)]
        items = list(
            self.db.scalars(
                select(ScoringConfig)
                .options(selectinload(ScoringConfig.score_bands))
                .where(*filters)
                .order_by(ScoringConfig.created_at.asc())
            ).all()
        )
        total = int(self.db.scalar(select(func.count()).select_from(ScoringConfig).where(*filters)) or 0)
        return items, total

    def get_scoring_config(self, config_id: str) -> ScoringConfig:
        return self._get_scoring_config(config_id)

    def update_scoring_config(self, config_id: str, payload: ScoringConfigUpdate) -> ScoringConfig:
        config = self._get_scoring_config(config_id)
        self._validate_scope(config.form_id, payload)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(config, field, value)
        self.db.commit()
        return self._get_scoring_config(config.id)

    def delete_scoring_config(self, config_id: str) -> dict[str, str]:
        config = self._get_scoring_config(config_id)
        config.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": config.id}

    def add_score_band(self, config_id: str, payload: ScoreBandCreate) -> ScoreBand:
        config = self._get_scoring_config(config_id)
        band = ScoreBand(scoring_config_id=config.id, **payload.model_dump())
        self.db.add(band)
        self.db.commit()
        self.db.refresh(band)
        return band

    def list_score_bands(self, config_id: str) -> list[ScoreBand]:
        config = self._get_scoring_config(config_id)
        return [band for band in config.score_bands if band.deleted_at is None]

    def update_score_band(self, band_id: str, payload: ScoreBandUpdate) -> ScoreBand:
        band = self._get_band(band_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(band, field, value)
        if band.max_value < band.min_value:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="max_value must be greater than or equal to min_value")
        self.db.commit()
        self.db.refresh(band)
        return band

    def delete_score_band(self, band_id: str) -> dict[str, str]:
        band = self._get_band(band_id)
        band.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"status": "deleted", "id": band.id}
