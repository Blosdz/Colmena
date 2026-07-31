from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.baremo_table_state import (
    BaremoTableStateDeleteResponse,
    BaremoTableStateListRead,
    BaremoTableStateRead,
    BaremoTableStateSave,
)
from app.services.baremo_table_state_service import BaremoTableStateService


router = APIRouter(tags=["baremo-tables"])


def get_service(db: Session = Depends(get_db)) -> BaremoTableStateService:
    return BaremoTableStateService(db)


@router.get(
    "/api/v1/forms/{form_id}/baremo-tables",
    response_model=BaremoTableStateListRead,
)
def list_baremo_tables(
    form_id: str,
    service: BaremoTableStateService = Depends(get_service),
) -> BaremoTableStateListRead:
    return service.list_for_form(form_id)


@router.put(
    "/api/v1/forms/{form_id}/baremo-tables/{table_key}",
    response_model=BaremoTableStateRead,
    status_code=200,
)
def upsert_baremo_table(
    form_id: str,
    table_key: str,
    payload: BaremoTableStateSave,
    service: BaremoTableStateService = Depends(get_service),
) -> BaremoTableStateRead:
    return service.upsert(form_id, table_key, payload)


@router.delete(
    "/api/v1/forms/{form_id}/baremo-tables/{table_key}",
    response_model=BaremoTableStateDeleteResponse,
)
def delete_baremo_table(
    form_id: str,
    table_key: str,
    service: BaremoTableStateService = Depends(get_service),
) -> BaremoTableStateDeleteResponse:
    return service.delete(form_id, table_key)
