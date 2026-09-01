from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.compat_appthesis import router as compat_appthesis_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging

settings = get_settings()

configure_logging()

app = FastAPI(
    title="Colmena Backend",
    description=(
        "Backend unificado de Colmena (proyectos académicos, CENSOPAS-COPSOQ, "
        "surveys, motor estadístico, autenticación). Fases 1-9 implementadas."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_origin_regex=settings.cors_allow_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.api_v1_prefix)
# Shim del monorepo `fullProyect` — rutas absolutas, no bajo api_v1_prefix.
app.include_router(compat_appthesis_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
