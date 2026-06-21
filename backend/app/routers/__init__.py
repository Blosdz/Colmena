from app.routers.analysis_orchestrator import router as analysis_orchestrator_router
from app.routers.chart_editor_states import router as chart_editor_states_router
from app.routers.apa_tables import router as apa_tables_router
from app.routers.categorical_associations import router as categorical_associations_router
from app.routers.charts import router as charts_router
from app.routers.chart_images import router as chart_images_router
from app.routers.correlations import router as correlations_router
from app.routers.descriptives import router as descriptives_router
from app.routers.datasets import router as datasets_router
from app.routers.forms import router as forms_router
from app.routers.group_comparisons import router as group_comparisons_router
from app.routers.health import router as health_router
from app.routers.normality import router as normality_router
from app.routers.projects import router as projects_router
from app.routers.project_variables import router as project_variables_router
from app.routers.public_forms import router as public_forms_router
from app.routers.responses import router as responses_router
from app.routers.scoring import router as scoring_router
from app.routers.statistical_decisions import router as statistical_decisions_router
from app.routers.word_reports import router as word_reports_router

__all__ = [
    "analysis_orchestrator_router",
    "chart_editor_states_router",
    "apa_tables_router",
    "categorical_associations_router",
    "charts_router",
    "chart_images_router",
    "correlations_router",
    "forms_router",
    "descriptives_router",
    "datasets_router",
    "group_comparisons_router",
    "health_router",
    "normality_router",
    "projects_router",
    "project_variables_router",
    "public_forms_router",
    "responses_router",
    "scoring_router",
    "statistical_decisions_router",
    "word_reports_router",
]
