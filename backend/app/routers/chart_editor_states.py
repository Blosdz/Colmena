from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chart_editor_state import (
    ChartEditorStateDeleteResponse,
    ChartEditorStateListRead,
    ChartEditorStateRead,
    ChartEditorStateSave,
)
from app.services.chart_editor_state_service import ChartEditorStateService


router = APIRouter(tags=["chart-editor-states"])


def get_service(db: Session = Depends(get_db)) -> ChartEditorStateService:
    return ChartEditorStateService(db)


@router.put(
    "/api/v1/forms/{form_id}/chart-editor-states/{chart_id}",
    response_model=ChartEditorStateRead,
    status_code=200,
)
def upsert_chart_editor_state(
    form_id: str,
    chart_id: str,
    payload: ChartEditorStateSave,
    service: ChartEditorStateService = Depends(get_service),
) -> ChartEditorStateRead:
    return service.upsert(form_id, chart_id, payload)


@router.get(
    "/api/v1/forms/{form_id}/chart-editor-states",
    response_model=ChartEditorStateListRead,
)
def list_chart_editor_states(
    form_id: str,
    service: ChartEditorStateService = Depends(get_service),
) -> ChartEditorStateListRead:
    return service.list_for_form(form_id)


@router.get(
    "/api/v1/forms/{form_id}/chart-editor-states/{chart_id}",
    response_model=ChartEditorStateRead,
)
def get_chart_editor_state(
    form_id: str,
    chart_id: str,
    service: ChartEditorStateService = Depends(get_service),
) -> ChartEditorStateRead:
    return service.get(form_id, chart_id)


@router.delete(
    "/api/v1/forms/{form_id}/chart-editor-states/{chart_id}",
    response_model=ChartEditorStateDeleteResponse,
)
def delete_chart_editor_state(
    form_id: str,
    chart_id: str,
    service: ChartEditorStateService = Depends(get_service),
) -> ChartEditorStateDeleteResponse:
    return service.delete(form_id, chart_id)
