"""Broker de eventos de telemetría en tiempo real.

Publica eventos cuando llegan respuestas de formularios y los reparte a los
WebSockets suscritos. Usa Redis pub/sub cuando está disponible (multi-worker
safe); si Redis no responde al arrancar, cae a un broadcaster en memoria que
solo funciona dentro del mismo proceso (suficiente para desarrollo con un
worker de uvicorn).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import AsyncIterator
from typing import Any

import redis as redis_sync
import redis.asyncio as redis_async

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "colmena:telemetry:"


class TelemetryBroker:
    def __init__(self) -> None:
        self._redis_url: str | None = None
        self._mode: str = "local"
        self._sync_client: redis_sync.Redis | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._local_subscribers: dict[str, set[asyncio.Queue]] = {}
        self._lock = threading.Lock()

    @property
    def mode(self) -> str:
        return self._mode

    async def startup(self, redis_url: str) -> None:
        """Se llama en el lifespan de FastAPI. Detecta si Redis está disponible."""
        self._loop = asyncio.get_running_loop()
        self._redis_url = redis_url
        try:
            client = redis_sync.Redis.from_url(
                redis_url, socket_connect_timeout=1, socket_timeout=1
            )
            client.ping()
            self._sync_client = client
            self._mode = "redis"
            logger.info("Telemetry broker: Redis pub/sub en %s", redis_url)
        except Exception as exc:  # noqa: BLE001 - cualquier fallo => fallback local
            self._sync_client = None
            self._mode = "local"
            logger.warning(
                "Telemetry broker: Redis no disponible (%s); usando broadcaster en memoria", exc
            )

    async def shutdown(self) -> None:
        if self._sync_client is not None:
            try:
                self._sync_client.close()
            except Exception:  # noqa: BLE001
                pass
        self._sync_client = None
        self._loop = None

    def publish(self, form_id: str, event: dict[str, Any]) -> None:
        """Publica un evento. Sync-safe: se llama desde los servicios (threadpool).

        Nunca lanza: un fallo al publicar no debe romper el guardado de la respuesta.
        """
        try:
            payload = json.dumps(event, default=str)
            if self._mode == "redis" and self._sync_client is not None:
                self._sync_client.publish(CHANNEL_PREFIX + form_id, payload)
                return
            self._publish_local(form_id, event)
        except Exception:  # noqa: BLE001
            logger.exception("Telemetry broker: fallo publicando evento para form %s", form_id)

    def _publish_local(self, form_id: str, event: dict[str, Any]) -> None:
        loop = self._loop
        if loop is None:
            return
        with self._lock:
            queues = list(self._local_subscribers.get(form_id, ()))
        for queue in queues:
            loop.call_soon_threadsafe(queue.put_nowait, event)

    async def subscribe(self, form_id: str) -> AsyncIterator[dict[str, Any]]:
        """Iterador async de eventos para un formulario (lo consume el WebSocket)."""
        if self._mode == "redis" and self._redis_url is not None:
            client = redis_async.Redis.from_url(self._redis_url)
            pubsub = client.pubsub()
            await pubsub.subscribe(CHANNEL_PREFIX + form_id)
            try:
                async for message in pubsub.listen():
                    if message["type"] != "message":
                        continue
                    try:
                        yield json.loads(message["data"])
                    except (TypeError, ValueError):
                        continue
            finally:
                try:
                    await pubsub.unsubscribe(CHANNEL_PREFIX + form_id)
                    await pubsub.aclose()
                    await client.aclose()
                except Exception:  # noqa: BLE001
                    pass
        else:
            queue: asyncio.Queue = asyncio.Queue()
            with self._lock:
                self._local_subscribers.setdefault(form_id, set()).add(queue)
            try:
                while True:
                    yield await queue.get()
            finally:
                with self._lock:
                    subscribers = self._local_subscribers.get(form_id)
                    if subscribers is not None:
                        subscribers.discard(queue)
                        if not subscribers:
                            self._local_subscribers.pop(form_id, None)


broker = TelemetryBroker()


def publish_response_event(
    *,
    form_id: str,
    project_id: str,
    response_id: str,
    response_status: str,
    submitted_at: Any,
    source: str,
) -> None:
    """Helper para los servicios: arma y publica el evento de respuesta recibida."""
    broker.publish(
        form_id,
        {
            "type": "response.submitted",
            "form_id": form_id,
            "project_id": project_id,
            "response_id": response_id,
            "status": response_status,
            "submitted_at": submitted_at.isoformat() if submitted_at else None,
            "source": source,
        },
    )
