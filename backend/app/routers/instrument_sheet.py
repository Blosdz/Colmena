from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dataset import DatasetExportRead
from app.schemas.instrument_sheet import InstrumentSheetRead
from app.services.instrument_sheet_service import InstrumentSheetService

router = APIRouter(tags=["instrument-sheet"])


def get_instrument_sheet_service(db: Session = Depends(get_db)) -> InstrumentSheetService:
    return InstrumentSheetService(db)


@router.get("/api/v1/forms/{form_id}/instrument-sheet", response_model=InstrumentSheetRead)
def get_instrument_sheet(
    form_id: str,
    instrument_id: str | None = Query(default=None),
    decimals: int = Query(default=3, ge=0, le=6),
    include_discarded: bool = Query(default=False),
    service: InstrumentSheetService = Depends(get_instrument_sheet_service),
) -> InstrumentSheetRead:
    return service.get_instrument_sheet(
        form_id,
        instrument_id=instrument_id,
        decimals=decimals,
        include_discarded=include_discarded,
    )


@router.post(
    "/api/v1/forms/{form_id}/instrument-sheet/exports/excel",
    response_model=DatasetExportRead,
    status_code=201,
)
def export_instrument_sheet_excel(
    form_id: str,
    instrument_id: str | None = Query(default=None),
    service: InstrumentSheetService = Depends(get_instrument_sheet_service),
) -> DatasetExportRead:
    return service.export_instrument_sheet_excel(form_id, instrument_id=instrument_id)
