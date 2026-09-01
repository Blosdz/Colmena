"""Publica una nueva aplicación académica del formulario del proyecto 10.

El cuestionario conserva el contenido propio del caso de estudio. Del manual
CENSOPAS-COPSOQ toma las reglas de aplicación: anonimato, perfil separado,
codificación cruda 1..5, snapshot al abrir y baremo versionado. No presenta el
formulario académico como instrumento oficial CENSOPAS.
"""

from __future__ import annotations

import asyncio
import json

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal, engine
from app.models.project import Project
from app.models.study import Study
from app.models.survey import Survey, SurveySection
from app.schemas.studies import StudyCreate, StudyUpdate
from app.services.study_service import StudyService

PROJECT_ID = 10
SURVEY_ID = 3
BAREM_ID = 2
STUDY_NAME = "Aplicación pública 2026 — Metodologías y satisfacción"

METHODOLOGY = {
    "framework": "Adaptación académica con criterios de implementación CENSOPAS-COPSOQ",
    "official_censopas_instrument": False,
    "references": [
        "Manual técnico CENSOPAS-COPSOQ para Colmena",
        "Guía y modelos de reporte CENSOPAS-COPSOQ para Colmena",
    ],
    "response_scale": {
        "raw_codes": ["1", "2", "3", "4", "5"],
        "labels": [
            "Totalmente en desacuerdo",
            "En desacuerdo",
            "Ni de acuerdo ni en desacuerdo",
            "De acuerdo",
            "Totalmente de acuerdo",
        ],
        "note": "El código marcado se conserva sin sobrescribir y el puntaje se calcula por separado.",
    },
    "privacy": "Respuestas anónimas; edad y sexo se usan sólo para segmentación y no modifican el puntaje.",
    "reporting": "Resultados colectivos por variable y dimensión, con mínimo publicable de cinco respuestas.",
}


async def publish() -> dict:
    async with AsyncSessionLocal() as session:
        project = await session.get(Project, PROJECT_ID)
        survey_stmt = (
            select(Survey)
            .where(Survey.id == SURVEY_ID, Survey.project_id == PROJECT_ID)
            .options(selectinload(Survey.sections))
        )
        survey = (await session.execute(survey_stmt)).scalar_one_or_none()
        if project is None or survey is None:
            raise RuntimeError("No se encontró el proyecto 10 o su formulario 3.")

        survey.description = (
            "Encuesta anónima sobre metodologías de enseñanza y satisfacción estudiantil. "
            "Responde según tu experiencia durante el ciclo académico actual. La estructura de "
            "aplicación, trazabilidad y lectura colectiva sigue criterios documentados en el manual "
            "técnico CENSOPAS-COPSOQ para Colmena; no corresponde al cuestionario ocupacional oficial."
        )
        survey.status = "PUBLISHED"
        survey.settings = {**(survey.settings or {}), "methodology": METHODOLOGY}

        sections = {section.section_kind: section for section in survey.sections}
        profile = sections.get("EXOGENOUS")
        if profile:
            profile.title = "Perfil anónimo"
            profile.description = (
                "Selecciona el rango que te corresponde. Estos datos permiten comparar grupos de forma "
                "colectiva y no forman parte del puntaje."
            )
        instrument = sections.get("INSTRUMENT")
        if instrument:
            instrument.title = "Experiencia académica"
            instrument.description = (
                "Indica tu grado de acuerdo pensando en las clases de tu ciclo actual. Usa una sola "
                "respuesta por afirmación; no hay respuestas correctas o incorrectas."
            )

        project.metadata_ = {
            **(project.metadata_ or {}),
            "survey_methodology": METHODOLOGY,
        }
        await session.commit()

        existing_stmt = (
            select(Study)
            .where(
                Study.project_id == PROJECT_ID,
                Study.name == STUDY_NAME,
                Study.status.in_(("DRAFT", "OPEN")),
            )
            .order_by(Study.id.desc())
        )
        existing = (await session.execute(existing_stmt)).scalars().first()
        service = StudyService(session)

        if existing is None:
            study = await service.create(
                PROJECT_ID,
                StudyCreate(
                    survey_id=SURVEY_ID,
                    name=STUDY_NAME,
                    study_type="ACADEMIC",
                    min_publishable_n=5,
                    requires_invitation=False,
                    settings={
                        "publication_key": "project-10-censopas-guided-2026",
                        "methodology": METHODOLOGY,
                        "participant_context": "Estudiantes universitarios de pregrado",
                    },
                ),
            )
        else:
            study = existing

        if study.barem_id != BAREM_ID:
            study = await service.update(study.id, StudyUpdate(barem_id=BAREM_ID))
        if study.status == "DRAFT":
            study = await service.open(study.id)

        project = await session.get(Project, PROJECT_ID)
        project.metadata_ = {
            **(project.metadata_ or {}),
            "published_study_id": study.id,
            "published_study_public_id": str(study.public_id),
        }
        await session.commit()

        return {
            "project_id": PROJECT_ID,
            "survey_id": SURVEY_ID,
            "study_id": study.id,
            "public_id": str(study.public_id),
            "status": study.status,
            "questions": 14,
        }


async def main() -> None:
    try:
        print(json.dumps(await publish(), ensure_ascii=False))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
