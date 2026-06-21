from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.form import FormCreate, FormListResponse, FormRead, FormUpdate
from app.schemas.form_dimension import (
    FormDimensionCreate,
    FormDimensionListResponse,
    FormDimensionRead,
    FormDimensionUpdate,
)
from app.schemas.form_instrument import (
    FormInstrumentCreate,
    FormInstrumentListResponse,
    FormInstrumentRead,
    FormInstrumentUpdate,
)
from app.schemas.form_question import (
    FormQuestionCreate,
    FormQuestionListResponse,
    FormQuestionRead,
    FormQuestionUpdate,
)
from app.schemas.form_question_option import (
    FormQuestionOptionCreate,
    FormQuestionOptionListResponse,
    FormQuestionOptionRead,
    FormQuestionOptionUpdate,
)
from app.schemas.form_section import (
    FormSectionCreate,
    FormSectionListResponse,
    FormSectionRead,
    FormSectionUpdate,
)
from app.services.form_service import FormService
from app.schemas.public_form import PublicFormLinkRead
from app.services.public_form_service import PublicFormService

router = APIRouter(tags=["forms"])


def get_form_service(db: Session = Depends(get_db)) -> FormService:
    return FormService(db)


def get_public_form_service(db: Session = Depends(get_db)) -> PublicFormService:
    return PublicFormService(db)


@router.post("/api/v1/projects/{project_id}/forms", response_model=FormRead, status_code=201)
def create_form(
    project_id: str,
    payload: FormCreate,
    service: FormService = Depends(get_form_service),
) -> FormRead:
    return service.create_form(project_id, payload)


@router.get("/api/v1/projects/{project_id}/forms", response_model=FormListResponse)
def list_forms(
    project_id: str,
    service: FormService = Depends(get_form_service),
) -> FormListResponse:
    items, total = service.list_forms(project_id)
    return FormListResponse(items=items, total=total)


@router.get("/api/v1/forms/{form_id}", response_model=FormRead)
def get_form(
    form_id: str,
    service: FormService = Depends(get_form_service),
) -> FormRead:
    return service.get_form(form_id)


@router.patch("/api/v1/forms/{form_id}", response_model=FormRead)
def update_form(
    form_id: str,
    payload: FormUpdate,
    service: FormService = Depends(get_form_service),
) -> FormRead:
    return service.update_form(form_id, payload)


@router.delete("/api/v1/forms/{form_id}")
def delete_form(
    form_id: str,
    service: FormService = Depends(get_form_service),
) -> dict[str, str]:
    return service.soft_delete_form(form_id)


@router.post("/api/v1/forms/{form_id}/publish", response_model=PublicFormLinkRead)
def publish_form(
    form_id: str,
    service: PublicFormService = Depends(get_public_form_service),
) -> PublicFormLinkRead:
    _, link = service.publish_form(form_id)
    return link


@router.post("/api/v1/forms/{form_id}/close", response_model=FormRead)
def close_form(
    form_id: str,
    service: PublicFormService = Depends(get_public_form_service),
) -> FormRead:
    return service.close_form(form_id)


@router.post("/api/v1/forms/{form_id}/reopen", response_model=FormRead)
def reopen_form(
    form_id: str,
    service: PublicFormService = Depends(get_public_form_service),
) -> FormRead:
    return service.reopen_form(form_id)


@router.get("/api/v1/forms/{form_id}/public-link", response_model=PublicFormLinkRead)
def get_public_link(
    form_id: str,
    service: PublicFormService = Depends(get_public_form_service),
) -> PublicFormLinkRead:
    return service.get_public_link(form_id)


@router.post("/api/v1/forms/{form_id}/sections", response_model=FormSectionRead, status_code=201)
def create_section(
    form_id: str,
    payload: FormSectionCreate,
    service: FormService = Depends(get_form_service),
) -> FormSectionRead:
    return service.create_section(form_id, payload)


@router.get("/api/v1/forms/{form_id}/sections", response_model=FormSectionListResponse)
def list_sections(
    form_id: str,
    service: FormService = Depends(get_form_service),
) -> FormSectionListResponse:
    items, total = service.list_sections(form_id)
    return FormSectionListResponse(items=items, total=total)


@router.patch("/api/v1/form-sections/{section_id}", response_model=FormSectionRead)
def update_section(
    section_id: str,
    payload: FormSectionUpdate,
    service: FormService = Depends(get_form_service),
) -> FormSectionRead:
    return service.update_section(section_id, payload)


@router.delete("/api/v1/form-sections/{section_id}")
def delete_section(
    section_id: str,
    service: FormService = Depends(get_form_service),
) -> dict[str, str]:
    return service.soft_delete_section(section_id)


@router.post("/api/v1/forms/{form_id}/instruments", response_model=FormInstrumentRead, status_code=201)
def create_instrument(
    form_id: str,
    payload: FormInstrumentCreate,
    service: FormService = Depends(get_form_service),
) -> FormInstrumentRead:
    return service.create_instrument(form_id, payload)


@router.get("/api/v1/forms/{form_id}/instruments", response_model=FormInstrumentListResponse)
def list_instruments(
    form_id: str,
    service: FormService = Depends(get_form_service),
) -> FormInstrumentListResponse:
    items, total = service.list_instruments(form_id)
    return FormInstrumentListResponse(items=items, total=total)


@router.patch("/api/v1/form-instruments/{instrument_id}", response_model=FormInstrumentRead)
def update_instrument(
    instrument_id: str,
    payload: FormInstrumentUpdate,
    service: FormService = Depends(get_form_service),
) -> FormInstrumentRead:
    return service.update_instrument(instrument_id, payload)


@router.delete("/api/v1/form-instruments/{instrument_id}")
def delete_instrument(
    instrument_id: str,
    service: FormService = Depends(get_form_service),
) -> dict[str, str]:
    return service.soft_delete_instrument(instrument_id)


@router.post("/api/v1/form-instruments/{instrument_id}/dimensions", response_model=FormDimensionRead, status_code=201)
def create_dimension(
    instrument_id: str,
    payload: FormDimensionCreate,
    service: FormService = Depends(get_form_service),
) -> FormDimensionRead:
    return service.create_dimension(instrument_id, payload)


@router.get("/api/v1/form-instruments/{instrument_id}/dimensions", response_model=FormDimensionListResponse)
def list_dimensions(
    instrument_id: str,
    service: FormService = Depends(get_form_service),
) -> FormDimensionListResponse:
    items, total = service.list_dimensions(instrument_id)
    return FormDimensionListResponse(items=items, total=total)


@router.patch("/api/v1/form-dimensions/{dimension_id}", response_model=FormDimensionRead)
def update_dimension(
    dimension_id: str,
    payload: FormDimensionUpdate,
    service: FormService = Depends(get_form_service),
) -> FormDimensionRead:
    return service.update_dimension(dimension_id, payload)


@router.delete("/api/v1/form-dimensions/{dimension_id}")
def delete_dimension(
    dimension_id: str,
    service: FormService = Depends(get_form_service),
) -> dict[str, str]:
    return service.soft_delete_dimension(dimension_id)


@router.post("/api/v1/forms/{form_id}/questions", response_model=FormQuestionRead, status_code=201)
def create_question(
    form_id: str,
    payload: FormQuestionCreate,
    service: FormService = Depends(get_form_service),
) -> FormQuestionRead:
    return service.create_question(form_id, payload)


@router.get("/api/v1/forms/{form_id}/questions", response_model=FormQuestionListResponse)
def list_questions(
    form_id: str,
    service: FormService = Depends(get_form_service),
) -> FormQuestionListResponse:
    items, total = service.list_questions(form_id)
    return FormQuestionListResponse(items=items, total=total)


@router.get("/api/v1/form-questions/{question_id}", response_model=FormQuestionRead)
def get_question(
    question_id: str,
    service: FormService = Depends(get_form_service),
) -> FormQuestionRead:
    return service.get_question(question_id)


@router.patch("/api/v1/form-questions/{question_id}", response_model=FormQuestionRead)
def update_question(
    question_id: str,
    payload: FormQuestionUpdate,
    service: FormService = Depends(get_form_service),
) -> FormQuestionRead:
    return service.update_question(question_id, payload)


@router.delete("/api/v1/form-questions/{question_id}")
def delete_question(
    question_id: str,
    service: FormService = Depends(get_form_service),
) -> dict[str, str]:
    return service.soft_delete_question(question_id)


@router.post("/api/v1/form-questions/{question_id}/options", response_model=FormQuestionOptionRead, status_code=201)
def create_option(
    question_id: str,
    payload: FormQuestionOptionCreate,
    service: FormService = Depends(get_form_service),
) -> FormQuestionOptionRead:
    return service.create_option(question_id, payload)


@router.get("/api/v1/form-questions/{question_id}/options", response_model=FormQuestionOptionListResponse)
def list_options(
    question_id: str,
    service: FormService = Depends(get_form_service),
) -> FormQuestionOptionListResponse:
    items, total = service.list_options(question_id)
    return FormQuestionOptionListResponse(items=items, total=total)


@router.patch("/api/v1/form-question-options/{option_id}", response_model=FormQuestionOptionRead)
def update_option(
    option_id: str,
    payload: FormQuestionOptionUpdate,
    service: FormService = Depends(get_form_service),
) -> FormQuestionOptionRead:
    return service.update_option(option_id, payload)


@router.delete("/api/v1/form-question-options/{option_id}")
def delete_option(
    option_id: str,
    service: FormService = Depends(get_form_service),
) -> dict[str, str]:
    return service.soft_delete_option(option_id)
