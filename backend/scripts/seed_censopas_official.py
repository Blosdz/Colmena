"""Seed del contenido OFICIAL y protegido de CENSOPAS-COPSOQ — versiones corta y media.

A diferencia de `seed_censopas_demo.py` (que genera texto SINTÉTICO y reconstruye
en cada corrida las versiones de instrumento compartidas `id=1`/`id=2` sembradas
por la migración `0001_colmena_schema.sql`), este script importa el banco de
ítems REAL del Manual técnico CENSOPAS-COPSOQ (dimensiones, subdimensiones,
preguntas, catálogos de respuesta y dirección de puntuación) desde
`censopas_seed_complete.json` (raíz del repo) y lo publica como versiones de
instrumento nuevas y protegidas — una por cada versión canónica del JSON
(`SHORT`, `MEDIUM`). El propio JSON aclara que "versión larga" es un alias
coloquial de la versión media y que no debe crearse una tercera versión
metodológica (`version_aliases`), así que este script tampoco lo hace.

Se usa deliberadamente una `instrument_version` propia por versión
(`version_code = "SHORT-OFICIAL"` / `"MEDIUM-OFICIAL"`), NUNCA las filas
`id=1`/`id=2`: esas dos son reconstruidas y borradas en cada ejecución de
`seed_censopas_demo.py` (ver su `reset_demo()`), así que sembrar el contenido
oficial ahí lo dejaría expuesto a ser borrado por el siguiente
`python scripts/seed_censopas_demo.py` que alguien ejecute.

Mecanismo (reutiliza el motor ya existente, no reescribe nada):
    CensopasManifest (construido desde el JSON)
        -> CensopasScoringService.import_manifest()   (valida hash + estructura,
           persiste OptionSet/Question/Construct/ScoringRule transaccionalmente)
        -> InstrumentService.update_version(status="ACTIVE")

Al quedar `status="ACTIVE"` en un instrumento `is_system=True`,
`InstrumentEditPolicy` congela automáticamente la versión: ya no admite más
`import-manifest` ni edición estructural vía el Constructor genérico (ver
`app/services/instrument_edit_policy.py`). Esa es la protección de "núcleo
oficial" pedida — no hace falta código nuevo para el candado, solo poblar y
activar.

Idempotente por hash: puede ejecutarse en cada deploy sin duplicar datos ni
volver a escribir sobre una versión ya publicada. Si el contenido del JSON
cambia después de que una versión ya esté ACTIVA, el script se niega a
mutarla (una revisión del manual es una versión nueva, ej.
"MEDIUM-OFICIAL-V2", nunca una edición en caliente de la vigente).

Uso (desde backend/, con el venv de poetry activo):
    python scripts/seed_censopas_official.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models.instrument import Instrument, InstrumentVersion
from app.schemas.censopas import (
    CensopasManifest,
    CensopasManifestConstruct,
    CensopasManifestItemLink,
    CensopasManifestOption,
    CensopasManifestQuestion,
    CensopasManifestScale,
    CensopasManifestScoringRule,
)
from app.schemas.instruments import InstrumentVersionCreate, InstrumentVersionUpdate
from app.services.censopas_service import CensopasScoringService
from app.services.instrument_service import InstrumentService

INSTRUMENT_CODE = "CENSOPAS_COPSOQ"
SEED_JSON_PATH = Path(__file__).resolve().parents[2] / "censopas_seed_complete.json"

VersionKind = Literal["SHORT", "MEDIUM"]

# (version_kind, version_code, version_name, manifest_version_suffix)
VERSION_PLANS: list[tuple[VersionKind, str, str, str]] = [
    ("SHORT", "SHORT-OFICIAL", "Plan corto — CENSOPAS-COPSOQ (oficial)", "CORTA"),
    ("MEDIUM", "MEDIUM-OFICIAL", "Plan media — CENSOPAS-COPSOQ (oficial)", "MEDIA"),
]


def _load_seed_data() -> dict:
    with SEED_JSON_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _source_reference(data: dict, version_kind: VersionKind) -> str:
    source = data["source"]
    label = "versión corta" if version_kind == "SHORT" else "versión media"
    return f"{source['title']} ({source['edition']}) — {label}."


def _build_scales(data: dict, version_kind: VersionKind) -> dict[str, CensopasManifestScale]:
    scales: dict[str, CensopasManifestScale] = {}
    for catalog in data["catalogs"]:
        if catalog["version"] != version_kind.lower() or catalog["dynamic"]:
            continue
        scales[catalog["code"]] = CensopasManifestScale(
            code=catalog["code"],
            name=catalog["code"],
            options=[
                CensopasManifestOption(
                    raw_code=str(option["raw_code"]),
                    label=option["label"],
                    numeric_value=float(option["raw_code"]),
                    sort_order=index,
                )
                for index, option in enumerate(catalog["options"])
            ],
        )
    return scales


def build_manifest(data: dict, version_kind: VersionKind, manifest_version: str) -> CensopasManifest:
    scales = _build_scales(data, version_kind)
    version_questions = [q for q in data["questions"] if q["version"] == version_kind.lower()]
    version_questions.sort(key=lambda item: item["order"])

    questions: list[CensopasManifestQuestion] = []
    items_by_construct: dict[str, list[CensopasManifestItemLink]] = {
        dim["code"]: [] for dim in data["dimensions"]
    }
    if version_kind == "MEDIUM":
        items_by_construct.update({sub["code"]: [] for sub in data["subdimensions"]})

    scoring_rules: list[CensopasManifestScoringRule] = []

    for entry in version_questions:
        is_free_text = bool(entry["dynamic_catalog"])
        questions.append(
            CensopasManifestQuestion(
                code=entry["code"],
                source_code=entry["source_code"],
                question_text=entry["question"],
                question_type="TEXT" if is_free_text else entry["suggested_question_type"],
                is_scored=entry["is_scored"],
                research_role="ENDOGENOUS" if entry["is_scored"] else "EXOGENOUS",
                option_set_code=None if is_free_text else entry["catalog"],
                is_required=True,
                sort_order=entry["order"],
                category=entry["category_code"],
                metadata={"dynamic_catalog": is_free_text},
            )
        )

        if not entry["is_scored"]:
            continue

        # La versión SHORT sólo publica constructos de dimensión (más abajo,
        # `constructs` no agrega subdimensiones salvo en MEDIUM) — aunque el
        # JSON trae `subdimension_code` también para preguntas SHORT, un
        # ítem SHORT debe enlazarse siempre a su dimensión o
        # `items_by_construct[subdim_code]` revienta con KeyError.
        construct_code = (
            entry["dimension_code"]
            if version_kind == "SHORT"
            else entry["subdimension_code"] or entry["dimension_code"]
        )
        links = items_by_construct[construct_code]
        links.append(
            CensopasManifestItemLink(
                question_code=entry["code"],
                item_role="SCORED",
                scoring_direction=entry["provisional_scoring_direction"],
                sort_order=len(links) + 1,
            )
        )
        # El motor (analytics/censopas/scoring.py::derive_item_values) invierte
        # según scoring_direction del ConstructItem — el risk_map en sí es
        # siempre el mapa identidad 1..5, nunca se hornea la inversión aquí.
        scoring_rules.append(
            CensopasManifestScoringRule(
                question_code=entry["code"],
                risk_map={"1": 1.0, "2": 2.0, "3": 3.0, "4": 4.0, "5": 5.0},
                source_reference=_source_reference(data, version_kind),
                rule_version=manifest_version,
            )
        )

    root_code = f"CENSOPAS_{version_kind}_ROOT"
    constructs: list[CensopasManifestConstruct] = [
        CensopasManifestConstruct(
            code=root_code,
            name=f"CENSOPAS-COPSOQ — {'Versión corta' if version_kind == 'SHORT' else 'Versión media'} (oficial)",
            construct_type="VARIABLE",
            sort_order=0,
        )
    ]
    for dim in data["dimensions"]:
        constructs.append(
            CensopasManifestConstruct(
                code=dim["code"],
                name=dim["name"],
                construct_type="DIMENSION",
                parent_code=root_code,
                sort_order=dim["sort_order"],
                items=items_by_construct[dim["code"]],
            )
        )
    if version_kind == "MEDIUM":
        for sub in data["subdimensions"]:
            constructs.append(
                CensopasManifestConstruct(
                    code=sub["code"],
                    name=sub["name"],
                    construct_type="SUBDIMENSION",
                    parent_code=sub["dimension_code"],
                    sort_order=sub["sort_order"],
                    items=items_by_construct[sub["code"]],
                )
            )

    return CensopasManifest(
        version_kind=version_kind,
        manifest_version=manifest_version,
        source_reference=_source_reference(data, version_kind),
        scales=list(scales.values()),
        questions=questions,
        constructs=constructs,
        scoring_rules=scoring_rules,
    )


async def get_or_create_official_version(
    session: AsyncSession, version_code: str, version_name: str, source_reference: str
) -> InstrumentVersion:
    instrument = (
        (
            await session.execute(
                select(Instrument).where(Instrument.code == INSTRUMENT_CODE)
            )
        )
        .scalars()
        .first()
    )
    if instrument is None:
        raise RuntimeError(
            f"No existe Instrument(code='{INSTRUMENT_CODE}') — falta aplicar la migración "
            "0001_colmena_schema.sql (siembra el instrumento CENSOPAS-COPSOQ base)."
        )

    version = (
        (
            await session.execute(
                select(InstrumentVersion).where(
                    InstrumentVersion.instrument_id == instrument.id,
                    InstrumentVersion.version_code == version_code,
                )
            )
        )
        .scalars()
        .first()
    )
    if version is not None:
        return version

    service = InstrumentService(session)
    version = await service.create_version(
        instrument.id,
        InstrumentVersionCreate(
            version_code=version_code,
            version_name=version_name,
            edition="Manual técnico CENSOPAS-COPSOQ",
            status="DRAFT",
            source_reference=source_reference,
            config={},
        ),
    )
    print(f"[version] creada instrument_version id={version.id} version_code={version_code}")
    return version


async def run_one(
    session: AsyncSession,
    data: dict,
    version_kind: VersionKind,
    version_code: str,
    version_name: str,
    manifest_version: str,
) -> dict:
    source_reference = _source_reference(data, version_kind)
    version = await get_or_create_official_version(session, version_code, version_name, source_reference)
    manifest = build_manifest(data, version_kind, manifest_version)

    censopas_service = CensopasScoringService(session)
    validation = censopas_service.validate_manifest_payload(manifest)
    if not validation.valid:
        raise RuntimeError(
            f"El manifiesto oficial de {version_code} no pasó su propia validación: "
            f"{validation.errors}"
        )

    existing_hash = (version.config or {}).get("manifest_hash")

    if existing_hash == validation.calculated_hash:
        if version.status in ("ACTIVE", "LOCKED"):
            print(
                f"[skip] instrument_version id={version.id} ({version_code}) ya sembrado y "
                f"activo (hash={existing_hash[:12]}...)"
            )
            readiness = await censopas_service.get_readiness(version.id)
            return {"instrument_version_id": version.id, "version_code": version_code, "status": "SKIPPED", "readiness": readiness}
        print(f"[recover] contenido ya importado pero versión no activada — activando id={version.id}")
    elif existing_hash is not None:
        raise RuntimeError(
            f"instrument_version id={version.id} ('{version_code}') ya fue publicado con un "
            f"manifiesto distinto (hash actual={existing_hash[:12]}..., nuevo={validation.calculated_hash[:12]}...). "
            "No se muta una versión oficial ya publicada: si el contenido cambió (revisión del "
            f"manual o del JSON fuente), cree un nuevo version_code (ej. '{version_code}-V2') "
            "en vez de editar esta."
        )
    else:
        print(f"[import] importando manifiesto oficial en instrument_version id={version.id} ({version_code})")
        import_result = await censopas_service.import_manifest(version.id, manifest)
        print(
            f"[import] ok: {import_result.imported} — "
            f"ready_for_scoring={import_result.readiness.ready_for_scoring} "
            f"errors={import_result.readiness.errors}"
        )

    instrument_service = InstrumentService(session)
    version = await instrument_service.update_version(
        version.id, InstrumentVersionUpdate(status="ACTIVE")
    )
    print(f"[activate] instrument_version id={version.id} status={version.status} (protegido por InstrumentEditPolicy)")

    readiness = await censopas_service.get_readiness(version.id)
    return {
        "instrument_version_id": version.id,
        "version_code": version_code,
        "status": version.status,
        "readiness": readiness,
    }


async def run() -> list[dict]:
    data = _load_seed_data()
    results = []
    async with AsyncSessionLocal() as session:
        for version_kind, version_code, version_name, suffix in VERSION_PLANS:
            manifest_version = f"CENSOPAS-{suffix}-2025-V1"
            result = await run_one(session, data, version_kind, version_code, version_name, manifest_version)
            results.append(result)
    return results


async def main() -> None:
    try:
        results = await run()
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
