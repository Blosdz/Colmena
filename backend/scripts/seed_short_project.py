"""Seed de UN proyecto corto (CENSOPAS-COPSOQ versión SHORT) para
`ammyt11@gmail.com`, tras un reset completo de la base de datos.

No reimplementa nada: reutiliza `reset_demo`, `build_short_manifest`,
`import_instrument` y `seed_demo_short` de `seed_demo_current.py` — el mismo
camino ya probado que arma el proyecto "Servicios Andinos S.A.C. — DEMO"
(20 respuestas válidas, plan preventivo + BSC, analítica y reportes). Solo
cambia el dueño y omite la versión MEDIUM (no se pidió).

Uso (desde backend/, con el venv activo):
    python scripts/seed_short_project.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.models.instrument import Instrument
from app.models.user import User
from scripts.seed_demo_current import (
    SHORT_VERSION_ID,
    SEED_VERSION,
    build_short_manifest,
    import_instrument,
    reset_demo,
    seed_demo_short,
)

OWNER_EMAIL = "ammyt11@gmail.com"


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

        await reset_demo(session)

        short_build = build_short_manifest()
        await import_instrument(session, SHORT_VERSION_ID, short_build)

        instrument = await session.get(Instrument, 1)
        instrument.metadata_ = {**(instrument.metadata_ or {}), "official_equivalence_enabled": False}
        await session.commit()

        demo = await seed_demo_short(session, owner, short_build)

        return {"short_project": demo, "owner_email": OWNER_EMAIL, "seed_version": SEED_VERSION}


async def main() -> None:
    try:
        result = await run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
