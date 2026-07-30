from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.realtime import broker
from app.routers.analysis_orchestrator import router as analysis_orchestrator_router
from app.routers.catalogs import router as catalogs_router
from app.routers.chart_editor_states import router as chart_editor_states_router
from app.routers.apa_tables import router as apa_tables_router
from app.routers.auth import router as auth_router
from app.routers.categorical_associations import router as categorical_associations_router
from app.routers.charts import router as charts_router
from app.routers.chart_exports import router as chart_exports_router
from app.routers.chart_images import router as chart_images_router
from app.routers.correlations import router as correlations_router
from app.routers.descriptives import router as descriptives_router
from app.routers.datasets import router as datasets_router
from app.routers.forms import router as forms_router
from app.routers.group_comparisons import router as group_comparisons_router
from app.routers.health import router as health_router
from app.routers.instrument_sheet import router as instrument_sheet_router
from app.routers.normality import router as normality_router
from app.routers.projects import router as projects_router
from app.routers.project_variables import router as project_variables_router
from app.routers.public_forms import router as public_forms_router
from app.routers.regression import router as regression_router
from app.routers.reliability import router as reliability_router
from app.routers.responses import router as responses_router
from app.routers.scales import router as scales_router
from app.routers.scoring import router as scoring_router
from app.routers.statistical_decisions import router as statistical_decisions_router
from app.routers.stewart import router as stewart_router
from app.routers.telemetry_ws import router as telemetry_ws_router
from app.routers.word_reports import router as word_reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.startup(get_settings().redis_url)
    yield
    await broker.shutdown()


app = FastAPI(
    title="Colmena API",
    version="0.1.0",
    description="API base para la plataforma academica Colmena.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        *get_settings().cors_extra_origins_list,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(auth_router)
app.include_router(catalogs_router)
app.include_router(projects_router)
app.include_router(project_variables_router)
app.include_router(forms_router)
app.include_router(datasets_router)
app.include_router(descriptives_router)
app.include_router(categorical_associations_router)
app.include_router(analysis_orchestrator_router)
app.include_router(apa_tables_router)
app.include_router(charts_router)
app.include_router(chart_images_router)
app.include_router(chart_exports_router)
app.include_router(correlations_router)
app.include_router(regression_router)
app.include_router(group_comparisons_router)
app.include_router(normality_router)
app.include_router(reliability_router)
app.include_router(instrument_sheet_router)
app.include_router(stewart_router)
app.include_router(responses_router)
app.include_router(scales_router)
app.include_router(public_forms_router)
app.include_router(statistical_decisions_router)
app.include_router(scoring_router)
app.include_router(word_reports_router)
app.include_router(chart_editor_states_router)
app.include_router(telemetry_ws_router)


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {
        "message": "Colmena API is running.",
        "service": "colmena-api",
        "version": "0.1.0",
    }
