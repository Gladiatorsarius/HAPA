"""FastAPI application factory."""

from __future__ import annotations

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from src.core.settings import AppSettings, load_settings

from .routes import approvals, chat, health, observability, tasks
from .store import ApiStore
from .websocket import TelemetryBus


def create_app(settings: AppSettings | None = None) -> FastAPI:
    config = settings or load_settings()
    app = FastAPI(title=config.name, debug=config.debug)
    app.state.settings = config
    app.state.store = ApiStore(config.storage.database_url)
    app.state.telemetry = TelemetryBus()
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(tasks.router)
    app.include_router(approvals.router)
    app.include_router(observability.router)

    @app.websocket("/api/v1/ws/telemetry")
    async def telemetry_socket(websocket: WebSocket) -> None:
        await websocket.accept()
        task_id = websocket.query_params.get("task_id")
        parsed_task_id = __import__("uuid").UUID(task_id) if task_id else None
        queue = await app.state.telemetry.subscribe(parsed_task_id)
        try:
            while True:
                await websocket.send_json(await queue.get())
        except WebSocketDisconnect:
            pass
        finally:
            await app.state.telemetry.unsubscribe(queue, parsed_task_id)

    return app


app = create_app()
