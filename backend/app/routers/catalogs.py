from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.catalog import CatalogListResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/v1/catalogs", tags=["catalogs"])


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


@router.get("/research-types", response_model=CatalogListResponse)
def list_research_types(
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogListResponse:
    items = service.list_research_types()
    return CatalogListResponse(items=items, total=len(items))


@router.get("/design-types", response_model=CatalogListResponse)
def list_design_types(
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogListResponse:
    items = service.list_design_types()
    return CatalogListResponse(items=items, total=len(items))


@router.get("/approaches", response_model=CatalogListResponse)
def list_approaches(
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogListResponse:
    items = service.list_approaches()
    return CatalogListResponse(items=items, total=len(items))
