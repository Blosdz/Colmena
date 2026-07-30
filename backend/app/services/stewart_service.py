from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.form import Form
from app.models.form_instrument import FormInstrument
from app.schemas.stewart import StewartMatrixRead, StewartPointRead
from app.services.descriptive_service import DescriptiveService


class StewartService:
    def __init__(self, db: Session):
        self.db = db
        self.descriptive_service = DescriptiveService(db)

    def _get_form(self, form_id: str) -> Form:
        form = self.db.get(Form, form_id)
        if form is None or form.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
        return form

    def _active_instruments(self, form: Form) -> list[FormInstrument]:
        return sorted(
            (instrument for instrument in form.instruments if instrument.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )

    def _resolve_instrument(self, form: Form, instrument_id: str | None) -> FormInstrument:
        instruments = self._active_instruments(form)
        if not instruments:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form has no instruments")
        if instrument_id is None:
            return instruments[0]
        instrument = next((item for item in instruments if item.id == instrument_id), None)
        if instrument is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found for form")
        return instrument

    def get_stewart_matrix(
        self,
        form_id: str,
        *,
        instrument_id: str | None = None,
        include_discarded: bool = False,
        decimals: int = 3,
        score_aggregation: str = "sum",
    ) -> StewartMatrixRead:
        form = self._get_form(form_id)
        instrument = self._resolve_instrument(form, instrument_id)

        dimension_items = self.descriptive_service.build_dimension_scores(
            form_id,
            include_discarded=include_discarded,
            decimals=decimals,
            score_aggregation=score_aggregation,
        )

        warnings: list[str] = []
        points: list[StewartPointRead] = []
        for item in dimension_items:
            if item.instrument_id != instrument.id:
                continue
            if item.numeric is None or item.importance is None or item.numeric.mean is None or item.importance.mean is None:
                warnings.append(f"dimension_missing_importance_items:{item.dimension_id}")
                continue
            points.append(
                StewartPointRead(
                    dimension_id=item.dimension_id,
                    dimension_name=item.name,
                    performance_mean=item.numeric.mean,
                    importance_mean=item.importance.mean,
                    performance_n=item.numeric.valid_n,
                    importance_n=item.importance.valid_n,
                )
            )

        performance_axis_mean = (
            round(sum(point.performance_mean for point in points) / len(points), decimals) if points else None
        )
        importance_axis_mean = (
            round(sum(point.importance_mean for point in points) / len(points), decimals) if points else None
        )
        if not points:
            warnings.append("no_dimensions_with_importance_items")

        return StewartMatrixRead(
            form_id=form.id,
            instrument_id=instrument.id,
            instrument_name=instrument.name,
            points=points,
            performance_axis_mean=performance_axis_mean,
            importance_axis_mean=importance_axis_mean,
            warnings=list(dict.fromkeys(warnings)),
        )
