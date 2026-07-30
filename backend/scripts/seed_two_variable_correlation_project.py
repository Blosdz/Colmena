#!/usr/bin/env python3
"""DEV TOOL — NOT A PRODUCTION FEATURE.

Creates a full demo project with two instrument-based variables (each with
two dimensions and four Likert items) plus simulated respondent data, so the
descriptives / reliability / normality / correlation stages can be exercised
end-to-end against a realistic two-variable correlational design instead of
an empty project.

The two variables are negatively correlated by construction (a classic
"stress vs. performance" correlational design), so the correlation matrix at
/api/v1/forms/{form_id}/correlations/project-variables should show a
moderate-to-strong negative Pearson r, and each dimension should show good
internal consistency (Cronbach's alpha) when checked at
/api/v1/forms/{form_id}/reliability/dimensions.

Usage:
    cd COLMENA/backend
    source venv/bin/activate  # or .venv, whichever this checkout uses
    python scripts/seed_two_variable_correlation_project.py --username johaba.jb --n 180

Rerunning creates another project (no dedup) — delete the old one from the
UI if you don't want duplicates. This must never be wired into any API
route, scheduled job, or app startup path — it is a one-off CLI helper for
local/dev environments only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.approach import Approach
from app.models.design_type import DesignType
from app.models.form import Form
from app.models.form_answer import FormAnswer
from app.models.form_dimension import FormDimension
from app.models.form_instrument import FormInstrument
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.models.form_response import FormResponse
from app.models.project import Project
from app.models.project_variable import ProjectVariable
from app.models.scale import Scale
from app.models.type_research import TypeResearch
from app.models.user import User

SEED_SOURCE = "dev_seed"
LIKERT_SCALE_ID = "sys_acuerdo_5"  # preset "Acuerdo · 5 puntos" (system-wide, project_id NULL)
LIKERT_LABELS = [
    "Totalmente en desacuerdo",
    "En desacuerdo",
    "Ni de acuerdo ni en desacuerdo",
    "De acuerdo",
    "Totalmente de acuerdo",
]

# Factor-model loadings: item -> dimension -> variable. Building the data as
# a sum of independent normals guarantees a valid (positive semi-definite)
# correlation structure, unlike hand-writing a target correlation matrix.
ITEM_LOADING = 0.75  # within-dimension item correlation ≈ ITEM_LOADING**2 ≈ 0.56 (alpha ≈ 0.84 @ 4 items)
DIMENSION_LOADING = 0.65  # same-variable cross-dimension correlation
CROSS_VARIABLE_FACTOR_CORRELATION = -0.95  # drives the two variables apart -> composite r ≈ -0.47

VARIABLES = [
    {
        "name": "Estrés Laboral",
        "code": "EL",
        "classification": "independent",
        "instrument_name": "Escala de Estrés Laboral",
        "acronym": "EEL",
        "dimensions": [
            {
                "name": "Sobrecarga Laboral",
                "code": "EL-SC",
                "items": [
                    "Siento que la cantidad de trabajo que debo realizar excede el tiempo disponible.",
                    "Debo atender demasiadas tareas al mismo tiempo durante mi jornada laboral.",
                    "Con frecuencia debo llevarme trabajo pendiente fuera de mi horario laboral.",
                    "El ritmo de trabajo que me exigen es difícil de sostener de manera constante.",
                ],
            },
            {
                "name": "Agotamiento Emocional",
                "code": "EL-AE",
                "items": [
                    "Al finalizar mi jornada laboral me siento emocionalmente agotado(a).",
                    "Me cuesta recuperar energía incluso después de descansar.",
                    "Siento que el trabajo ha disminuido mi tolerancia frente a los problemas cotidianos.",
                    "Me siento tenso(a) o irritable la mayor parte de mi jornada laboral.",
                ],
            },
        ],
    },
    {
        "name": "Desempeño Laboral",
        "code": "DL",
        "classification": "dependent",
        "instrument_name": "Escala de Desempeño Laboral",
        "acronym": "EDL",
        "dimensions": [
            {
                "name": "Desempeño de Tarea",
                "code": "DL-DT",
                "items": [
                    "Cumplo con los objetivos de mi puesto dentro de los plazos establecidos.",
                    "La calidad de mi trabajo cumple con los estándares que exige mi área.",
                    "Puedo priorizar correctamente mis tareas cuando tengo varias pendientes.",
                    "Utilizo eficientemente los recursos disponibles para completar mis funciones.",
                ],
            },
            {
                "name": "Compromiso Organizacional",
                "code": "DL-CO",
                "items": [
                    "Me siento comprometido(a) con los objetivos de la organización.",
                    "Estoy dispuesto(a) a hacer un esfuerzo adicional cuando la organización lo requiere.",
                    "Me identifico con los valores de la institución donde trabajo.",
                    "Recomendaría esta organización como un buen lugar para trabajar.",
                ],
            },
        ],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--username", default="johaba.jb", help="Colmena username that will own the project")
    parser.add_argument(
        "--title",
        default="Estrés Laboral y Desempeño Laboral",
        help="Project title (default: 'Estrés Laboral y Desempeño Laboral')",
    )
    parser.add_argument("--n", type=int, default=180, help="Number of simulated respondents (default: 180)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    return parser.parse_args()


def discretize(values: np.ndarray, n_points: int) -> np.ndarray:
    """Map continuous z-scores to 1..n_points via equal-probability bins."""
    cut_points = norm.ppf(np.linspace(0, 1, n_points + 1)[1:-1])
    bins = np.digitize(values, cut_points)
    return bins + 1


def simulate_item_scores(rng: np.random.Generator, n: int) -> dict[str, np.ndarray]:
    """Simulate one latent z-score series per (variable, dimension, item)."""
    variable_factors: dict[str, np.ndarray] = {}
    g_stress = rng.standard_normal(n)
    variable_factors["Estrés Laboral"] = g_stress
    eps = rng.standard_normal(n)
    variable_factors["Desempeño Laboral"] = (
        CROSS_VARIABLE_FACTOR_CORRELATION * g_stress
        + np.sqrt(1 - CROSS_VARIABLE_FACTOR_CORRELATION**2) * eps
    )

    series: dict[str, np.ndarray] = {}
    for variable in VARIABLES:
        g_v = variable_factors[variable["name"]]
        for dimension in variable["dimensions"]:
            f_d = DIMENSION_LOADING * g_v + np.sqrt(1 - DIMENSION_LOADING**2) * rng.standard_normal(n)
            for item_index, _ in enumerate(dimension["items"]):
                key = f"{dimension['code']}::{item_index}"
                series[key] = ITEM_LOADING * f_d + np.sqrt(1 - ITEM_LOADING**2) * rng.standard_normal(n)
    return series


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == args.username, User.deleted_at.is_(None)))
        if user is None:
            raise SystemExit(f"No active Colmena user found with username {args.username!r}.")

        type_research = db.scalar(select(TypeResearch).where(TypeResearch.name == "correlacional"))
        design_type = db.scalar(select(DesignType).where(DesignType.name == "no experimental"))
        approach = db.scalar(select(Approach).where(Approach.name == "cuantitativo"))
        scale = db.scalar(select(Scale).where(Scale.id == LIKERT_SCALE_ID))
        if scale is None:
            raise SystemExit(f"Expected preset scale {LIKERT_SCALE_ID!r} not found.")

        project = Project(
            user_id=user.id,
            title=args.title,
            subtitle="Estudio correlacional cuantitativo entre estrés y desempeño laboral",
            type_research_id=type_research.id if type_research else None,
            design_type_id=design_type.id if design_type else None,
            approach_id=approach.id if approach else None,
            status="active",
            notes=(
                "Proyecto generado con scripts/seed_two_variable_correlation_project.py "
                "para verificar descriptivos, confiabilidad, normalidad y correlación "
                "con datos simulados coherentes entre dos variables."
            ),
        )
        db.add(project)
        db.flush()

        form = Form(
            project_id=project.id,
            title="Cuestionario de Estrés y Desempeño Laboral",
            description="Instrumento único que recoge ambas escalas en la misma aplicación.",
            status="published",
            allow_anonymous=True,
        )
        db.add(form)
        db.flush()

        item_series = simulate_item_scores(rng, args.n)

        variable_records: list[ProjectVariable] = []
        question_lookup: dict[str, FormQuestion] = {}

        for var_index, variable in enumerate(VARIABLES):
            project_variable = ProjectVariable(
                project_id=project.id,
                name=variable["name"],
                code=variable["code"],
                variable_role="main",
                variable_classification=variable["classification"],
                measurement_mode="instrument",
                measurement_level="ordinal",
                data_type="numeric",
                is_required_for_analysis=True,
            )
            db.add(project_variable)
            db.flush()
            variable_records.append(project_variable)

            instrument = FormInstrument(
                form_id=form.id,
                project_variable_id=project_variable.id,
                default_scale_id=scale.id,
                name=variable["instrument_name"],
                acronym=variable["acronym"],
                response_scale_name=scale.name,
                application_mode="individual",
                scoring_method="Suma directa de los ítems por dimensión",
                sort_order=var_index,
            )
            db.add(instrument)
            db.flush()

            question_sort_order = 0
            for dim_index, dimension in enumerate(variable["dimensions"]):
                form_dimension = FormDimension(
                    instrument_id=instrument.id,
                    name=dimension["name"],
                    code=dimension["code"],
                    sort_order=dim_index,
                )
                db.add(form_dimension)
                db.flush()

                for item_index, label in enumerate(dimension["items"]):
                    question = FormQuestion(
                        form_id=form.id,
                        instrument_id=instrument.id,
                        dimension_id=form_dimension.id,
                        project_variable_id=project_variable.id,
                        scale_id=scale.id,
                        code=f"{dimension['code']}{item_index + 1}",
                        label=label,
                        question_type="likert",
                        question_role="item",
                        measurement_level="ordinal",
                        data_type="numeric",
                        is_required=True,
                        is_scored=True,
                        is_reverse_scored=False,
                        min_value=1,
                        max_value=5,
                        sort_order=question_sort_order,
                    )
                    db.add(question)
                    db.flush()
                    question_sort_order += 1

                    for opt_index, opt_label in enumerate(LIKERT_LABELS):
                        db.add(
                            FormQuestionOption(
                                question_id=question.id,
                                label=opt_label,
                                value=str(opt_index + 1),
                                score=float(opt_index + 1),
                                sort_order=opt_index,
                            )
                        )

                    question_lookup[f"{dimension['code']}::{item_index}"] = question

        db.commit()

        options_by_question: dict[str, list[FormQuestionOption]] = {}
        for key, question in question_lookup.items():
            options = list(
                db.scalars(
                    select(FormQuestionOption)
                    .where(FormQuestionOption.question_id == question.id)
                    .order_by(FormQuestionOption.sort_order)
                ).all()
            )
            options_by_question[key] = options

        n = args.n
        created = 0
        for respondent_index in range(n):
            response = FormResponse(
                project_id=project.id,
                form_id=form.id,
                respondent_code=f"SEED-{respondent_index + 1:03d}",
                status="complete",
                source=SEED_SOURCE,
            )
            db.add(response)
            db.flush()

            for key, question in question_lookup.items():
                options = options_by_question[key]
                latent = item_series[key][respondent_index]
                bucket = discretize(np.array([latent]), len(options))[0]
                bucket = int(np.clip(bucket, 1, len(options)))
                option = options[bucket - 1]

                db.add(
                    FormAnswer(
                        response_id=response.id,
                        question_id=question.id,
                        option_id=option.id,
                        value_text=option.value,
                        score_value=option.score,
                    )
                )
            created += 1

        db.commit()

        print(f"Created project {project.id!r} ({project.title}) for user {user.username!r}.")
        print(f"Form {form.id!r} published with {len(question_lookup)} Likert items across 2 variables / 4 dimensions.")
        print(f"Seeded {created} simulated responses (source={SEED_SOURCE!r}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
