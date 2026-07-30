import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.realtime import broker

router = APIRouter(tags=["telemetry"])


async def _forward_events(websocket: WebSocket, form_id: str) -> None:
    async for event in broker.subscribe(form_id):
        await websocket.send_json(event)


async def _watch_disconnect(websocket: WebSocket) -> None:
    # Consume frames entrantes (pings del cliente) solo para detectar el cierre.
    while True:
        await websocket.receive_text()


@router.websocket("/api/ws/telemetry/{form_id}")
async def telemetry_websocket(websocket: WebSocket, form_id: str) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "form_id": form_id, "mode": broker.mode})

    forward_task = asyncio.create_task(_forward_events(websocket, form_id))
    disconnect_task = asyncio.create_task(_watch_disconnect(websocket))
    try:
        done, pending = await asyncio.wait(
            {forward_task, disconnect_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        for task in done:
            exc = task.exception()
            if exc is not None and not isinstance(exc, WebSocketDisconnect):
                raise exc
    except WebSocketDisconnect:
        pass
    finally:
        forward_task.cancel()
        disconnect_task.cancel()
