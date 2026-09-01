"""Shim de compatibilidad con el monorepo `fullProyect` (AppThesis).

`thesis-assistantV2` (`src/api/colmenaCharts.js`, `colmenaBaremos.js`) y
`thesis-backend` (`src/colmena/colmena.service.ts`) hablan con la API del COLMENA
anterior. COL2 reorganizó el dominio (`forms`→`studies`, `scoring_configs`→
`barems`+`constructs`, sin almacén de `chart-images`). Este router traduce esos
pocos endpoints sin reimplementar lógica: se apoya en `ScoringService`,
`PublicSurveyService` y `ResponseService`.

Se monta con rutas absolutas directamente en `app` (no bajo el prefijo
`/api/v1` del `api_router`) para no colisionar con las rutas reales de COL2.
"""

from __future__ import annotations

import statistics
import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_optional_current_user
from app.models.censopas import ConstructScore
from app.models.study import Study
from app.models.user import User
from app.repositories.censopas import CensopasRepository
from app.repositories.studies import StudyRepository
from app.schemas.public import PublicSurveyBundle
from app.schemas.responses import ResponseSessionCompleteRequest, ResponseUpsert
from app.services import compat_charts
from app.services.public_survey_service import PublicSurveyService
from app.services.response_service import ResponseService
from app.services.scoring_service import ScoringService

router = APIRouter(tags=["compat-appthesis"])


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #
async def _resolve_study_by_slug(session: AsyncSession, slug: str) -> Study:
    """Un `form` de AppThesis es un `Study` de COL2. El `slug` es el
    `public_id` (UUID) del estudio, o el `legacy_public_slug` que la migración
    guardó en `study.settings` para los formularios importados del COLMENA
    anterior."""
    try:
        public_id = uuid.UUID(str(slug))
    except (ValueError, TypeError):
        public_id = None

    stmt = select(Study)
    if public_id is not None:
        stmt = stmt.where(Study.public_id == public_id)
    else:
        # `settings` es JSON genérico (JSONB en PG): `.as_string()` castea de forma
        # portable — `.astext` sólo existe en el tipo JSONB nativo.
        stmt = stmt.where(Study.settings["legacy_public_slug"].as_string() == str(slug))
    study = (await session.execute(stmt)).scalar_one_or_none()
    if study is None:
        raise NotFoundError(f"No existe un formulario público con slug '{slug}'.")
    return study


async def _resolve_form_study_id(session: AsyncSession, form_id: str) -> int:
    """`form_id` en la API vieja: acepta el id entero del estudio o su slug."""
    try:
        return int(form_id)
    except (ValueError, TypeError):
        study = await _resolve_study_by_slug(session, form_id)
        return study.id


# --------------------------------------------------------------------------- #
#  Proyectos / formularios (chart & baremo pickers del editor de tesis)        #
# --------------------------------------------------------------------------- #
@router.get("/api/v1/projects/{project_id}/forms")
async def list_project_forms(
    project_id: int,
    session: AsyncSession = Depends(get_db),
    _user: User | None = Depends(get_optional_current_user),
):
    """Estudios de un proyecto, expuestos como "formularios" (id = study.id)."""
    stmt = (
        select(Study)
        .where(Study.project_id == project_id)
        .options(selectinload(Study.instrument_version))
        .order_by(Study.created_at.desc())
    )
    studies = (await session.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "id": study.id,
                "title": study.name,
                "name": study.name,
                "project_id": study.project_id,
                "status": study.status,
                "public_slug": (study.settings or {}).get("legacy_public_slug")
                or str(study.public_id),
            }
            for study in studies
        ]
    }


# --------------------------------------------------------------------------- #
#  chart-images (generadas al vuelo desde los resultados de baremación)        #
# --------------------------------------------------------------------------- #
@router.get("/api/v1/forms/{form_id}/chart-images/word-ready")
async def chart_images_word_ready(
    form_id: str,
    session: AsyncSession = Depends(get_db),
    _user: User | None = Depends(get_optional_current_user),
):
    study_id = await _resolve_form_study_id(session, form_id)
    return {"items": await compat_charts.list_available_charts(session, study_id)}


@router.get("/api/v1/forms/{form_id}/chart-images/{artifact_id}/base64")
async def chart_image_base64(
    form_id: str,
    artifact_id: str,
    session: AsyncSession = Depends(get_db),
    _user: User | None = Depends(get_optional_current_user),
):
    study_id = await _resolve_form_study_id(session, form_id)
    png = await compat_charts.render_chart_png(session, study_id, artifact_id)
    return compat_charts.png_to_payload(study_id, artifact_id, png)


@router.get("/api/v1/forms/{form_id}/chart-images/{artifact_id}.png")
async def chart_image_png(
    form_id: str,
    artifact_id: str,
    session: AsyncSession = Depends(get_db),
    _user: User | None = Depends(get_optional_current_user),
):
    study_id = await _resolve_form_study_id(session, form_id)
    png = await compat_charts.render_chart_png(session, study_id, artifact_id)
    return Response(content=png, media_type="image/png")


# --------------------------------------------------------------------------- #
#  Baremos: resolución por formulario (colmenaBaremos.js / colmena.service.ts) #
# --------------------------------------------------------------------------- #
@router.get("/api/v1/forms/{form_id}/scoring/baremos/resolution")
async def baremos_resolution(
    form_id: str,
    levels_count: int = Query(default=3, ge=2, le=10),
    session: AsyncSession = Depends(get_db),
    _user: User | None = Depends(get_optional_current_user),
):
    del levels_count  # COL2 modela N bandas; el parámetro se conserva por compat
    study_id = await _resolve_form_study_id(session, form_id)
    study = await StudyRepository(session).get(study_id)
    if study is None:
        raise NotFoundError(f"Estudio {study_id} no encontrado")

    overview = await ScoringService(session).get_overview(study_id)
    barem = (
        await CensopasRepository(session).get_barem(study.barem_id)
        if study.barem_id
        else None
    )
    bands_by_construct: dict[int, list] = {}
    if barem:
        for band in barem.bands:
            bands_by_construct.setdefault(band.construct_id, []).append(band)

    # Puntajes crudos por constructo (de la última corrida) para SD y para
    # clasificar la media contra las bandas.
    raw_by_construct: dict[int, list[float]] = {}
    if overview.analysis_run_id is not None:
        scores = (
            await session.execute(
                select(ConstructScore).where(
                    ConstructScore.analysis_run_id == overview.analysis_run_id
                )
            )
        ).scalars().all()
        for score in scores:
            if score.score_0_100 is not None:
                raw_by_construct.setdefault(score.construct_id, []).append(
                    float(score.score_0_100)
                )

    baremo_source = None
    if barem:
        baremo_source = barem.source_reference or barem.population_label or barem.name

    # El "scoring_config" del COLMENA viejo era una variable/dimensión puntuada
    # con su baremo. COL2 modela las bandas por constructo (normalmente las
    # dimensiones). Se expone una entrada por constructo con bandas; si ninguno
    # las tiene, se cae a las variables raíz para no dejar el picker vacío.
    scored = [r for r in overview.results if bands_by_construct.get(r.construct_id)]
    if not scored:
        scored = [r for r in overview.results if r.parent_id is None]

    items = []
    for result in scored:
        model_bands = sorted(
            bands_by_construct.get(result.construct_id, []),
            key=lambda b: b.severity_order,
        )
        by_band_id = {b.id: b for b in model_bands}

        raw = raw_by_construct.get(result.construct_id, [])
        sd_score = round(statistics.stdev(raw), 4) if len(raw) > 1 else None

        mean_band = None
        if result.mean_score is not None and model_bands:
            mean_band = ScoringService._find_band(float(result.mean_score), model_bands)

        levels = []
        for rb in result.bands:
            mb = by_band_id.get(rb.band_id)
            levels.append(
                {
                    "label": rb.label,
                    "code": rb.code,
                    "min_value": float(mb.min_value) if mb else None,
                    "max_value": float(mb.max_value) if mb else None,
                    "severity_order": mb.severity_order if mb else None,
                    "interpretation": (mb.interpretation if mb else None),
                    "classification_code": rb.classification_code,
                    "color_hint": rb.color_hint,
                    "source": baremo_source or "estudio",
                    "n": rb.n,
                    "percent": rb.pct,
                }
            )

        items.append(
            {
                "scoring_config_id": str(result.construct_id),
                "scoring_config_name": (
                    f"{result.construct_name} · {barem.name}" if barem else result.construct_name
                ),
                "variable_label": result.construct_name,
                "scoring_level": result.construct_type,
                "score_min": 0.0,
                "score_max": 100.0,
                "baremo_source": baremo_source or ("estudio" if barem else "sin_baremo"),
                "valid_n": result.n_valid,
                "mean_score": (float(result.mean_score) if result.mean_score is not None else None),
                "sd_score": sd_score,
                "mean_level": (mean_band.label if mean_band else None),
                "mean_interpretation": (mean_band.interpretation if mean_band else None),
                "levels": levels,
                "warnings": [] if not result.suppressed else ["Resultado suprimido por privacidad."],
            }
        )

    return {
        "form_id": str(study_id),
        "project_id": str(study.project_id),
        "resolved_variables": len(items),
        "items": items,
        "warnings": ([] if overview.analysis_run_id else ["El estudio todavía no tiene resultados calculados."]),
    }


# --------------------------------------------------------------------------- #
#  Formulario público por slug (iframe embebido en AppThesis)                  #
# --------------------------------------------------------------------------- #
@router.get("/api/public/forms/{slug}", response_model=PublicSurveyBundle)
async def public_form_bundle(slug: str, session: AsyncSession = Depends(get_db)):
    study = await _resolve_study_by_slug(session, slug)
    return await PublicSurveyService(session).get_open_study_bundle(study.public_id)


@router.post("/api/public/forms/{slug}/responses", status_code=201)
async def public_form_submit(
    slug: str,
    payload: dict,
    session: AsyncSession = Depends(get_db),
):
    """Envío en un solo POST (API vieja). `payload.answers` es
    `{question_id: value}` o una lista `[{question_id, ...ResponseUpsert}]`."""
    study = await _resolve_study_by_slug(session, slug)
    public = PublicSurveyService(session)
    response_session = await public.create_session_for_public_study(
        study.public_id,
        (payload or {}).get("invitation_token"),
    )

    responses = ResponseService(session)
    answers = (payload or {}).get("answers") or {}
    if isinstance(answers, dict):
        answers = [{"question_id": int(qid), **_coerce_answer(value)} for qid, value in answers.items()]
    for entry in answers:
        qid = int(entry.pop("question_id"))
        await responses.upsert_response(response_session.id, qid, ResponseUpsert(**entry))

    await responses.complete_session(
        response_session.id, ResponseSessionCompleteRequest()
    )
    return {"ok": True, "response_session_id": response_session.id}


def _coerce_answer(value) -> dict:
    if value is None or value == "":
        return {"is_missing": True}
    if isinstance(value, bool):
        return {"boolean_value": value}
    if isinstance(value, (int, float)):
        return {"numeric_value": float(value)}
    if isinstance(value, list):
        return {"selected_option_ids": [int(v) for v in value]}
    if isinstance(value, str) and value.isdigit():
        return {"option_id": int(value)}
    return {"text_value": str(value)}
