"""In-process telemetry fan-out for WebSocket and SSE consumers."""

from __future__ import annotations

import asyncio
from uuid import UUID


class TelemetryBus:
    def __init__(self) -> None:
        self._subscribers: dict[UUID | None, set[asyncio.Queue[dict]]] = {}

    async def subscribe(self, task_id: UUID | None = None) -> asyncio.Queue[dict]:
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(task_id, set()).add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict], task_id: UUID | None = None) -> None:
        subscribers = self._subscribers.get(task_id, set())
        subscribers.discard(queue)
        if not subscribers:
            self._subscribers.pop(task_id, None)

    async def publish(self, event: dict) -> None:
        task_id = UUID(str(event["task_id"]))
        for key in (None, task_id):
            for queue in tuple(self._subscribers.get(key, set())):
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    await queue.get()
                    queue.put_nowait(event)
