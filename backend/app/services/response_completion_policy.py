"""Política de completitud de sesiones de respuesta (harness §16-17).

Deliberadamente separada de `ScoringService._scoring_config` (namespace
`scoring`, usado por la política de missing-data a nivel de constructo, con
su propio default 80%): esta política vive bajo `response_validation` para
no acoplar ni cambiar el comportamiento existente de la política de scoring.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.study import Study

DEFAULT_MIN_COMPLETION_PERCENT = 60.0
DEFAULT_MIN_ANSWERED_COUNT = 5


@dataclass
class CompletionPolicy:
    min_completion_percent: float
    min_answered_count: int


def resolve_completion_policy(study: Study) -> CompletionPolicy:
    config = {
        "min_completion_percent": DEFAULT_MIN_COMPLETION_PERCENT,
        "min_answered_count": DEFAULT_MIN_ANSWERED_COUNT,
    }
    if study.instrument_version is not None:
        config.update((study.instrument_version.config or {}).get("response_validation", {}))
    config.update((study.settings or {}).get("response_validation", {}))
    return CompletionPolicy(
        min_completion_percent=float(config["min_completion_percent"]),
        min_answered_count=int(config["min_answered_count"]),
    )
