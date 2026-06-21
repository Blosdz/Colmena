from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.scoring import (
    ControlScaleCreate,
    ControlScaleItemCreate,
    ControlScaleItemRead,
    ControlScaleRead,
    ControlScaleUpdate,
    ResponseScoreRead,
    ScoreBandCreate,
    ScoreBandRead,
    ScoreBandUpdate,
    ScoredDatasetRead,
    ScoringConfigCreate,
    ScoringConfigListRead,
    ScoringConfigRead,
    ScoringConfigUpdate,
    ScoringOptionsRead,
    ScoringPreviewRead,
    ScoringResultsRead,
    ScoringRunRead,
    ScoringRunRequest,
)
from app.services.advanced_scoring_service import AdvancedScoringService
from app.services.control_scale_service import ControlScaleService
from app.services.scoring_config_service import ScoringConfigService

router = APIRouter(tags=["scoring"])


def get_scoring_config_service(db: Session = Depends(get_db)) -> ScoringConfigService:
    return ScoringConfigService(db)


def get_control_scale_service(db: Session = Depends(get_db)) -> ControlScaleService:
    return ControlScaleService(db)


def get_advanced_scoring_service(db: Session = Depends(get_db)) -> AdvancedScoringService:
    return AdvancedScoringService(db)


@router.get("/api/v1/forms/{form_id}/scoring/configs", response_model=ScoringConfigListRead)
def list_scoring_configs(form_id: str, service: ScoringConfigService = Depends(get_scoring_config_service)) -> ScoringConfigListRead:
    items, total = service.list_scoring_configs(form_id)
    warnings = []
    for item in items:
        warnings.extend(service.validate_scoring_config(item))
    return ScoringConfigListRead(form_id=form_id, total=total, items=[ScoringConfigRead.model_validate(item) for item in items], warnings=list(dict.fromkeys(warnings)))


@router.post("/api/v1/forms/{form_id}/scoring/configs", response_model=ScoringConfigRead, status_code=201)
def create_scoring_config(form_id: str, payload: ScoringConfigCreate, service: ScoringConfigService = Depends(get_scoring_config_service)) -> ScoringConfigRead:
    return ScoringConfigRead.model_validate(service.create_scoring_config(form_id, payload))


@router.get("/api/v1/scoring/configs/{config_id}", response_model=ScoringConfigRead)
def get_scoring_config(config_id: str, service: ScoringConfigService = Depends(get_scoring_config_service)) -> ScoringConfigRead:
    return ScoringConfigRead.model_validate(service.get_scoring_config(config_id))


@router.patch("/api/v1/scoring/configs/{config_id}", response_model=ScoringConfigRead)
def update_scoring_config(config_id: str, payload: ScoringConfigUpdate, service: ScoringConfigService = Depends(get_scoring_config_service)) -> ScoringConfigRead:
    return ScoringConfigRead.model_validate(service.update_scoring_config(config_id, payload))


@router.delete("/api/v1/scoring/configs/{config_id}")
def delete_scoring_config(config_id: str, service: ScoringConfigService = Depends(get_scoring_config_service)) -> dict[str, str]:
    return service.delete_scoring_config(config_id)


@router.post("/api/v1/scoring/configs/{config_id}/bands", response_model=ScoreBandRead, status_code=201)
def create_score_band(config_id: str, payload: ScoreBandCreate, service: ScoringConfigService = Depends(get_scoring_config_service)) -> ScoreBandRead:
    return ScoreBandRead.model_validate(service.add_score_band(config_id, payload))


@router.get("/api/v1/scoring/configs/{config_id}/bands", response_model=list[ScoreBandRead])
def list_score_bands(config_id: str, service: ScoringConfigService = Depends(get_scoring_config_service)) -> list[ScoreBandRead]:
    return [ScoreBandRead.model_validate(item) for item in service.list_score_bands(config_id)]


@router.patch("/api/v1/scoring/bands/{band_id}", response_model=ScoreBandRead)
def update_score_band(band_id: str, payload: ScoreBandUpdate, service: ScoringConfigService = Depends(get_scoring_config_service)) -> ScoreBandRead:
    return ScoreBandRead.model_validate(service.update_score_band(band_id, payload))


@router.delete("/api/v1/scoring/bands/{band_id}")
def delete_score_band(band_id: str, service: ScoringConfigService = Depends(get_scoring_config_service)) -> dict[str, str]:
    return service.delete_score_band(band_id)


@router.get("/api/v1/forms/{form_id}/control-scales", response_model=list[ControlScaleRead])
def list_control_scales(form_id: str, service: ControlScaleService = Depends(get_control_scale_service)) -> list[ControlScaleRead]:
    items, _ = service.list_control_scales(form_id)
    return [ControlScaleRead.model_validate(item) for item in items]


@router.post("/api/v1/forms/{form_id}/control-scales", response_model=ControlScaleRead, status_code=201)
def create_control_scale(form_id: str, payload: ControlScaleCreate, service: ControlScaleService = Depends(get_control_scale_service)) -> ControlScaleRead:
    return ControlScaleRead.model_validate(service.create_control_scale(form_id, payload))


@router.get("/api/v1/control-scales/{control_scale_id}", response_model=ControlScaleRead)
def get_control_scale(control_scale_id: str, service: ControlScaleService = Depends(get_control_scale_service)) -> ControlScaleRead:
    return ControlScaleRead.model_validate(service.get_control_scale(control_scale_id))


@router.patch("/api/v1/control-scales/{control_scale_id}", response_model=ControlScaleRead)
def update_control_scale(control_scale_id: str, payload: ControlScaleUpdate, service: ControlScaleService = Depends(get_control_scale_service)) -> ControlScaleRead:
    return ControlScaleRead.model_validate(service.update_control_scale(control_scale_id, payload))


@router.delete("/api/v1/control-scales/{control_scale_id}")
def delete_control_scale(control_scale_id: str, service: ControlScaleService = Depends(get_control_scale_service)) -> dict[str, str]:
    return service.delete_control_scale(control_scale_id)


@router.post("/api/v1/control-scales/{control_scale_id}/items", response_model=ControlScaleItemRead, status_code=201)
def create_control_scale_item(control_scale_id: str, payload: ControlScaleItemCreate, service: ControlScaleService = Depends(get_control_scale_service)) -> ControlScaleItemRead:
    return ControlScaleItemRead.model_validate(service.add_control_scale_item(control_scale_id, payload))


@router.get("/api/v1/control-scales/{control_scale_id}/items", response_model=list[ControlScaleItemRead])
def list_control_scale_items(control_scale_id: str, service: ControlScaleService = Depends(get_control_scale_service)) -> list[ControlScaleItemRead]:
    return [ControlScaleItemRead.model_validate(item) for item in service.list_control_scale_items(control_scale_id)]


@router.delete("/api/v1/control-scale-items/{item_id}")
def delete_control_scale_item(item_id: str, service: ControlScaleService = Depends(get_control_scale_service)) -> dict[str, str]:
    return service.remove_control_scale_item(item_id)


@router.post("/api/v1/forms/{form_id}/scoring/preview", response_model=ScoringPreviewRead)
def preview_scoring(form_id: str, service: AdvancedScoringService = Depends(get_advanced_scoring_service)) -> ScoringPreviewRead:
    return service.preview_scoring(form_id)


@router.post("/api/v1/forms/{form_id}/scoring/run", response_model=ScoringRunRead)
def run_scoring(form_id: str, payload: ScoringRunRequest, service: AdvancedScoringService = Depends(get_advanced_scoring_service)) -> ScoringRunRead:
    return service.run_scoring_for_form(form_id, payload)


@router.get("/api/v1/form-responses/{response_id}/scores", response_model=list[ResponseScoreRead])
def get_response_scores(response_id: str, service: AdvancedScoringService = Depends(get_advanced_scoring_service)) -> list[ResponseScoreRead]:
    return service.get_response_scores(response_id)


@router.get("/api/v1/forms/{form_id}/scoring/results", response_model=ScoringResultsRead)
def get_scoring_results(form_id: str, service: AdvancedScoringService = Depends(get_advanced_scoring_service)) -> ScoringResultsRead:
    return service.get_form_score_results(form_id)


@router.get("/api/v1/forms/{form_id}/scoring/dataset", response_model=ScoredDatasetRead)
def get_scoring_dataset(form_id: str, service: AdvancedScoringService = Depends(get_advanced_scoring_service)) -> ScoredDatasetRead:
    return service.get_scored_dataset(form_id)


@router.get("/api/v1/forms/{form_id}/scoring/options", response_model=ScoringOptionsRead)
def get_scoring_options(form_id: str, service: AdvancedScoringService = Depends(get_advanced_scoring_service)) -> ScoringOptionsRead:
    return service.get_scoring_options(form_id)
