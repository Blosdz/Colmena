"""Rate limit en memoria por IP (E-17), ventana deslizante.

Sin Redis — no hay esa infraestructura en el proyecto. Limitación conocida y
documentada: en un despliegue multi-worker/multi-proceso cada proceso
llevaría su propio cupo, así que el límite real sería
`public_session_rate_limit_max * n_workers`. Suficiente para bloquear
inyección masiva de respuestas desde un único proceso; una mejora futura
fuera de este alcance sería centralizar el cupo en Redis.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import RateLimitExceededError

_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def enforce_public_session_rate_limit(request: Request) -> None:
    settings = get_settings()
    key = _client_key(request)
    now = time.monotonic()
    bucket = _buckets[key]
    while bucket and now - bucket[0] > settings.public_session_rate_limit_window_seconds:
        bucket.popleft()
    if len(bucket) >= settings.public_session_rate_limit_max:
        raise RateLimitExceededError(
            "Demasiadas solicitudes; intente de nuevo en unos minutos.",
            retry_after_seconds=settings.public_session_rate_limit_window_seconds,
        )
    bucket.append(now)
