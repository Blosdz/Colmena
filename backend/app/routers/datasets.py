from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dataset import (
    AnswerUpdateRead,
    AnswerUpdateRequest,
    CompletenessSummaryRead,
    DataDictionaryRead,
    DatasetExportListResponse,
    DatasetExportRead,
    DatasetExportRequest,
    DatasetRead,
    ResponseStatusRead,
    ResponseStatusUpdateRequest,
)
from app.services.dataset_service import DatasetService

router = APIRouter(tags=["datasets"])


def get_dataset_service(db: Session = Depends(get_db)) -> DatasetService:
    return DatasetService(db)


@router.get("/api/v1/forms/{form_id}/dataset", response_model=DatasetRead)
def get_dataset(
    form_id: str,
    mode: str = Query(default="mixed"),
    include_metadata: bool = Query(default=True),
    include_discarded: bool = Query(default=False),
    expand_multiple_choice: bool = Query(default=False),
    include_scores: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetRead:
    return service.build_form_dataset(
        form_id,
        mode=mode,
        include_metadata=include_metadata,
        include_discarded=include_discarded,
        expand_multiple_choice=expand_multiple_choice,
        include_scores=include_scores,
        limit=limit,
        offset=offset,
    )


@router.get("/api/v1/forms/{form_id}/dataset/preview", response_model=DatasetRead)
def get_dataset_preview(
    form_id: str,
    mode: str = Query(default="mixed"),
    include_metadata: bool = Query(default=True),
    include_discarded: bool = Query(default=False),
    expand_multiple_choice: bool = Query(default=False),
    include_scores: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetRead:
    return service.build_form_dataset(
        form_id,
        mode=mode,
        include_metadata=include_metadata,
        include_discarded=include_discarded,
        expand_multiple_choice=expand_multiple_choice,
        include_scores=include_scores,
        limit=limit,
        offset=offset,
    )


@router.get("/api/v1/forms/{form_id}/data-dictionary", response_model=DataDictionaryRead)
def get_data_dictionary(
    form_id: str,
    service: DatasetService = Depends(get_dataset_service),
) -> DataDictionaryRead:
    return service.build_data_dictionary(form_id)


@router.get("/api/v1/forms/{form_id}/completeness", response_model=CompletenessSummaryRead)
def get_completeness(
    form_id: str,
    service: DatasetService = Depends(get_dataset_service),
) -> CompletenessSummaryRead:
    return service.build_completeness_summary(form_id)


@router.post("/api/v1/forms/{form_id}/exports/excel", response_model=DatasetExportRead, status_code=201)
def export_dataset_excel(
    form_id: str,
    payload: DatasetExportRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetExportRead:
    return service.export_form_dataset_excel(
        form_id,
        mode=payload.mode,
        include_metadata=payload.include_metadata,
        include_discarded=payload.include_discarded,
        expand_multiple_choice=payload.expand_multiple_choice,
        include_scores=payload.include_scores,
    )


@router.post("/api/v1/forms/{form_id}/exports/csv", response_model=DatasetExportRead, status_code=201)
def export_dataset_csv(
    form_id: str,
    payload: DatasetExportRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetExportRead:
    return service.export_form_dataset_csv(
        form_id,
        mode=payload.mode,
        include_metadata=payload.include_metadata,
        include_discarded=payload.include_discarded,
        expand_multiple_choice=payload.expand_multiple_choice,
        include_scores=payload.include_scores,
    )


@router.get("/api/v1/forms/{form_id}/exports", response_model=DatasetExportListResponse)
def list_form_exports(
    form_id: str,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetExportListResponse:
    items, total = service.list_form_exports(form_id)
    return DatasetExportListResponse(items=items, total=total)


@router.patch("/api/v1/form-answers/{answer_id}", response_model=AnswerUpdateRead)
def update_form_answer(
    answer_id: str,
    payload: AnswerUpdateRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> AnswerUpdateRead:
    return service.update_answer_value(answer_id, payload)


@router.patch("/api/v1/form-responses/{response_id}/status", response_model=ResponseStatusRead)
def update_form_response_status(
    response_id: str,
    payload: ResponseStatusUpdateRequest,
    service: DatasetService = Depends(get_dataset_service),
) -> ResponseStatusRead:
    return service.update_response_status(response_id, payload.status)


@router.post("/api/v1/form-responses/{response_id}/restore", response_model=ResponseStatusRead)
def restore_form_response(
    response_id: str,
    service: DatasetService = Depends(get_dataset_service),
) -> ResponseStatusRead:
    return service.restore_response(response_id)
