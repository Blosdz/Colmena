from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "colmena-api",
        "version": "0.1.0",
    }
