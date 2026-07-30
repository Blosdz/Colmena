#!/usr/bin/env python3
"""DEV TOOL — NOT A PRODUCTION FEATURE.

Seeds simulated Likert responses into a demo project so the reliability
(Cronbach's alpha), normality, and inferential stages can be exercised
visually with realistic-looking data instead of an empty instrument.

Rerunning this script is safe: it first deletes any responses it
previously created (tagged with source="dev_seed") for the target form,
then regenerates a fresh batch.

Usage:
    cd COLMENA/backend
    source venv/bin/activate  # or .venv, whichever this checkout uses
    python scripts/seed_demo_reliability.py --project-name DEMO1 --n 80

This must never be wired into any API route, scheduled job, or app
startup path — it is a one-off CLI helper for local/dev environments only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.models.form import Form
from app.models.form_answer import FormAnswer
from app.models.form_question import FormQuestion
from app.models.form_question_option import FormQuestionOption
from app.models.form_response import FormResponse
from app.models.project import Project

SEED_SOURCE = "dev_seed"

# Target latent correlations: items in the same dimension correlate more
# strongly than items across dimensions, which is what makes Cronbach's
# alpha realistic (neither pure noise -> alpha ~ 0, nor a degenerate
# perfect correlation -> alpha = 1). Sampled jointly via a multivariate
# normal (not summed independent factors) so the realized sample
# correlation actually lands near the target instead of drifting due to
# accumulated finite-sample noise from several independent draws.
WITHIN_DIMENSION_CORRELATION = 0.75
ACROSS_DIMENSION_CORRELATION = 0.68


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-name", default="DEMO1", help="Project title to seed (default: DEMO1)")
    parser.add_argument("--project-id", default=None, help="Exact project id to seed; overrides --project-name")
    parser.add_argument("--n", type=int, default=80, help="Number of simulated responses to generate (default: 80)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    return parser.parse_args()


def discretize(values: np.ndarray, n_points: int) -> np.ndarray:
    """Map continuous z-scores to 1..n_points via equal-probability bins."""
    cut_points = norm.ppf(np.linspace(0, 1, n_points + 1)[1:-1])
    bins = np.digitize(values, cut_points)
    return bins + 1


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    db = SessionLocal()
    try:
        if args.project_id:
            project = db.scalar(
                select(Project).where(Project.id == args.project_id, Project.deleted_at.is_(None))
            )
            if project is None:
                raise SystemExit(f"No active project found with id {args.project_id!r}.")
            candidates = [project]
        else:
            candidates = list(
                db.scalars(
                    select(Project).where(Project.title == args.project_name, Project.deleted_at.is_(None))
                ).all()
            )
            if not candidates:
                raise SystemExit(f"No active project found with title {args.project_name!r}.")

        form = None
        project = None
        for candidate in candidates:
            candidate_form = db.scalar(
                select(Form)
                .where(Form.project_id == candidate.id, Form.deleted_at.is_(None))
                .order_by(Form.status.desc())
            )
            if candidate_form is not None:
                has_likert = db.scalar(
                    select(FormQuestion.id).where(
                        FormQuestion.form_id == candidate_form.id,
                        FormQuestion.deleted_at.is_(None),
                        FormQuestion.question_type == "likert",
                    )
                )
                if has_likert:
                    project, form = candidate, candidate_form
                    break
        if form is None:
            raise SystemExit(
                f"No project named {args.project_name!r} has a form with active Likert questions. "
                "Pass --project-id to target a specific project explicitly."
            )

        questions = list(
            db.scalars(
                select(FormQuestion)
                .options(selectinload(FormQuestion.options))
                .where(
                    FormQuestion.form_id == form.id,
                    FormQuestion.deleted_at.is_(None),
                    FormQuestion.question_type == "likert",
                )
                .order_by(FormQuestion.sort_order)
            ).all()
        )
        if not questions:
            raise SystemExit(f"Form {form.id} has no active Likert questions to seed.")

        # Clean up any previous seed run for this form before regenerating.
        previous_ids = list(
            db.scalars(
                select(FormResponse.id).where(FormResponse.form_id == form.id, FormResponse.source == SEED_SOURCE)
            ).all()
        )
        if previous_ids:
            db.query(FormAnswer).filter(FormAnswer.response_id.in_(previous_ids)).delete(synchronize_session=False)
            db.query(FormResponse).filter(FormResponse.id.in_(previous_ids)).delete(synchronize_session=False)
            db.commit()
            print(f"Removed {len(previous_ids)} previously seeded responses for form {form.id}.")

        n = args.n

        # Build a joint correlation matrix across all items in one shot and
        # sample latent scores from it directly, so the realized sample
        # correlation lands close to the target instead of drifting the way
        # a sum of several independent factors would at n=80.
        item_count = len(questions)
        correlation_matrix = np.eye(item_count)
        for i in range(item_count):
            for j in range(item_count):
                if i == j:
                    continue
                same_dimension = questions[i].dimension_id == questions[j].dimension_id and questions[i].dimension_id is not None
                correlation_matrix[i, j] = WITHIN_DIMENSION_CORRELATION if same_dimension else ACROSS_DIMENSION_CORRELATION

        latent_scores = rng.multivariate_normal(mean=np.zeros(item_count), cov=correlation_matrix, size=n)

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

            for item_index, question in enumerate(questions):
                active_options = sorted(
                    (option for option in question.options if option.deleted_at is None and option.score is not None),
                    key=lambda option: option.score,
                )
                if not active_options:
                    continue

                latent = latent_scores[respondent_index, item_index]
                bucket = discretize(np.array([latent]), len(active_options))[0]
                bucket = int(np.clip(bucket, 1, len(active_options)))
                option: FormQuestionOption = active_options[bucket - 1]

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
        print(
            f"Seeded {created} responses into form {form.id} ({project.title}), "
            f"answering {len(questions)} Likert item(s) across {len({q.dimension_id for q in questions})} dimension(s)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
