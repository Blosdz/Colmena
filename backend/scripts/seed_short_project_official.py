"""Seed de UN proyecto corto CENSOPAS-COPSOQ (versión SHORT) para
`ammyt11@gmail.com`, usando el banco de ítems OFICIAL real de
`censopas_seed_complete.json` (raíz del repo) en vez de contenido sintético.

Reutiliza infraestructura ya probada, no la reescribe:
  - `build_manifest()` de `seed_censopas_official.py` (importa el manifiesto
    real: dimensiones, ítems, catálogos de respuesta, dirección de scoring).
  - Los helpers genéricos de `seed_demo_current.py` (`raw_code_for_target`,
    `pick_tier_list`, `load_question_options`, `import_reference_barem`,
    `setup_area_units`, `seed_plan_and_bsc_short`,
    `seed_analytics_exports_reports`) — ninguno de ellos depende de que el
    contenido sea sintético, sólo del `instrument_version_id`.

Lo único propio de este script es la generación de personas/respuestas
apuntando a los 42 códigos de pregunta reales (`C-001`..`C-042`) y el alta
del proyecto/estudio con metadata que refleja contenido oficial.

Uso (desde backend/, con el venv activo):
    python scripts/seed_short_project_official.py
"""

from __future__ import annotations

import asyncio
import json
import random
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models.audit import AuditLog
from app.models.instrument import Instrument
from app.models.project import Project
from app.models.question import Question
from app.models.response import Response, ResponseSession, ResponseSessionUnit
from app.models.study import Study
from app.models.user import User
from app.models.variable import Variable
from app.schemas.instruments import InstrumentVersionUpdate
from app.schemas.projects import ProjectCreate
from app.schemas.studies import StudyCreate, StudyUpdate
from app.schemas.surveys import SurveyFromInstrumentCreate
from app.services.censopas_service import CensopasScoringService
from app.services.instrument_service import InstrumentService
from app.services.project_service import ProjectService
from app.services.scoring_orchestrator import run_canonical_scoring
from app.services.study_service import StudyService
from app.services.survey_service import SurveyService

from scripts.seed_censopas_official import _load_seed_data, build_manifest
from scripts.seed_demo_current import (
    DIMENSIONS,
    SHORT_VERSION_ID,
    TIER_BASE,
    import_reference_barem,
    load_question_options,
    pick_tier_list,
    random_datetime,
    raw_code_for_target,
    reset_instrument_version_content,
    seed_analytics_exports_reports,
    seed_plan_and_bsc_short,
)

OWNER_EMAIL = "ammyt11@gmail.com"
DEMO_CODE = "SYN-C20-2026-OFICIAL"
SEED_VERSION = "CENSOPAS_SHORT_OFICIAL_V1"
MANIFEST_VERSION = "CENSOPAS-CORTA-2025-V1"

DISCLAIMER = (
    "RESPUESTAS SINTÉTICAS — el banco de ítems (dimensiones, preguntas, catálogos de "
    "respuesta y dirección de scoring) es el contenido OFICIAL del Manual técnico "
    "CENSOPAS-COPSOQ; los 20 encuestados y sus respuestas son datos sintéticos de demo, "
    "no una aplicación real."
)

RNG = random.Random(20260819)

# (field_code, question_code, measurement_level, free_text)
PROFILE_FIELDS: list[tuple[str, str, str, bool]] = [
    ("SEXO", "C-001", "BINARY", False),
    ("EDAD", "C-002", "ORDINAL", False),
    ("NIVEL_INSTRUCCION", "C-003", "ORDINAL", False),
    ("PUESTO", "C-004", "NOMINAL", True),
    ("AREA", "C-005", "NOMINAL", True),
    ("CONTRATO", "C-006", "NOMINAL", False),
    ("TIEMPO_PUESTO", "C-007", "ORDINAL", False),
    ("TURNO", "C-008", "NOMINAL", False),
    ("HORAS_SEMANA", "C-009", "ORDINAL", False),
    ("TIPO_SUELDO", "C-010", "NOMINAL", False),
    ("RANGO_REMUNERATIVO", "C-011", "ORDINAL", False),
]

AREAS = ["Administración", "Operaciones", "Comercial"]
AREA_SIZES = {"Administración": 8, "Operaciones": 7, "Comercial": 5}
JOB_TITLES_BY_AREA = {
    "Administración": ["Analista administrativo", "Asistente de RR. HH.", "Contador"],
    "Operaciones": ["Operario de planta", "Técnico de mantenimiento", "Supervisor de turno"],
    "Comercial": ["Ejecutivo comercial", "Asesor de ventas", "Coordinador comercial"],
}

# Meta objetivo por dimensión para 20 personas (mismo perfil de riesgo usado
# en el seed sintético previo, ahora aplicado a los ítems oficiales reales).
DIM_TARGETS: dict[str, dict[str, int]] = {
    "D1": {"FAV": 3, "INT": 5, "DESF": 12},
    "D2": {"FAV": 4, "INT": 9, "DESF": 7},
    "D3": {"FAV": 10, "INT": 6, "DESF": 4},
    "D4": {"FAV": 5, "INT": 10, "DESF": 5},
    "D5": {"FAV": 3, "INT": 6, "DESF": 11},
    "D6": {"FAV": 11, "INT": 6, "DESF": 3},
}


async def reset_owner_projects(session: AsyncSession, owner: User) -> None:
    projects = (
        (await session.execute(select(Project).where(Project.owner_user_id == owner.id)))
        .scalars()
        .all()
    )
    for project in projects:
        print(f"[reset] borrando proyecto previo id={project.id} ({project.name})")
        await session.execute(delete(AuditLog).where(AuditLog.project_id == project.id))
        await session.execute(delete(Project).where(Project.id == project.id))
    await session.commit()
    await reset_instrument_version_content(session, SHORT_VERSION_ID)


async def import_official_short(session: AsyncSession) -> dict:
    data = _load_seed_data()
    manifest = build_manifest(data, "SHORT", MANIFEST_VERSION)
    service = CensopasScoringService(session)
    validation = service.validate_manifest_payload(manifest)
    if not validation.valid:
        raise RuntimeError(f"Manifiesto oficial SHORT inválido: {validation.errors}")
    result = await service.import_manifest(SHORT_VERSION_ID, manifest)
    print(
        f"[instrumento oficial v{SHORT_VERSION_ID}] importado: {result.imported} — "
        f"ready_for_scoring={result.readiness.ready_for_scoring} errors={result.readiness.errors}"
    )

    # Publicar la versión (status=ACTIVE) — sin esto "Instrumentos" en el
    # frontend muestra "no hay planes oficiales publicados" aunque el
    # contenido ya esté importado (el catálogo sólo lista versiones ACTIVE).
    instrument_service = InstrumentService(session)
    version = await instrument_service.update_version(
        SHORT_VERSION_ID, InstrumentVersionUpdate(status="ACTIVE")
    )
    print(f"[activar] instrument_version id={version.id} status={version.status}")
    return data


async def create_project(session: AsyncSession, owner: User) -> tuple[Project, "Survey", "Study"]:
    project_service = ProjectService(session)
    project = await project_service.create(
        ProjectCreate(
            owner_user_id=owner.id,
            name="Servicios Andinos S.A.C. — DEMO",
            project_type="CUSTOM",
            description=(
                "Proyecto CENSOPAS-COPSOQ (versión corta, banco de ítems oficial) — "
                f"generado por scripts/seed_short_project_official.py. {DISCLAIMER}"
            ),
            metadata={
                "demo": True,
                "demo_code": DEMO_CODE,
                "seed_version": SEED_VERSION,
                "disclaimer": DISCLAIMER,
                "censopas_version_kind": "SHORT",
                "instrument_id": 1,
                "instrument_version_id": SHORT_VERSION_ID,
                "censopas_auto_provisioned": True,
                "censopas_provisioning_version": "short-official-seed-v1",
            },
        )
    )
    project.project_type = "CENSO"
    await session.commit()
    await session.refresh(project)

    survey_service = SurveyService(session)
    survey = await survey_service.create_from_instrument(
        project.id,
        SurveyFromInstrumentCreate(
            created_by_user_id=owner.id,
            instrument_version_id=SHORT_VERSION_ID,
            name="Cuestionario CENSOPAS-COPSOQ — Servicios Andinos S.A.C.",
            description=f"Formulario autoaplicado, anónimo, confidencial y voluntario. {DISCLAIMER}",
            survey_type="CENSO",
        ),
    )
    survey.status = "ACTIVE"
    project.metadata_ = {**(project.metadata_ or {}), "survey_id": survey.id}
    await session.commit()
    await session.refresh(survey)

    period_start = date(2026, 6, 1)
    period_end = date(2026, 6, 19)
    study_service = StudyService(session)
    study = await study_service.create(
        project.id,
        StudyCreate(
            survey_id=survey.id,
            name="Aplicación CENSOPAS versión corta 2026 — Servicios Andinos S.A.C.",
            study_type="CENSO",
            start_at=datetime(period_start.year, period_start.month, period_start.day, tzinfo=UTC),
            end_at=datetime(period_end.year, period_end.month, period_end.day, 23, 59, tzinfo=UTC),
            min_publishable_n=5,
            settings={"demo": True, "demo_code": DEMO_CODE},
            requires_invitation=False,
        ),
    )
    return project, survey, study


async def register_exogenous_variables(
    session: AsyncSession, project: Project
) -> dict[str, Variable]:
    stmt = select(Question).where(
        Question.instrument_version_id == SHORT_VERSION_ID, Question.research_role == "EXOGENOUS"
    )
    questions_by_code = {q.code: q for q in (await session.execute(stmt)).scalars().all()}
    variables: dict[str, Variable] = {}
    for field_code, q_code, level, free_text in PROFILE_FIELDS:
        question = questions_by_code.get(q_code)
        if question is None:
            continue
        variable = Variable(
            project_id=project.id,
            instrument_version_id=SHORT_VERSION_ID,
            question_id=question.id,
            code=field_code,
            name=question.question_text,
            label=question.question_text,
            variable_type="EXOGENOUS",
            data_type="TEXT" if free_text else "CATEGORY",
            measurement_level=level,
            role="EXOGENOUS",
            is_editable=True,
            metadata_={"research_role": "EXOGENOUS", "source_code": q_code, "official": True},
        )
        session.add(variable)
        variables[field_code] = variable
    await session.commit()
    for variable in variables.values():
        await session.refresh(variable)
    return variables


async def run() -> dict:
    async with AsyncSessionLocal() as session:
        owner = (
            await session.execute(select(User).where(User.email == OWNER_EMAIL))
        ).scalar_one_or_none()
        if owner is None:
            raise RuntimeError(
                f"No existe el usuario {OWNER_EMAIL}; créelo primero (POST /api/v1/auth/register)."
            )
        print(f"[owner] {owner.email} (id={owner.id})")

        await reset_owner_projects(session, owner)
        data = await import_official_short(session)

        instrument = await session.get(Instrument, 1)
        instrument.metadata_ = {**(instrument.metadata_ or {}), "official_equivalence_enabled": False}
        await session.commit()

        barem = await import_reference_barem(session, SHORT_VERSION_ID, "Baremo referencia — CENSOPAS corta (ítems oficiales)")

        project, survey, study = await create_project(session, owner)
        exo_vars = await register_exogenous_variables(session, project)

        from app.models.study import StudyUnitType, StudyUnit

        area_units: dict[str, StudyUnit] = {}
        unit_type = StudyUnitType(study_id=study.id, code="AREA", name="Área / departamento", is_sensitive=False, sort_order=1)
        session.add(unit_type)
        await session.flush()
        for area_name in AREAS:
            unit = StudyUnit(study_unit_type_id=unit_type.id, code=area_name.upper().replace(" ", "_"), name=area_name)
            session.add(unit)
            area_units[area_name] = unit
        await session.flush()

        study_service = StudyService(session)
        await study_service.update(study.id, StudyUpdate(barem_id=barem.id))
        project.metadata_ = {**(project.metadata_ or {}), "barem_id": barem.id}
        await session.commit()
        study = await study_service.open(study.id)

        short_questions = [q for q in data["questions"] if q["version"] == "short"]
        scored_questions = [q for q in short_questions if q["is_scored"]]
        scored_by_construct: dict[str, list[str]] = {}
        item_direction: dict[str, str] = {}
        for q in scored_questions:
            scored_by_construct.setdefault(q["dimension_code"], []).append(q["code"])
            item_direction[q["code"]] = q["provisional_scoring_direction"]

        options_catalog_by_code = {
            q["code"]: [str(o["raw_code"]) for o in q["options"]] for q in short_questions
        }

        dim_tier_lists = {
            dim: pick_tier_list(counts, random.Random(2000 + i))
            for i, (dim, counts) in enumerate(DIM_TARGETS.items())
        }

        area_list = [name for name, n in AREA_SIZES.items() for _ in range(n)]
        RNG.shuffle(area_list)
        sexo_list = ["1"] * 11 + ["2"] * 9  # Mujer / Hombre
        RNG.shuffle(sexo_list)

        q_id_by_code: dict[str, int] = {}
        stmt = select(Question).where(Question.instrument_version_id == SHORT_VERSION_ID)
        for q in (await session.execute(stmt)).scalars().all():
            q_id_by_code[q.code] = q.id
        options_by_question = await load_question_options(session, SHORT_VERSION_ID)

        period_start, period_end = date(2026, 6, 1), date(2026, 6, 19)
        sessions: list[ResponseSession] = []
        for _ in range(20):
            started = random_datetime(RNG, period_start, period_end)
            completed = started + timedelta(minutes=RNG.randint(9, 16))
            sessions.append(
                ResponseSession(
                    study_id=study.id,
                    status="COMPLETED",
                    validation_status="VALID",
                    started_at=started,
                    completed_at=completed,
                    duration_seconds=int((completed - started).total_seconds()),
                    completion_pct=100.0,
                    metadata_={"demo": True, "seed_version": SEED_VERSION},
                )
            )
        session.add_all(sessions)
        await session.flush()

        responses: list[Response] = []
        session_units: list[ResponseSessionUnit] = []
        for idx, resp_session in enumerate(sessions):
            area_name = area_list[idx]
            session_units.append(
                ResponseSessionUnit(response_session_id=resp_session.id, study_unit_id=area_units[area_name].id)
            )

            for field_code, q_code, _level, free_text in PROFILE_FIELDS:
                q_id = q_id_by_code.get(q_code)
                if q_id is None:
                    continue
                if field_code == "AREA":
                    responses.append(
                        Response(
                            study_id=study.id, response_session_id=resp_session.id, question_id=q_id,
                            text_value=area_name, answered_at=resp_session.completed_at,
                        )
                    )
                elif field_code == "PUESTO":
                    job = RNG.choice(JOB_TITLES_BY_AREA[area_name])
                    responses.append(
                        Response(
                            study_id=study.id, response_session_id=resp_session.id, question_id=q_id,
                            text_value=job, answered_at=resp_session.completed_at,
                        )
                    )
                elif field_code == "SEXO":
                    raw_code = sexo_list[idx]
                    option = options_by_question[q_id][raw_code]
                    responses.append(
                        Response(
                            study_id=study.id, response_session_id=resp_session.id, question_id=q_id,
                            option_id=option.id, raw_code=option.raw_code, numeric_value=option.numeric_value,
                            answered_at=resp_session.completed_at,
                        )
                    )
                else:
                    n_options = len(options_catalog_by_code[q_code])
                    raw_code = str(RNG.randint(1, n_options))
                    option = options_by_question[q_id][raw_code]
                    responses.append(
                        Response(
                            study_id=study.id, response_session_id=resp_session.id, question_id=q_id,
                            option_id=option.id, raw_code=option.raw_code, numeric_value=option.numeric_value,
                            answered_at=resp_session.completed_at,
                        )
                    )

            for dim_code, _ in DIMENSIONS:
                tier = dim_tier_lists[dim_code][idx]
                base = TIER_BASE[tier]
                for q_code in scored_by_construct[dim_code]:
                    q_id = q_id_by_code[q_code]
                    direction = item_direction[q_code]
                    raw_code = raw_code_for_target(direction, base)
                    option = options_by_question[q_id][raw_code]
                    responses.append(
                        Response(
                            study_id=study.id, response_session_id=resp_session.id, question_id=q_id,
                            option_id=option.id, raw_code=option.raw_code, numeric_value=option.numeric_value,
                            answered_at=resp_session.completed_at,
                        )
                    )
        session.add_all(responses)
        session.add_all(session_units)
        await session.commit()

        _, summary = await run_canonical_scoring(session, study.id)
        print(f"[{DEMO_CODE}] scoring canónico: {summary.model_dump()}")

        await seed_plan_and_bsc_short(session, study)
        await seed_analytics_exports_reports(
            session,
            owner,
            project,
            study,
            version_id=SHORT_VERSION_ID,
            exo_vars=exo_vars,
            construct_codes=[code for code, _ in DIMENSIONS],
            compare_pairs=[("D1", "AREA"), ("D5", "AREA"), ("D1", "SEXO")],
            spearman_exo_codes=["EDAD"],
            cluster_codes=["D1", "D2", "D5"],
            logistic_outcome_code="SEXO",
            logistic_predictor_codes=["D1", "D5"],
        )

        return {"project_id": project.id, "study_id": study.id, "survey_id": survey.id, "owner_email": OWNER_EMAIL, "seed_version": SEED_VERSION}


async def main() -> None:
    try:
        result = await run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
