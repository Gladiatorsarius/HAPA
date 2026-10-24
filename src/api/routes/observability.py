import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ..auth import require_scopes

router = APIRouter(prefix="/api/v1", tags=["observability"])


@router.get("/tasks/{task_id}/events")
def events(task_id: UUID, request: Request, _: dict = Depends(require_scopes("hapa:read"))) -> list[dict]:
    return request.app.state.store.list_events(task_id)


@router.get("/tasks/{task_id}/events/stream")
async def stream(task_id: UUID, request: Request, _: dict = Depends(require_scopes("hapa:read"))) -> StreamingResponse:
    queue = await request.app.state.telemetry.subscribe(task_id)

    async def generate() -> AsyncIterator[str]:
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=request.app.state.settings.telemetry.sse_keepalive_seconds)
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await request.app.state.telemetry.unsubscribe(queue, task_id)

    return StreamingResponse(generate(), media_type="text/event-stream")
