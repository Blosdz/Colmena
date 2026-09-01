"""Autoridad única para el estado metodológico CENSOPAS (barem_status /
official_equivalence).

"Resultado oficial CENSOPAS" nunca puede mostrarse (ni en Resultados, ni en
Premium, ni en Reportes/Exportaciones) salvo que el baremo activo sea
`barem_type == "OFFICIAL"` **y** el instrumento tenga
`official_equivalence_enabled = True`. Esta regla vivía duplicada en
`censopas_service.apply_privacy`, `scoring_service.get_overview` y
`report_service.build_bundle`; cualquier consumidor nuevo debe usar las
funciones de este módulo en vez de reimplementar la condición.
"""

from __future__ import annotations

from app.models.censopas import Barem
from app.repositories.instruments import InstrumentRepository


async def resolve_official_equivalence_enabled(
    instrument_repo: InstrumentRepository, instrument_version_id: int | None
) -> bool:
    if instrument_version_id is None:
        return False
    version = await instrument_repo.get_version_with_instrument(instrument_version_id)
    if version is None:
        return False
    return bool(version.instrument.metadata_.get("official_equivalence_enabled", False))


def resolve_censopas_methodological_status(
    barem: Barem | None, official_equivalence_enabled: bool
) -> dict:
    barem_status = barem.metadata_.get("barem_type") if barem else None
    official_equivalence = bool(
        barem is not None and barem_status == "OFFICIAL" and official_equivalence_enabled
    )
    label = "Baremo oficial" if official_equivalence else "Baremo de referencia"
    return {
        "barem_status": barem_status,
        "official_equivalence": official_equivalence,
        "label": label,
    }
