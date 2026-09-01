"""Seed reproducible de datos demo CENSOPAS-COPSOQ.

Implementa la regla de datos demo del documento de requisitos
"COLMENA — Requisitos CENSOPAS-COPSOQ y Datos Demo.md" (§2-4, §75-79):

    seed backend -> servicios/modelos existentes -> base de datos -> endpoints reales -> frontend

No crea JSON estáticos ni resultados hardcodeados: construye el instrumento
(dimensiones/subdimensiones/ítems/opciones/scoring_rules), el proyecto, la
encuesta, el estudio, las sesiones de respuesta con `raw_code` real y ejecuta
los DOS motores de scoring que ya expone el backend (el específico CENSOPAS
en `censopas_service.py`, usado por Constructor/Analítica/unit-results, y el
motor genérico `scoring_service.py`, usado por Resultados/Baremos) para que
todo lo que el frontend muestre venga de filas persistidas.

Todo el contenido textual (ítems, nombres de opciones, hallazgos) es
SINTÉTICO y está marcado como tal en cada proyecto/instrumento — no reproduce
el banco de ítems oficial del manual CENSOPAS-COPSOQ (no disponible para este
seed), sólo su estructura pública (6 dimensiones, 20 subdimensiones, conteos
42/31 y 112/69 preguntas/ítems psicosociales).

Reproducible: reset_demo() borra los dos proyectos demo (y por cascada FK
todo lo que cuelga de sus estudios) y limpia el contenido de las versiones de
instrumento compartidas 1 (SHORT) y 2 (MEDIUM) antes de reconstruirlas, así
que `python scripts/seed_censopas_demo.py` puede ejecutarse varias veces sin
dejar datos inconsistentes (seed_version = CENSOPAS_DEMO_V1).

Uso (desde backend/, con el venv de poetry activo):
    python scripts/seed_censopas_demo.py
"""

from __future__ import annotations

import asyncio
import json
import random
import sys
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models.audit import AuditLog
from app.models.bsc import ActionPlan, ActionPlanItem, Kpi, KpiMeasurement
from app.models.censopas import Barem, BaremBand, BaremCutoff, ConstructResult, ConstructScore
from app.models.construct import Construct, ConstructItem
from app.models.instrument import Instrument, InstrumentVersion
from app.models.option_set import OptionSet, OptionSetOption
from app.models.participant import StudyInvitation
from app.models.project import Project
from app.models.question import Question
from app.models.response import Response, ResponseSession, ResponseSessionUnit
from app.models.scoring import ScoringRule
from app.models.study import Study, StudyUnit, StudyUnitType
from app.models.survey import Survey
from app.models.user import User
from app.models.variable import Variable
from app.schemas.censopas import (
    CensopasBaremCutoffManifest,
    CensopasBaremManifest,
    CensopasManifest,
    CensopasManifestConstruct,
    CensopasManifestItemLink,
    CensopasManifestOption,
    CensopasManifestQuestion,
    CensopasManifestScale,
    CensopasManifestScoringRule,
)
from app.schemas.analytics import (
    ConstructCompareGroupsRequest,
    KMeansRequest,
    LogisticRegressionRequest,
    NormalityRequest,
    ReliabilityRequest,
    SpearmanMatrixRequest,
)
from app.schemas.exports import ExportCreate
from app.schemas.projects import ProjectCreate
from app.schemas.reports import ReportRunCreate
from app.schemas.studies import StudyCreate, StudyUnitCreate, StudyUnitTypeCreate, StudyUpdate
from app.schemas.surveys import SurveyFromInstrumentCreate
from app.services.advanced_analysis_service import AdvancedAnalysisService
from app.services.analysis_service import AnalysisService
from app.services.censopas_service import CensopasScoringService
from app.services.export_service import ExportService
from app.services.project_service import ProjectService
from app.services.report_service import ReportService
from app.services.scoring_orchestrator import run_canonical_scoring
from app.services.study_service import StudyService
from app.services.survey_service import SurveyService

OWNER_EMAIL = "johaba.jb@gmail.com"
SHORT_VERSION_ID = 1
MEDIUM_VERSION_ID = 2
DEMO_CODE_SHORT = "SYN-C20-2026"
DEMO_CODE_MEDIUM = "SYN-M200-2026"
SEED_VERSION = "CENSOPAS_DEMO_V1"

DISCLAIMER = (
    "DATOS SINTÉTICOS — NO CORRESPONDE A UNA EVALUACIÓN REAL — "
    "NO USAR PARA DECISIONES LABORALES."
)
CONTENT_NOTICE = (
    "Estructura oficial (dimensiones/subdimensiones/conteos) del Manual técnico "
    "CENSOPAS-COPSOQ; texto de ítems y opciones GENERADO para este demo (no es el "
    "banco de ítems oficial). No usar como equivalente a una evaluación oficial."
)

RNG = random.Random(20260817)

DIMENSIONS: list[tuple[str, str]] = [
    ("D1", "Exigencias psicológicas en el trabajo"),
    ("D2", "Conflicto trabajo-familia"),
    ("D3", "Control sobre el trabajo"),
    ("D4", "Apoyo social y calidad de liderazgo"),
    ("D5", "Compensaciones del trabajo"),
    ("D6", "Capital social"),
]

# (código, nombre, dimensión padre)
SUBDIMENSIONS: list[tuple[str, str, str]] = [
    ("S1", "Exigencias cuantitativas", "D1"),
    ("S2", "Ritmo de trabajo", "D1"),
    ("S3", "Exigencias emocionales", "D1"),
    ("S4", "Exigencia de esconder emociones", "D1"),
    ("S5", "Doble presencia", "D2"),
    ("S6", "Influencia", "D3"),
    ("S7", "Posibilidades de desarrollo", "D3"),
    ("S8", "Sentido del trabajo", "D3"),
    ("S9", "Apoyo social de los compañeros", "D4"),
    ("S10", "Apoyo social de superiores", "D4"),
    ("S11", "Calidad de liderazgo", "D4"),
    ("S12", "Sentimiento de grupo", "D4"),
    ("S13", "Previsibilidad", "D4"),
    ("S14", "Claridad de rol", "D4"),
    ("S15", "Conflicto de rol", "D4"),
    ("S16", "Reconocimiento", "D5"),
    ("S17", "Inseguridad sobre el empleo", "D5"),
    ("S18", "Inseguridad sobre las condiciones de trabajo", "D5"),
    ("S19", "Justicia", "D6"),
    ("S20", "Confianza vertical", "D6"),
]
# 9 subdimensiones con 4 ítems, 11 con 3 ítems -> 36 + 33 = 69 (harness §15/§37).
SUBDIM_4_ITEMS = {"S1", "S2", "S3", "S9", "S10", "S11", "S14", "S17", "S19"}

# Distribución de los 31 ítems psicosociales de la versión corta entre las 6
# dimensiones (harness §8: 31 ítems, 6 dimensiones, sin subdimensiones públicas).
SHORT_DIM_ITEM_COUNTS = {"D1": 6, "D2": 3, "D3": 5, "D4": 9, "D5": 5, "D6": 3}

TIER_BASE = {"FAV": 1, "INT": 3, "DESF": 5}
TIER_LABELS = {"FAV": "favorable", "INT": "intermedio", "DESF": "desfavorable"}


def even_values(n: int) -> list[float]:
    if n == 1:
        return [1.0]
    step = 4.0 / (n - 1)
    return [round(1.0 + i * step, 4) for i in range(n)]


def make_scale(code: str, name: str, labels: list[str]) -> CensopasManifestScale:
    values = even_values(len(labels))
    return CensopasManifestScale(
        code=code,
        name=name,
        options=[
            CensopasManifestOption(
                raw_code=str(i + 1), label=label, numeric_value=values[i], sort_order=i
            )
            for i, label in enumerate(labels)
        ],
    )


LIKERT_5 = make_scale(
    "LIKERT_5_FREC",
    "Frecuencia (Likert 5 puntos, demo)",
    ["Nunca", "Sólo alguna vez", "Algunas veces", "Muchas veces", "Siempre"],
)
AGREEMENT_5 = make_scale(
    "LIKERT_5_ACUERDO",
    "Grado de acuerdo (Likert 5 puntos, demo)",
    [
        "Totalmente en desacuerdo",
        "En desacuerdo",
        "Ni de acuerdo ni en desacuerdo",
        "De acuerdo",
        "Totalmente de acuerdo",
    ],
)

PROFILE_FIELDS: list[dict] = [
    {"code": "SEXO", "name": "Sexo", "labels": ["Mujer", "Hombre"]},
    {"code": "EDAD", "name": "Edad (agrupada)", "labels": ["<31", "31-45", ">45"]},
    {
        "code": "AREA",
        "name": "Área / departamento",
        "labels": [
            "Operaciones",
            "Mantenimiento",
            "Administración",
            "Logística",
            "Comercial",
            "SST y RR. HH.",
            "Proyecto Piloto",
        ],
    },
    {
        "code": "PUESTO",
        "name": "Puesto",
        "labels": ["Operativo", "Administrativo", "Supervisión"],
    },
    {
        "code": "NIVEL_INSTRUCCION",
        "name": "Nivel de instrucción",
        "labels": ["Secundaria", "Técnica", "Universitaria"],
    },
    {
        "code": "TIEMPO_PUESTO",
        "name": "Tiempo en el puesto",
        "labels": ["<1 año", "1-3 años", ">3 años"],
    },
    {
        "code": "RELACION_LABORAL",
        "name": "Relación laboral",
        "labels": ["Planilla", "Locación de servicios"],
    },
    {"code": "TURNO", "name": "Turno / horario", "labels": ["Diurno", "Rotativo"]},
    {
        "code": "SEDE",
        "name": "Sede",
        "labels": ["Lima", "Operación Sur", "Operación Centro"],
    },
    {"code": "CONTRATO", "name": "Tipo de contrato", "labels": ["Indefinido", "Plazo fijo"]},
    {
        "code": "REMUNERACION_RANGO",
        "name": "Rango de remuneración actualizado (módulo descriptivo complementario)",
        "labels": ["< S/1500", "S/1500 - S/3000", "> S/3000"],
    },
]

COMPLEMENTARY_MODULES: list[dict] = [
    {"code": "SALUD", "name": "Salud percibida", "count": 4},
    {"code": "BIENESTAR", "name": "Bienestar", "count": 4},
    {"code": "SATISFACCION", "name": "Satisfacción laboral", "count": 4},
    {"code": "TELETRABAJO", "name": "Teletrabajo", "count": 3},
    {"code": "ERGONOMIA", "name": "Ergonomía", "count": 3},
    {"code": "VIOLENCIA", "name": "Violencia en el trabajo", "count": 3},
    {"code": "HOSTIGAMIENTO", "name": "Hostigamiento", "count": 3},
    {"code": "CLIMA", "name": "Clima laboral", "count": 3},
    {"code": "OTROS", "name": "Otros aspectos complementarios", "count": 5},
]  # 4+4+4+3+3+3+3+3+5 = 32 (+11 perfil = 43 descriptivas, harness §8/§37)


@dataclass
class ManifestBuild:
    manifest: CensopasManifest
    scored_by_construct: dict[str, list[str]] = field(default_factory=dict)  # construct_code -> [question_code]
    item_direction: dict[str, str] = field(default_factory=dict)  # question_code -> DIRECT/REVERSE
    profile_question_codes: dict[str, str] = field(default_factory=dict)  # field_code -> question_code


def _profile_questions(sort_start: int) -> tuple[list[CensopasManifestQuestion], list[CensopasManifestScale], dict[str, str]]:
    questions: list[CensopasManifestQuestion] = []
    scales: list[CensopasManifestScale] = []
    code_map: dict[str, str] = {}
    for i, spec in enumerate(PROFILE_FIELDS):
        scale_code = f"SCALE_{spec['code']}"
        scales.append(make_scale(scale_code, f"Opciones de {spec['name']}", spec["labels"]))
        q_code = f"PERFIL-{spec['code']}"
        code_map[spec["code"]] = q_code
        questions.append(
            CensopasManifestQuestion(
                code=q_code,
                source_code=q_code,
                question_text=f"[Perfil demo] {spec['name']}",
                question_type="SINGLE_CHOICE",
                is_scored=False,
                research_role="EXOGENOUS",
                option_set_code=scale_code,
                is_required=True,
                sort_order=sort_start + i,
                category="Datos de perfil",
                metadata={"demo": True},
            )
        )
    return questions, scales, code_map


def _complementary_questions(sort_start: int) -> list[CensopasManifestQuestion]:
    questions: list[CensopasManifestQuestion] = []
    idx = 0
    for module in COMPLEMENTARY_MODULES:
        for n in range(1, module["count"] + 1):
            code = f"COMP-{module['code']}-{n:02d}"
            questions.append(
                CensopasManifestQuestion(
                    code=code,
                    source_code=code,
                    question_text=(
                        f"[Módulo complementario demo] Afirmación sintética de «{module['name']}» "
                        f"(ítem {n} de {module['count']})."
                    ),
                    question_type="SINGLE_CHOICE",
                    is_scored=False,
                    research_role=None,
                    option_set_code=AGREEMENT_5.code,
                    is_required=False,
                    sort_order=sort_start + idx,
                    category=f"Módulo complementario: {module['name']}",
                    metadata={"module": "COMPLEMENTARY_MODULE", "module_name": module["name"], "demo": True},
                )
            )
            idx += 1
    return questions


def build_short_manifest() -> ManifestBuild:
    profile_questions, profile_scales, profile_code_map = _profile_questions(sort_start=0)

    scored_questions: list[CensopasManifestQuestion] = []
    constructs: list[CensopasManifestConstruct] = []
    scoring_rules: list[CensopasManifestScoringRule] = []
    scored_by_construct: dict[str, list[str]] = {}
    item_direction: dict[str, str] = {}

    constructs.append(
        CensopasManifestConstruct(
            code="CENSOPAS_ROOT",
            name="CENSOPAS-COPSOQ — Versión corta (demo)",
            construct_type="VARIABLE",
            sort_order=0,
        )
    )

    sort_cursor = len(profile_questions)
    for d_index, (dim_code, dim_name) in enumerate(DIMENSIONS):
        n_items = SHORT_DIM_ITEM_COUNTS[dim_code]
        item_links: list[CensopasManifestItemLink] = []
        codes: list[str] = []
        for i in range(1, n_items + 1):
            q_code = f"C-{dim_code}-{i:02d}"
            direction = "DIRECT" if i % 2 == 1 else "REVERSE"
            item_direction[q_code] = direction
            scored_questions.append(
                CensopasManifestQuestion(
                    code=q_code,
                    source_code=q_code,
                    question_text=(
                        f"[Ítem demo {q_code}] Afirmación sintética asociada a «{dim_name}» "
                        f"(ítem {i} de {n_items})."
                    ),
                    question_type="LIKERT",
                    is_scored=True,
                    research_role="ENDOGENOUS",
                    option_set_code=LIKERT_5.code,
                    is_required=True,
                    sort_order=sort_cursor,
                    category=dim_name,
                    metadata={"demo": True},
                )
            )
            sort_cursor += 1
            item_links.append(
                CensopasManifestItemLink(
                    question_code=q_code, item_role="SCORED", scoring_direction=direction, sort_order=i
                )
            )
            scoring_rules.append(
                CensopasManifestScoringRule(
                    question_code=q_code,
                    risk_map={"1": 1.0, "2": 2.0, "3": 3.0, "4": 4.0, "5": 5.0},
                    source_reference="Colmena CENSOPAS demo — mapa identidad 1..5 (no oficial)",
                    rule_version="DEMO-V1",
                )
            )
            codes.append(q_code)
        scored_by_construct[dim_code] = codes
        constructs.append(
            CensopasManifestConstruct(
                code=dim_code,
                name=dim_name,
                construct_type="DIMENSION",
                parent_code="CENSOPAS_ROOT",
                sort_order=d_index + 1,
                items=item_links,
            )
        )

    manifest = CensopasManifest(
        version_kind="SHORT",
        manifest_version="DEMO-V1",
        source_reference=CONTENT_NOTICE,
        scales=[LIKERT_5, *profile_scales],
        questions=[*profile_questions, *scored_questions],
        constructs=constructs,
        scoring_rules=scoring_rules,
    )
    return ManifestBuild(
        manifest=manifest,
        scored_by_construct=scored_by_construct,
        item_direction=item_direction,
        profile_question_codes=profile_code_map,
    )


def build_medium_manifest() -> ManifestBuild:
    profile_questions, profile_scales, profile_code_map = _profile_questions(sort_start=0)
    complementary_questions = _complementary_questions(sort_start=len(profile_questions))

    scored_questions: list[CensopasManifestQuestion] = []
    constructs: list[CensopasManifestConstruct] = []
    scoring_rules: list[CensopasManifestScoringRule] = []
    scored_by_construct: dict[str, list[str]] = {}
    item_direction: dict[str, str] = {}

    constructs.append(
        CensopasManifestConstruct(
            code="CENSOPAS_ROOT",
            name="CENSOPAS-COPSOQ — Versión media (demo)",
            construct_type="VARIABLE",
            sort_order=0,
        )
    )
    for d_index, (dim_code, dim_name) in enumerate(DIMENSIONS):
        constructs.append(
            CensopasManifestConstruct(
                code=dim_code,
                name=dim_name,
                construct_type="DIMENSION",
                parent_code="CENSOPAS_ROOT",
                sort_order=d_index + 1,
            )
        )

    sort_cursor = len(profile_questions) + len(complementary_questions)
    for s_index, (sub_code, sub_name, parent_dim) in enumerate(SUBDIMENSIONS):
        n_items = 4 if sub_code in SUBDIM_4_ITEMS else 3
        item_links: list[CensopasManifestItemLink] = []
        codes: list[str] = []
        for i in range(1, n_items + 1):
            q_code = f"M-{sub_code}-{i:02d}"
            direction = "DIRECT" if i % 2 == 1 else "REVERSE"
            item_direction[q_code] = direction
            scored_questions.append(
                CensopasManifestQuestion(
                    code=q_code,
                    source_code=q_code,
                    question_text=(
                        f"[Ítem demo {q_code}] Afirmación sintética asociada a «{sub_name}» "
                        f"(ítem {i} de {n_items})."
                    ),
                    question_type="LIKERT",
                    is_scored=True,
                    research_role="ENDOGENOUS",
                    option_set_code=LIKERT_5.code,
                    is_required=True,
                    sort_order=sort_cursor,
                    category=f"{parent_dim} · {sub_name}",
                    metadata={"demo": True},
                )
            )
            sort_cursor += 1
            item_links.append(
                CensopasManifestItemLink(
                    question_code=q_code, item_role="SCORED", scoring_direction=direction, sort_order=i
                )
            )
            scoring_rules.append(
                CensopasManifestScoringRule(
                    question_code=q_code,
                    risk_map={"1": 1.0, "2": 2.0, "3": 3.0, "4": 4.0, "5": 5.0},
                    source_reference="Colmena CENSOPAS demo — mapa identidad 1..5 (no oficial)",
                    rule_version="DEMO-V1",
                )
            )
            codes.append(q_code)
        scored_by_construct[sub_code] = codes
        constructs.append(
            CensopasManifestConstruct(
                code=sub_code,
                name=sub_name,
                construct_type="SUBDIMENSION",
                parent_code=parent_dim,
                sort_order=100 + s_index,
                items=item_links,
            )
        )

    manifest = CensopasManifest(
        version_kind="MEDIUM",
        manifest_version="DEMO-V1",
        source_reference=CONTENT_NOTICE,
        scales=[LIKERT_5, AGREEMENT_5, *profile_scales],
        questions=[*profile_questions, *complementary_questions, *scored_questions],
        constructs=constructs,
        scoring_rules=scoring_rules,
    )
    return ManifestBuild(
        manifest=manifest,
        scored_by_construct=scored_by_construct,
        item_direction=item_direction,
        profile_question_codes=profile_code_map,
    )


# --------------------------------------------------------------------------
# Reset (reproducibilidad, harness §4)
# --------------------------------------------------------------------------

async def reset_instrument_version_content(session: AsyncSession, version_id: int) -> None:
    await session.execute(delete(ScoringRule).where(ScoringRule.instrument_version_id == version_id))
    barem_ids = (
        (await session.execute(select(Barem.id).where(Barem.instrument_version_id == version_id)))
        .scalars()
        .all()
    )
    if barem_ids:
        await session.execute(delete(BaremBand).where(BaremBand.barem_id.in_(barem_ids)))
        await session.execute(delete(BaremCutoff).where(BaremCutoff.barem_id.in_(barem_ids)))
        await session.execute(delete(Barem).where(Barem.id.in_(barem_ids)))
    await session.execute(delete(Construct).where(Construct.instrument_version_id == version_id))
    await session.execute(delete(Question).where(Question.instrument_version_id == version_id))
    await session.execute(delete(OptionSet).where(OptionSet.instrument_version_id == version_id))
    await session.commit()


async def reset_demo(session: AsyncSession) -> None:
    projects = (await session.execute(select(Project))).scalars().all()
    demo_project_ids = {
        project.id
        for project in projects
        if (project.metadata_ or {}).get("demo_code") in (DEMO_CODE_SHORT, DEMO_CODE_MEDIUM)
    }
    for project in projects:
        if project.id in demo_project_ids:
            print(f"[reset] borrando proyecto demo previo id={project.id} ({project.name})")
            await session.execute(delete(AuditLog).where(AuditLog.project_id == project.id))
            await session.execute(delete(Project).where(Project.id == project.id))
    # El aprovisionador empresarial relaciona su baremo con el proyecto en
    # metadata (sin FK). Limpia cualquier baremo que haya quedado huérfano si
    # una corrida anterior del seed se interrumpió después de crear el proyecto.
    if demo_project_ids:
        barems = (await session.execute(select(Barem))).scalars().all()
        orphan_barem_ids = [
            barem.id
            for barem in barems
            if (barem.metadata_ or {}).get("project_id") in demo_project_ids
        ]
        if orphan_barem_ids:
            await session.execute(delete(Barem).where(Barem.id.in_(orphan_barem_ids)))
    await session.commit()
    await reset_instrument_version_content(session, SHORT_VERSION_ID)
    await reset_instrument_version_content(session, MEDIUM_VERSION_ID)


# --------------------------------------------------------------------------
# Importación de instrumento + baremo (servicios reales)
# --------------------------------------------------------------------------

async def import_instrument(session: AsyncSession, version_id: int, build: ManifestBuild) -> dict:
    service = CensopasScoringService(session)
    result = await service.import_manifest(version_id, build.manifest)
    print(
        f"[instrumento v{version_id}] importado: {result.imported} — "
        f"ready_for_scoring={result.readiness.ready_for_scoring} "
        f"errors={result.readiness.errors}"
    )
    return result.imported


async def import_reference_barem(
    session: AsyncSession, version_id: int, name: str
) -> Barem:
    stmt = select(Construct).where(
        Construct.instrument_version_id == version_id,
        Construct.construct_type.in_(("DIMENSION", "SUBDIMENSION")),
    )
    constructs = list((await session.execute(stmt)).scalars().all())

    service = CensopasScoringService(session)
    manifest = CensopasBaremManifest(
        name=name,
        barem_type="REFERENCE",
        population_label="Población de referencia sintética — demo Colmena",
        source_reference=(
            "Corte demostrativo por terciles (0-33.34 / 33.34-66.67 / 66.67-100). "
            "NO es un baremo oficial CENSOPAS-COPSOQ; official_equivalence_enabled=false."
        ),
        barem_version="DEMO-V1",
        authority=None,
        cutoffs=[
            CensopasBaremCutoffManifest(
                construct_code=construct.code,
                cut_1=33.34,
                cut_2=66.67,
                direction="LOWER_BETTER",
                favorable_label="FAVORABLE",
                intermediate_label="INTERMEDIO",
                unfavorable_label="DESFAVORABLE",
            )
            for construct in constructs
        ],
    )
    imported = await service.import_barem_manifest(version_id, manifest)
    barem_id = imported.barem_id
    # import_barem_manifest materializa tanto los cortes autorales como sus
    # tres bandas ejecutables. No volver a insertarlas aquí: además de ser
    # redundante, viola la unicidad (barem, constructo, severidad).
    band_count = len(constructs) * 3
    print(
        f"[barem v{version_id}] barem_id={barem_id} "
        f"cutoffs={len(constructs)} bands={band_count}"
    )
    return await service.repo.get_barem(barem_id)


# --------------------------------------------------------------------------
# Helpers de generación de personas / respuestas
# --------------------------------------------------------------------------

def raw_code_for_target(direction: str, target_risk_value: int) -> str:
    if direction == "REVERSE":
        return str(6 - target_risk_value)
    return str(target_risk_value)


def pick_tier_list(counts: dict[str, int], rng: random.Random) -> list[str]:
    tiers: list[str] = []
    for tier, n in counts.items():
        tiers.extend([tier] * n)
    rng.shuffle(tiers)
    return tiers


async def load_question_options(session: AsyncSession, version_id: int) -> dict[int, dict[str, OptionSetOption]]:
    stmt = (
        select(Question)
        .where(Question.instrument_version_id == version_id)
    )
    questions = list((await session.execute(stmt)).scalars().all())
    option_sets_stmt = select(OptionSet).where(OptionSet.instrument_version_id == version_id)
    option_sets = list((await session.execute(option_sets_stmt)).scalars().all())
    options_stmt = select(OptionSetOption).where(
        OptionSetOption.option_set_id.in_([o.id for o in option_sets])
    )
    all_options = list((await session.execute(options_stmt)).scalars().all())
    by_set: dict[int, dict[str, OptionSetOption]] = {}
    for opt in all_options:
        by_set.setdefault(opt.option_set_id, {})[opt.raw_code] = opt
    result: dict[int, dict[str, OptionSetOption]] = {}
    for q in questions:
        if q.option_set_id is not None:
            result[q.id] = by_set.get(q.option_set_id, {})
    return result


def questions_by_code(build: ManifestBuild) -> dict[str, CensopasManifestQuestion]:
    return {q.code: q for q in build.manifest.questions}


# --------------------------------------------------------------------------
# Proyecto base (project/survey/study)
# --------------------------------------------------------------------------

async def create_base_project(
    session: AsyncSession,
    owner: User,
    *,
    name: str,
    demo_code: str,
    version_id: int,
    version_kind: str,
    period_start: date,
    period_end: date,
) -> tuple[Project, Survey]:
    project_service = ProjectService(session)
    project = await project_service.create(
        ProjectCreate(
            owner_user_id=owner.id,
            name=name,
            # El servicio aprovisiona automáticamente todo proyecto CENSO con
            # la versión oficial protegida. Este seed necesita deliberadamente
            # sus versiones sintéticas 1/2, así que crea primero un CUSTOM y lo
            # marca como CENSO una vez persistido, sin generar artefactos
            # oficiales redundantes que apunten a otra versión.
            project_type="CUSTOM",
            description=(
                f"Proyecto demo CENSOPAS-COPSOQ ({version_kind}) generado por "
                f"scripts/seed_censopas_demo.py — {DISCLAIMER}"
            ),
            metadata={
                "demo": True,
                "demo_code": demo_code,
                "seed_version": SEED_VERSION,
                "disclaimer": DISCLAIMER,
                "censopas_version_kind": version_kind,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "evaluador": "Equipo SST — Colmena (demo)",
                # El instrumento CENSOPAS es compartido (`is_system=True`,
                # `project_id=NULL`) — `GET /projects/{id}/instruments` no lo
                # lista porque filtra por project_id. `useProjectInstruments`
                # (frontend) cae de vuelta a este metadata "legado" para
                # resolverlo; sin esto, Constructor/Formulario ven 0 instrumentos.
                "instrument_id": 1,
                "instrument_version_id": version_id,
                "censopas_auto_provisioned": True,
                "censopas_provisioning_version": "demo-seed-v1",
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
            instrument_version_id=version_id,
            name=f"Cuestionario CENSOPAS-COPSOQ — {name}",
            description=f"Formulario autoaplicado, anónimo, confidencial y voluntario. {DISCLAIMER}",
            survey_type="CENSO",
        ),
    )
    survey.status = "ACTIVE"
    project.metadata_ = {**(project.metadata_ or {}), "survey_id": survey.id}
    await session.commit()
    await session.refresh(survey)
    return project, survey


ORDINAL_PROFILE_FIELDS = {"EDAD", "TIEMPO_PUESTO", "NIVEL_INSTRUCCION", "REMUNERACION_RANGO"}
# Campos de perfil con exactamente 2 categorías: measurement_level=BINARY los
# habilita como outcome de regresión logística (harness §64) además de como
# variable de agrupación (§56-58).
BINARY_PROFILE_FIELDS = {"SEXO", "RELACION_LABORAL", "TURNO", "CONTRATO"}


async def register_exogenous_variables(
    session: AsyncSession, project_id: int, version_id: int, profile_code_map: dict[str, str]
) -> dict[str, Variable]:
    """Registra `Variable(variable_type=EXOGENOUS)` para los campos de perfil ya
    creados por el manifiesto (evita duplicar preguntas vía VariableService)."""
    stmt = select(Question).where(
        Question.instrument_version_id == version_id, Question.research_role == "EXOGENOUS"
    )
    questions = {q.code: q for q in (await session.execute(stmt)).scalars().all()}
    field_by_code = {spec["code"]: spec for spec in PROFILE_FIELDS}
    variables_by_field: dict[str, Variable] = {}
    for field_code, q_code in profile_code_map.items():
        question = questions.get(q_code)
        if question is None:
            continue
        spec = field_by_code[field_code]
        if field_code in BINARY_PROFILE_FIELDS:
            level = "BINARY"
        elif field_code in ORDINAL_PROFILE_FIELDS:
            level = "ORDINAL"
        else:
            level = "NOMINAL"
        variable = Variable(
            project_id=project_id,
            instrument_version_id=version_id,
            question_id=question.id,
            code=field_code,
            name=spec["name"],
            label=question.question_text,
            variable_type="EXOGENOUS",
            data_type="CATEGORY",
            measurement_level=level,
            role="EXOGENOUS",
            is_editable=True,
            metadata_={"research_role": "EXOGENOUS", "demo": True},
        )
        session.add(variable)
        variables_by_field[field_code] = variable
    await session.commit()
    for variable in variables_by_field.values():
        await session.refresh(variable)
    return variables_by_field


async def register_construct_score_variable(
    session: AsyncSession, project_id: int, version_id: int, construct: Construct
) -> Variable:
    """Variable técnica `CONSTRUCT_SCORE` para un constructo puntual (mismo
    patrón que `ScoringService._materialize_construct_variables`, que sólo
    materializa la variable raíz) — habilita ese constructo como predictor/
    feature en k-means y regresión logística (harness §62/§64)."""
    stmt = select(Variable).where(
        Variable.project_id == project_id, Variable.construct_id == construct.id
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing
    variable = Variable(
        project_id=project_id,
        instrument_version_id=version_id,
        construct_id=construct.id,
        code=f"SCORE_{construct.code}",
        name=construct.name,
        label=f"Puntaje 0-100: {construct.name}",
        variable_type="CONSTRUCT_SCORE",
        data_type="DECIMAL",
        measurement_level="SCALE",
        role="DESCRIPTIVE",
        is_editable=False,
        metadata_={"source": "construct_scores.score_0_100", "demo": True},
    )
    session.add(variable)
    await session.commit()
    await session.refresh(variable)
    return variable


async def setup_area_units(
    session: AsyncSession, study_id: int, area_sizes: dict[str, int]
) -> dict[str, StudyUnit]:
    study_service = StudyService(session)
    unit_type = await study_service.create_unit_type(
        study_id,
        StudyUnitTypeCreate(code="AREA", name="Área / departamento", is_sensitive=False, sort_order=1),
    )
    units: dict[str, StudyUnit] = {}
    for area_name in area_sizes:
        unit = await study_service.create_unit(
            unit_type.id, StudyUnitCreate(code=area_name.upper().replace(" ", "_"), name=area_name)
        )
        units[area_name] = unit
    return units


def random_datetime(rng: random.Random, start: date, end: date) -> datetime:
    span_days = (end - start).days
    offset_days = rng.randint(0, max(span_days, 0))
    seconds = rng.randint(8 * 3600, 18 * 3600)  # jornada laboral
    d = start + timedelta(days=offset_days)
    return datetime(d.year, d.month, d.day, tzinfo=UTC) + timedelta(seconds=seconds)


# --------------------------------------------------------------------------
# DEMO A — SYN-C20-2026 (versión corta, 20 válidos)
# --------------------------------------------------------------------------

async def seed_demo_short(session: AsyncSession, owner: User, build: ManifestBuild) -> dict:
    period_start = date(2026, 6, 1)
    period_end = date(2026, 6, 19)
    rng = random.Random(101)

    project, survey = await create_base_project(
        session,
        owner,
        name="Servicios Andinos S.A.C. — DEMO",
        demo_code=DEMO_CODE_SHORT,
        version_id=SHORT_VERSION_ID,
        version_kind="SHORT",
        period_start=period_start,
        period_end=period_end,
    )
    exo_vars = await register_exogenous_variables(
        session, project.id, SHORT_VERSION_ID, build.profile_question_codes
    )

    study_service = StudyService(session)
    study = await study_service.create(
        project.id,
        StudyCreate(
            survey_id=survey.id,
            name="Aplicación CENSOPAS versión corta 2026 — Servicios Andinos (demo)",
            study_type="CENSO",
            start_at=datetime(period_start.year, period_start.month, period_start.day, tzinfo=UTC),
            end_at=datetime(period_end.year, period_end.month, period_end.day, 23, 59, tzinfo=UTC),
            min_publishable_n=5,
            settings={"demo": True, "demo_code": DEMO_CODE_SHORT},
            requires_invitation=False,
        ),
    )

    area_sizes = {"Administración": 8, "Operaciones": 7, "Comercial": 5}
    area_units = await setup_area_units(session, study.id, area_sizes)

    barem = await import_reference_barem(session, SHORT_VERSION_ID, "Baremo referencia demo — CENSOPAS corta")
    await study_service.update(study.id, StudyUpdate(barem_id=barem.id))
    project.metadata_ = {**(project.metadata_ or {}), "barem_id": barem.id}
    await session.commit()
    study = await study_service.open(study.id)

    # 20 invitaciones, todas consumidas (convocados = recibidos = válidos = 20, harness §75).
    invitations = [
        StudyInvitation(
            study_id=study.id,
            access_token_hash=f"demo-consumed-{DEMO_CODE_SHORT}-{i}",
            status="CONSUMED",
            sent_at=random_datetime(rng, period_start, period_end),
        )
        for i in range(20)
    ]
    for inv in invitations:
        inv.consumed_at = inv.sent_at + timedelta(minutes=rng.randint(5, 120))
    session.add_all(invitations)
    await session.commit()

    # Tier objetivo por dimensión (harness §35, 20 personas).
    dim_targets = {
        "D1": {"FAV": 3, "INT": 5, "DESF": 12},
        "D2": {"FAV": 4, "INT": 9, "DESF": 7},
        "D3": {"FAV": 10, "INT": 6, "DESF": 4},
        "D4": {"FAV": 5, "INT": 10, "DESF": 5},
        "D5": {"FAV": 3, "INT": 6, "DESF": 11},
        "D6": {"FAV": 11, "INT": 6, "DESF": 3},
    }
    dim_tier_lists = {
        dim: pick_tier_list(counts, random.Random(1000 + i))
        for i, (dim, counts) in enumerate(dim_targets.items())
    }

    # Perfil sociolaboral demo corto (harness §36): sexo 11/9, edad 9/8/3, área 8/7/5.
    sexo_list = ["Mujer"] * 11 + ["Hombre"] * 9
    edad_list = ["<31"] * 9 + ["31-45"] * 8 + [">45"] * 3
    rng.shuffle(sexo_list)
    rng.shuffle(edad_list)
    area_list = ["Administración"] * 8 + ["Operaciones"] * 7 + ["Comercial"] * 5
    rng.shuffle(area_list)

    q_by_code = questions_by_code(build)
    q_id_by_code: dict[str, int] = {}
    stmt = select(Question).where(Question.instrument_version_id == SHORT_VERSION_ID)
    for q in (await session.execute(stmt)).scalars().all():
        q_id_by_code[q.code] = q.id
    options_by_question = await load_question_options(session, SHORT_VERSION_ID)

    sessions: list[ResponseSession] = []
    for person in range(20):
        started = random_datetime(rng, period_start, period_end)
        completed = started + timedelta(minutes=rng.randint(9, 16))
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
        unit = area_units[area_name]
        session_units.append(ResponseSessionUnit(response_session_id=resp_session.id, study_unit_id=unit.id))

        profile_values = {
            "SEXO": sexo_list[idx],
            "EDAD": edad_list[idx],
            "AREA": area_name,
            "PUESTO": rng.choice(["Operativo", "Administrativo", "Supervisión"]),
            "NIVEL_INSTRUCCION": rng.choice(["Secundaria", "Técnica", "Universitaria"]),
            "TIEMPO_PUESTO": rng.choice(["<1 año", "1-3 años", ">3 años"]),
            "RELACION_LABORAL": rng.choice(["Planilla", "Locación de servicios"]),
            "TURNO": rng.choice(["Diurno", "Rotativo"]),
            "SEDE": rng.choice(["Lima", "Operación Sur", "Operación Centro"]),
            "CONTRATO": rng.choice(["Indefinido", "Plazo fijo"]),
            "REMUNERACION_RANGO": rng.choice(["< S/1500", "S/1500 - S/3000", "> S/3000"]),
        }
        for field_code, label in profile_values.items():
            q_code = build.profile_question_codes[field_code]
            q_id = q_id_by_code[q_code]
            spec = next(s for s in PROFILE_FIELDS if s["code"] == field_code)
            option = options_by_question[q_id][str(spec["labels"].index(label) + 1)]
            responses.append(
                Response(
                    study_id=study.id,
                    response_session_id=resp_session.id,
                    question_id=q_id,
                    option_id=option.id,
                    raw_code=option.raw_code,
                    numeric_value=option.numeric_value,
                    answered_at=resp_session.completed_at,
                )
            )

        for dim_code, _ in DIMENSIONS:
            tier = dim_tier_lists[dim_code][idx]
            base = TIER_BASE[tier]
            for q_code in build.scored_by_construct[dim_code]:
                q_id = q_id_by_code[q_code]
                direction = build.item_direction[q_code]
                raw_code = raw_code_for_target(direction, base)
                option = options_by_question[q_id][raw_code]
                responses.append(
                    Response(
                        study_id=study.id,
                        response_session_id=resp_session.id,
                        question_id=q_id,
                        option_id=option.id,
                        raw_code=option.raw_code,
                        numeric_value=option.numeric_value,
                        answered_at=resp_session.completed_at,
                    )
                )
    session.add_all(responses)
    session.add_all(session_units)
    await session.commit()

    # Una única corrida canónica alimenta resultados generales y por unidad.
    _, summary = await run_canonical_scoring(session, study.id)
    print(f"[{DEMO_CODE_SHORT}] scoring canónico: {summary.model_dump()}")

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
        logistic_outcome_code="RELACION_LABORAL",
        logistic_predictor_codes=["D1", "D5"],
    )

    return {"project_id": project.id, "study_id": study.id, "survey_id": survey.id}


async def seed_plan_and_bsc_short(session: AsyncSession, study: Study) -> None:
    d1 = (
        await session.execute(select(Construct).where(Construct.instrument_version_id == SHORT_VERSION_ID, Construct.code == "D1"))
    ).scalar_one()
    d5 = (
        await session.execute(select(Construct).where(Construct.instrument_version_id == SHORT_VERSION_ID, Construct.code == "D5"))
    ).scalar_one()

    plan = ActionPlan(study_id=study.id, name="Plan preventivo — SYN-C20-2026 (demo)", status="ACTIVE")
    session.add(plan)
    await session.flush()

    items = [
        ActionPlanItem(
            action_plan_id=plan.id,
            construct_id=d1.id,
            title="D1 — riesgo elevado (demo)",
            finding="Se observó una mayor proporción de casos en el nivel desfavorable de D1 (60%, sintético).",
            action_description="Rebalancear cargas semanales y revisar la planificación de tareas del área más afectada.",
            responsible_label="Jefatura de Operaciones",
            priority=1,
            due_date=date(2026, 7, 19),
            status="IN_PROGRESS",
        ),
        ActionPlanItem(
            action_plan_id=plan.id,
            construct_id=d5.id,
            title="D5 — compensaciones (demo)",
            finding="La distribución sugiere revisar percepción de compensaciones en el nivel desfavorable (55%, sintético).",
            action_description="Sesión informativa sobre política de compensaciones y canal de consultas.",
            responsible_label="Jefatura de Administración",
            priority=2,
            due_date=date(2026, 5, 30),
            status="PENDING",
        ),
        ActionPlanItem(
            action_plan_id=plan.id,
            construct_id=d1.id,
            title="Pausas activas (demo)",
            finding="Debe contrastarse con observación directa antes de concluir causalidad.",
            action_description="Implementar pausas activas guiadas en turnos de Operaciones.",
            responsible_label="SST y RR. HH.",
            priority=3,
            due_date=date(2026, 8, 15),
            status="DONE",
        ),
        ActionPlanItem(
            action_plan_id=plan.id,
            construct_id=None,
            title="Difusión de resultados colectivos (demo)",
            finding=None,
            action_description="Comunicar resultados agregados al comité de SST, respetando n>=5.",
            responsible_label="Comité SST",
            priority=4,
            due_date=date(2026, 9, 30),
            status="PENDING",
        ),
    ]
    session.add_all(items)
    await session.flush()

    kpi = Kpi(
        action_plan_item_id=items[0].id,
        study_id=study.id,
        code="KPI-TAREAS-VENCIDAS",
        name="% de tareas vencidas (demo)",
        description="Indicador analítico Colmena — no forma parte del método oficial CENSOPAS.",
        formula="tareas_vencidas / tareas_totales * 100",
        unit="%",
        baseline_value=32.0,
        target_value=25.6,
        frequency="MENSUAL",
    )
    session.add(kpi)
    await session.flush()
    session.add_all(
        [
            KpiMeasurement(kpi_id=kpi.id, measured_at=datetime(2026, 6, 30, tzinfo=UTC), numeric_value=32.0, status="LINEA_BASE"),
            KpiMeasurement(kpi_id=kpi.id, measured_at=datetime(2026, 7, 31, tzinfo=UTC), numeric_value=28.5, status="EN_PROGRESO"),
        ]
    )
    await session.commit()


# --------------------------------------------------------------------------
# DEMO B — SYN-M200-2026 (versión media, 200/186/180)
# --------------------------------------------------------------------------

AREA_TARGETS_MEDIUM: dict[str, dict[str, int]] = {
    # nombre_area: {tamaño, % desfavorable por dimensión D1..D6}
    "Operaciones": {"n": 55, "D1": 80, "D2": 26, "D3": 0, "D4": 14, "D5": 28, "D6": 4},
    "Mantenimiento": {"n": 38, "D1": 63, "D2": 14, "D3": 0, "D4": 23, "D5": 23, "D6": 0},
    "Administración": {"n": 33, "D1": 25, "D2": 10, "D3": 5, "D4": 10, "D5": 15, "D6": 5},
    "Logística": {"n": 24, "D1": 36, "D2": 0, "D3": 0, "D4": 16, "D5": 20, "D6": 0},
    "Comercial": {"n": 21, "D1": 45, "D2": 20, "D3": 10, "D4": 20, "D5": 25, "D6": 10},
    "SST y RR. HH.": {"n": 4, "D1": 20, "D2": 5, "D3": 0, "D4": 5, "D5": 10, "D6": 0},  # fixture n<5 (harness §78)
    "Proyecto Piloto": {"n": 5, "D1": 40, "D2": 20, "D3": 20, "D4": 20, "D5": 20, "D6": 40},  # fixture n=5 (harness §79/§80)
}
assert sum(v["n"] for v in AREA_TARGETS_MEDIUM.values()) == 180


def area_dimension_tiers(area: str, dim_code: str, rng: random.Random) -> list[str]:
    spec = AREA_TARGETS_MEDIUM[area]
    n = spec["n"]
    desf_pct = spec[dim_code]
    n_desf = round(n * desf_pct / 100)
    remaining = n - n_desf
    n_fav = remaining // 2
    n_int = remaining - n_fav
    counts = {"FAV": n_fav, "INT": n_int, "DESF": n_desf}
    return pick_tier_list(counts, rng)


async def seed_demo_medium(session: AsyncSession, owner: User, build: ManifestBuild) -> dict:
    period_start = date(2026, 5, 4)
    period_end = date(2026, 7, 24)
    rng = random.Random(202)

    project, survey = await create_base_project(
        session,
        owner,
        name="Industrias del Sur S.A. — DEMO",
        demo_code=DEMO_CODE_MEDIUM,
        version_id=MEDIUM_VERSION_ID,
        version_kind="MEDIUM",
        period_start=period_start,
        period_end=period_end,
    )
    exo_vars = await register_exogenous_variables(
        session, project.id, MEDIUM_VERSION_ID, build.profile_question_codes
    )

    study_service = StudyService(session)
    study = await study_service.create(
        project.id,
        StudyCreate(
            survey_id=survey.id,
            name="Aplicación CENSOPAS versión media 2026 — Industrias del Sur (demo)",
            study_type="CENSO",
            start_at=datetime(period_start.year, period_start.month, period_start.day, tzinfo=UTC),
            end_at=datetime(period_end.year, period_end.month, period_end.day, 23, 59, tzinfo=UTC),
            min_publishable_n=5,
            settings={"demo": True, "demo_code": DEMO_CODE_MEDIUM},
            requires_invitation=True,
        ),
    )

    area_units = await setup_area_units(session, study.id, {a: v["n"] for a, v in AREA_TARGETS_MEDIUM.items()})

    barem = await import_reference_barem(session, MEDIUM_VERSION_ID, "Baremo referencia demo — CENSOPAS media")
    await study_service.update(study.id, StudyUpdate(barem_id=barem.id))
    project.metadata_ = {**(project.metadata_ or {}), "barem_id": barem.id}
    await session.commit()
    study = await study_service.open(study.id)

    # Convocados=200: 186 consumidas (recibidos), 14 sin consumir (no respondieron), harness §28/§37.
    invitations = []
    for i in range(200):
        sent = random_datetime(rng, period_start, period_end)
        if i < 186:
            invitations.append(
                StudyInvitation(
                    study_id=study.id,
                    access_token_hash=f"demo-consumed-{DEMO_CODE_MEDIUM}-{i}",
                    status="CONSUMED",
                    sent_at=sent,
                    consumed_at=sent + timedelta(minutes=rng.randint(5, 240)),
                )
            )
        else:
            invitations.append(
                StudyInvitation(
                    study_id=study.id,
                    access_token_hash=f"demo-pending-{DEMO_CODE_MEDIUM}-{i}",
                    status=rng.choice(["SENT", "EXPIRED"]),
                    sent_at=sent,
                )
            )
    session.add_all(invitations)
    await session.commit()

    q_id_by_code: dict[str, int] = {}
    stmt = select(Question).where(Question.instrument_version_id == MEDIUM_VERSION_ID)
    for q in (await session.execute(stmt)).scalars().all():
        q_id_by_code[q.code] = q.id
    options_by_question = await load_question_options(session, MEDIUM_VERSION_ID)

    # -- 180 sesiones válidas, repartidas por área --------------------------
    person_specs: list[dict] = []
    for area, spec in AREA_TARGETS_MEDIUM.items():
        n = spec["n"]
        tiers_by_dim = {dim: area_dimension_tiers(area, dim, random.Random(hash((area, dim)) & 0xFFFF)) for dim, _ in DIMENSIONS}
        for i in range(n):
            person_specs.append(
                {
                    "area": area,
                    "dim_tier": {dim: tiers_by_dim[dim][i] for dim, _ in DIMENSIONS},
                }
            )
    rng.shuffle(person_specs)

    # Fixture de empate (harness §80): forzar D6 = FAV,FAV,INT,INT,DESF en Proyecto Piloto.
    piloto = [p for p in person_specs if p["area"] == "Proyecto Piloto"]
    for p, tier in zip(piloto, ["FAV", "FAV", "INT", "INT", "DESF"]):
        p["dim_tier"]["D6"] = tier

    sexo_cycle = ["Mujer", "Hombre"]
    edad_cycle = ["<31", "31-45", ">45"]

    valid_sessions: list[ResponseSession] = []
    for idx, spec in enumerate(person_specs):
        started = random_datetime(rng, period_start, period_end)
        completed = started + timedelta(minutes=rng.randint(18, 34))
        valid_sessions.append(
            ResponseSession(
                study_id=study.id,
                status="COMPLETED",
                validation_status="VALID",
                started_at=started,
                completed_at=completed,
                duration_seconds=int((completed - started).total_seconds()),
                completion_pct=round(rng.uniform(92.0, 100.0), 2),
                metadata_={"demo": True, "seed_version": SEED_VERSION, "area": spec["area"]},
            )
        )
    session.add_all(valid_sessions)
    await session.flush()

    responses: list[Response] = []
    session_units: list[ResponseSessionUnit] = []
    for idx, (resp_session, spec) in enumerate(zip(valid_sessions, person_specs)):
        unit = area_units[spec["area"]]
        session_units.append(ResponseSessionUnit(response_session_id=resp_session.id, study_unit_id=unit.id))

        profile_values = {
            "SEXO": sexo_cycle[idx % 2],
            "EDAD": edad_cycle[idx % 3],
            "AREA": spec["area"],
            "PUESTO": rng.choice(["Operativo", "Administrativo", "Supervisión"]),
            "NIVEL_INSTRUCCION": rng.choice(["Secundaria", "Técnica", "Universitaria"]),
            "TIEMPO_PUESTO": rng.choice(["<1 año", "1-3 años", ">3 años"]),
            "RELACION_LABORAL": rng.choice(["Planilla", "Locación de servicios"]),
            "TURNO": rng.choices(["Diurno", "Rotativo"], weights=[114, 66])[0],
            "SEDE": rng.choice(["Lima", "Operación Sur", "Operación Centro"]),
            "CONTRATO": rng.choices(["Indefinido", "Plazo fijo"], weights=[120, 60])[0],
            "REMUNERACION_RANGO": rng.choice(["< S/1500", "S/1500 - S/3000", "> S/3000"]),
        }
        for field_code, label in profile_values.items():
            q_code = build.profile_question_codes[field_code]
            q_id = q_id_by_code[q_code]
            spec_field = next(s for s in PROFILE_FIELDS if s["code"] == field_code)
            option = options_by_question[q_id][str(spec_field["labels"].index(label) + 1)]
            responses.append(
                Response(
                    study_id=study.id,
                    response_session_id=resp_session.id,
                    question_id=q_id,
                    option_id=option.id,
                    raw_code=option.raw_code,
                    numeric_value=option.numeric_value,
                    answered_at=resp_session.completed_at,
                )
            )

        for sub_code, _, dim_code in SUBDIMENSIONS:
            tier = spec["dim_tier"][dim_code]
            # jitter suave a nivel de subdimensión (±1 nivel, 20% de probabilidad) para variedad de ranking (§40).
            if rng.random() < 0.2:
                order = ["FAV", "INT", "DESF"]
                pos = order.index(tier)
                pos = max(0, min(2, pos + rng.choice([-1, 1])))
                tier = order[pos]
            base = TIER_BASE[tier]
            for q_code in build.scored_by_construct[sub_code]:
                q_id = q_id_by_code[q_code]
                direction = build.item_direction[q_code]
                raw_code = raw_code_for_target(direction, base)
                option = options_by_question[q_id][raw_code]
                responses.append(
                    Response(
                        study_id=study.id,
                        response_session_id=resp_session.id,
                        question_id=q_id,
                        option_id=option.id,
                        raw_code=option.raw_code,
                        numeric_value=option.numeric_value,
                        answered_at=resp_session.completed_at,
                    )
                )

    session.add_all(responses)
    session.add_all(session_units)
    await session.commit()

    # Respuestas de los módulos complementarios (una sola consulta, reutilizada para las 180 sesiones).
    comp_questions = (
        (
            await session.execute(
                select(Question).where(
                    Question.instrument_version_id == MEDIUM_VERSION_ID,
                    Question.is_scored.is_(False),
                    Question.research_role.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    comp_responses: list[Response] = []
    for resp_session in valid_sessions:
        for q in comp_questions:
            opts = options_by_question.get(q.id, {})
            if not opts:
                continue
            raw_code = str(rng.randint(2, 5))
            option = opts.get(raw_code) or next(iter(opts.values()))
            comp_responses.append(
                Response(
                    study_id=study.id,
                    response_session_id=resp_session.id,
                    question_id=q.id,
                    option_id=option.id,
                    raw_code=option.raw_code,
                    numeric_value=option.numeric_value,
                    answered_at=resp_session.completed_at,
                )
            )
    session.add_all(comp_responses)
    await session.commit()

    # -- 6 sesiones excluidas, casos de QA deliberados (harness §29) --------
    excluded_specs = [
        {"reason": "Cuestionario incompleto: sólo se respondió el 45% de los ítems.", "pct": 45.0, "answer_frac": 0.45},
        {"reason": "Cuestionario incompleto: abandonado tras el bloque de perfil (52%).", "pct": 52.0, "answer_frac": 0.52},
        {
            "reason": "Código fuera de catálogo detectado en un ítem psicosocial; sesión excluida para auditoría.",
            "pct": 98.0,
            "answer_frac": 0.98,
            "meta": {"qa_case": "raw_code_invalido_detectado"},
        },
        {
            "reason": "Sesión marcada como posible duplicado de otro token dentro de la misma ventana horaria.",
            "pct": 100.0,
            "answer_frac": 1.0,
            "meta": {"qa_case": "duplicate_pattern"},
        },
        {
            "reason": "Duración de sesión por debajo del mínimo plausible para 112 ítems (respuesta extremadamente rápida).",
            "pct": 100.0,
            "answer_frac": 1.0,
            "fast": True,
        },
        {
            "reason": "Patrón de respuesta lineal detectado (misma opción marcada en todos los ítems psicosociales).",
            "pct": 100.0,
            "answer_frac": 1.0,
            "meta": {"qa_case": "linear_pattern"},
            "linear": True,
        },
    ]
    excluded_sessions: list[ResponseSession] = []
    for i, spec in enumerate(excluded_specs):
        started = random_datetime(rng, period_start, period_end)
        duration = 40 if spec.get("fast") else rng.randint(18, 34) * 60
        completed = started + timedelta(seconds=duration)
        excluded_sessions.append(
            ResponseSession(
                study_id=study.id,
                status="COMPLETED",
                validation_status="EXCLUDED",
                exclusion_reason=spec["reason"],
                started_at=started,
                completed_at=completed,
                duration_seconds=duration,
                completion_pct=spec["pct"],
                metadata_={"demo": True, "seed_version": SEED_VERSION, **spec.get("meta", {})},
            )
        )
    session.add_all(excluded_sessions)
    await session.flush()

    excluded_responses: list[Response] = []
    all_scored_codes = [code for codes in build.scored_by_construct.values() for code in codes]
    for resp_session, spec in zip(excluded_sessions, excluded_specs):
        answer_n = int(len(all_scored_codes) * spec["answer_frac"])
        codes_to_answer = all_scored_codes[:answer_n]
        for q_code in codes_to_answer:
            q_id = q_id_by_code[q_code]
            direction = build.item_direction[q_code]
            base = 5 if spec.get("linear") else RNG.choice([1, 2, 3, 4, 5])
            raw_code = raw_code_for_target(direction, base)
            option = options_by_question[q_id][raw_code]
            excluded_responses.append(
                Response(
                    study_id=study.id,
                    response_session_id=resp_session.id,
                    question_id=q_id,
                    option_id=option.id,
                    raw_code=option.raw_code,
                    numeric_value=option.numeric_value,
                    answered_at=resp_session.completed_at,
                )
            )
    session.add_all(excluded_responses)
    await session.commit()

    print(
        f"[{DEMO_CODE_MEDIUM}] sesiones válidas={len(valid_sessions)} excluidas={len(excluded_sessions)} "
        f"(recibidos={len(valid_sessions) + len(excluded_sessions)}, convocados=200)"
    )

    _, summary = await run_canonical_scoring(session, study.id)
    print(f"[{DEMO_CODE_MEDIUM}] scoring canónico: {summary.model_dump()}")

    await seed_plan_and_bsc_medium(session, study)
    await seed_analytics_exports_reports(
        session,
        owner,
        project,
        study,
        version_id=MEDIUM_VERSION_ID,
        exo_vars=exo_vars,
        construct_codes=[code for code, _, _ in SUBDIMENSIONS],
        compare_pairs=[("S1", "TURNO"), ("S19", "CONTRATO"), ("S1", "AREA")],
        spearman_exo_codes=["EDAD"],
        cluster_codes=["S1", "S2", "S17", "S19"],
        logistic_outcome_code="RELACION_LABORAL",
        logistic_predictor_codes=["S17", "S18"],
    )

    return {"project_id": project.id, "study_id": study.id, "survey_id": survey.id}


async def seed_plan_and_bsc_medium(session: AsyncSession, study: Study) -> None:
    d1 = (
        await session.execute(select(Construct).where(Construct.instrument_version_id == MEDIUM_VERSION_ID, Construct.code == "D1"))
    ).scalar_one()
    s1 = (
        await session.execute(select(Construct).where(Construct.instrument_version_id == MEDIUM_VERSION_ID, Construct.code == "S1"))
    ).scalar_one()
    s17 = (
        await session.execute(select(Construct).where(Construct.instrument_version_id == MEDIUM_VERSION_ID, Construct.code == "S17"))
    ).scalar_one()

    plan = ActionPlan(study_id=study.id, name="Plan preventivo — SYN-M200-2026 (demo)", status="ACTIVE")
    session.add(plan)
    await session.flush()

    items = [
        ActionPlanItem(
            action_plan_id=plan.id,
            construct_id=d1.id,
            title="D1 — Operaciones, riesgo elevado (demo)",
            finding="Se observó una mayor proporción desfavorable en D1 concentrada en el área Operaciones (sintético).",
            action_description="Rebalancear cargas semanales en Operaciones y revisar turnos rotativos.",
            responsible_label="Jefatura de Operaciones",
            priority=1,
            due_date=date(2026, 8, 24),
            status="IN_PROGRESS",
        ),
        ActionPlanItem(
            action_plan_id=plan.id,
            construct_id=s1.id,
            title="S1 — Exigencias cuantitativas (demo)",
            finding="La subdimensión de mayor prioridad en el ranking desfavorable (sintético, ver §40).",
            action_description="Revisar dotación de personal y metas de producción por turno.",
            responsible_label="Jefatura de Operaciones",
            priority=2,
            due_date=date(2026, 9, 10),
            status="PENDING",
        ),
        ActionPlanItem(
            action_plan_id=plan.id,
            construct_id=s17.id,
            title="S17 — Inseguridad sobre el empleo (demo)",
            finding="Debe contrastarse con datos de rotación/contratos antes de concluir causalidad.",
            action_description="Sesión informativa sobre estabilidad contractual con RR. HH.",
            responsible_label="SST y RR. HH.",
            priority=3,
            due_date=date(2026, 6, 20),
            status="PENDING",
        ),
        ActionPlanItem(
            action_plan_id=plan.id,
            construct_id=None,
            title="Comunicación de resultados por sede (demo)",
            action_description="Difundir resultados agregados respetando n>=5 y supresión secundaria.",
            responsible_label="Comité SST",
            priority=4,
            due_date=date(2026, 10, 15),
            status="DONE",
        ),
    ]
    session.add_all(items)
    await session.flush()

    kpis = [
        Kpi(
            action_plan_item_id=items[0].id,
            study_id=study.id,
            code="KPI-COBERTURA-VALIDA",
            name="Cobertura válida (demo)",
            description="Indicador analítico Colmena — no forma parte del método oficial CENSOPAS.",
            formula="validos / convocados * 100",
            unit="%",
            baseline_value=85.0,
            target_value=90.0,
            frequency="POR_ESTUDIO",
        ),
        Kpi(
            action_plan_item_id=items[1].id,
            study_id=study.id,
            code="KPI-BSC",
            name="Índice BSC (demo)",
            description="Indicador analítico Colmena — no forma parte del método oficial CENSOPAS.",
            formula="promedio ponderado de objetivos BSC",
            unit="pts/100",
            baseline_value=62.0,
            target_value=75.0,
            frequency="TRIMESTRAL",
        ),
    ]
    session.add_all(kpis)
    await session.flush()
    measurements = []
    base_date = date(2026, 5, 15)
    for kpi, values in zip(kpis, [[85.0, 88.0, 90.0], [62.0, 68.0, 70.0]]):
        for i, value in enumerate(values):
            measurements.append(
                KpiMeasurement(
                    kpi_id=kpi.id,
                    measured_at=datetime(base_date.year, base_date.month, min(base_date.day + i * 30, 28), tzinfo=UTC),
                    numeric_value=value,
                    status="EN_PROGRESO" if i < len(values) - 1 else "ACTUAL",
                )
            )
    session.add_all(measurements)
    await session.commit()


# --------------------------------------------------------------------------
# Analítica avanzada / premium, exportaciones y reportes (harness §51-73)
# --------------------------------------------------------------------------

async def _get_construct(session: AsyncSession, version_id: int, code: str) -> Construct:
    stmt = select(Construct).where(
        Construct.instrument_version_id == version_id, Construct.code == code
    )
    return (await session.execute(stmt)).scalar_one()


async def seed_analytics_exports_reports(
    session: AsyncSession,
    owner: User,
    project: Project,
    study: Study,
    *,
    version_id: int,
    exo_vars: dict[str, Variable],
    construct_codes: list[str],
    compare_pairs: list[tuple[str, str]],
    spearman_exo_codes: list[str],
    cluster_codes: list[str],
    logistic_outcome_code: str | None,
    logistic_predictor_codes: list[str],
) -> None:
    """Ejercita el resto de la Fase 7/9 (inferencial, correlaciones, clustering,
    regresión), exportaciones y reporte para que Analítica/Reportes/Exportaciones
    tengan datos reales persistidos, no pantallas vacías (harness §92-96)."""
    advanced = AdvancedAnalysisService(session)
    basic = AnalysisService(session)
    constructs_by_code = {
        code: await _get_construct(session, version_id, code) for code in construct_codes
    }

    # -- Confiabilidad por constructo (Cronbach/Omega, harness §54-55) ------
    for code, construct in constructs_by_code.items():
        try:
            await basic.run_reliability(study.id, ReliabilityRequest(construct_id=construct.id))
        except Exception as exc:  # noqa: BLE001 - demo: seguir con el resto si un constructo falla
            print(f"  [reliability] {code}: {exc}")

    # -- Normalidad (complementaria, harness §54) ---------------------------
    try:
        await advanced.run_normality(
            study.id,
            NormalityRequest(construct_ids=[c.id for c in constructs_by_code.values()]),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  [normality] {exc}")

    # -- Matriz de correlaciones Spearman + BH (harness §60-61) -------------
    try:
        await advanced.run_spearman_matrix(
            study.id,
            SpearmanMatrixRequest(
                construct_ids=[c.id for c in constructs_by_code.values()],
                exogenous_variable_ids=[
                    exo_vars[code].id for code in spearman_exo_codes if code in exo_vars
                ],
                include_points=False,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  [spearman] {exc}")

    # -- Comparación de grupos (Mann-Whitney/Kruskal-Wallis, harness §56-58) -
    for construct_code, group_code in compare_pairs:
        variable = exo_vars.get(group_code)
        if variable is None:
            continue
        try:
            response = await advanced.compare_construct_groups(
                study.id,
                ConstructCompareGroupsRequest(
                    construct_id=constructs_by_code[construct_code].id,
                    group_variable_id=variable.id,
                ),
            )
            print(
                f"  [compare_groups] {construct_code} x {group_code}: "
                f"method={response.method} suppressed={response.suppressed}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  [compare_groups] {construct_code} x {group_code}: {exc}")

    # -- Patrones ocultos: k-means sobre puntajes de constructo (harness §62-63)
    try:
        cluster_vars = [
            await register_construct_score_variable(
                session, project.id, version_id, constructs_by_code[code]
            )
            for code in cluster_codes
        ]
        await basic.run_kmeans(
            study.id, KMeansRequest(variable_ids=[v.id for v in cluster_vars], k=3)
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  [kmeans] {exc}")

    # -- Regresión logística (harness §64-65) -------------------------------
    if logistic_outcome_code and logistic_outcome_code in exo_vars:
        try:
            predictor_vars = [
                await register_construct_score_variable(
                    session, project.id, version_id, constructs_by_code[code]
                )
                for code in logistic_predictor_codes
            ]
            await basic.run_logistic_regression(
                study.id,
                LogisticRegressionRequest(
                    outcome_variable_id=exo_vars[logistic_outcome_code].id,
                    predictor_variable_ids=[v.id for v in predictor_vars],
                ),
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  [logistic_regression] {exc}")

    # -- Exportaciones (harness §72-73) -------------------------------------
    export_service = ExportService(session)
    for export_type, shape in (("CSV", "LONG"), ("XLSX", "WIDE"), ("JSON", "WIDE")):
        try:
            export = await export_service.create_export(
                study.id,
                ExportCreate(
                    export_type=export_type,
                    dataset_shape=shape,
                    requested_by_user_id=owner.id,
                    filters={},
                ),
            )
            print(f"  [export] {export_type}/{shape}: status={export.status} rows={export.row_count}")
        except Exception as exc:  # noqa: BLE001
            print(f"  [export] {export_type}/{shape}: {exc}")

    # -- Reporte (harness §49-50) -------------------------------------------
    report_service = ReportService(session)
    try:
        report_run = await report_service.generate(
            study.id,
            ReportRunCreate(
                output_format="DOCX",
                requested_by_user_id=owner.id,
                report_mode="PROVISIONAL",
                sections=[],
            ),
        )
        print(f"  [report] status={report_run.status} hash={report_run.data_hash}")
    except Exception as exc:  # noqa: BLE001
        print(f"  [report] {exc}")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

async def get_owner(session: AsyncSession) -> User:
    stmt = select(User).where(User.email == OWNER_EMAIL)
    owner = (await session.execute(stmt)).scalar_one_or_none()
    if owner is None:
        raise RuntimeError(
            f"No existe el usuario {OWNER_EMAIL} en la base de datos; créelo primero (registro normal)."
        )
    return owner


async def run() -> dict:
    async with AsyncSessionLocal() as session:
        owner = await get_owner(session)
        print(f"[owner] {owner.email} (id={owner.id})")

        await reset_demo(session)

        short_build = build_short_manifest()
        await import_instrument(session, SHORT_VERSION_ID, short_build)
        medium_build = build_medium_manifest()
        await import_instrument(session, MEDIUM_VERSION_ID, medium_build)

        # official_equivalence_enabled=false explícito en el instrumento compartido (harness §20).
        instrument = await session.get(Instrument, 1)
        instrument.metadata_ = {**(instrument.metadata_ or {}), "official_equivalence_enabled": False}
        await session.commit()

        demo_a = await seed_demo_short(session, owner, short_build)
        demo_b = await seed_demo_medium(session, owner, medium_build)

        summary = {
            DEMO_CODE_SHORT: demo_a,
            DEMO_CODE_MEDIUM: demo_b,
            "owner_email": OWNER_EMAIL,
            "seed_version": SEED_VERSION,
        }
        return summary


async def main() -> None:
    try:
        result = await run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
