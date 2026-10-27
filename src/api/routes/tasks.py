import asyncio
import json
from urllib.request import Request as UrlRequest, urlopen
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.core.schemas import TaskLifecycle
from src.tiers.tier1_supervisor.graph import build_supervisor_graph
from src.tiers.tier1_supervisor.state import create_initial_state

from ..auth import require_scopes
from ..models import TaskRequest, TaskResponse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def _persist_state(request: Request, state: dict, body: TaskRequest) -> dict:
    state["metadata"] = state["metadata"].model_copy(update={"labels": body.labels})
    task = request.app.state.store.create_task(
        {
            "task_id": state["metadata"].task_id,
            "title": body.title,
            "description": body.description,
            "lineage": state["lineage"].model_dump(mode="json"),
            "provenance": state["metadata"].provenance.model_dump(mode="json"),
            "callback_url": body.callback_url,
        },
        state["status"].state.value,
        False,
    )
    return task


async def _deliver_callback(request: Request, callback_url: str | None, payload: dict) -> None:
    if not callback_url:
        return
    body = json.dumps({"version": 1, **payload}, default=str).encode()

    def send() -> None:
        url_request = UrlRequest(
            callback_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(url_request, timeout=10) as response:
            response.read()

    try:
        await asyncio.to_thread(send)
    except OSError as exc:
        task_id = UUID(str(payload["task_id"]))
        event = request.app.state.store.add_event(
            task_id,
            "callback.failed",
            {"callback_url": callback_url, "error": str(exc)},
        )
        await request.app.state.telemetry.publish(event)


async def _execute_state(request: Request, state: dict, *, callback_url: str | None = None, event_prefix: str = "task") -> None:
    task_id = state["metadata"].task_id
    try:
        result = await asyncio.to_thread(build_supervisor_graph().invoke, state)
        lifecycle = result["status"].state
        request.app.state.store.update_task(
            task_id, state=lifecycle.value, approval_required=result["approval_required"]
        )
        payload = {
            "task_id": str(task_id),
            "state": lifecycle.value,
            "answer": result.get("plan") or f"{event_prefix.capitalize()} execution completed.",
            "provenance": result["metadata"].provenance.model_dump(mode="json"),
        }
        if event_prefix == "chat":
            payload["chat_id"] = str(task_id)
        event = request.app.state.store.add_event(task_id, f"{event_prefix}.completed", payload)
        await request.app.state.telemetry.publish(event)
        await _deliver_callback(request, callback_url, payload)
    except (KeyError, RuntimeError, TypeError, ValueError) as exc:
        task = request.app.state.store.update_task(task_id, state=TaskLifecycle.FAILED.value)
        payload = {"task_id": str(task_id), "state": task["state"], "error": str(exc)}
        event = request.app.state.store.add_event(task_id, f"{event_prefix}.failed", payload)
        await request.app.state.telemetry.publish(event)
        await _deliver_callback(request, callback_url, payload)


async def _create(request: Request, body: TaskRequest) -> TaskResponse:
    state = create_initial_state(
        title=body.title,
        description=body.description,
        requested_by=body.requested_by,
        source="api",
    )
    state["metadata"] = state["metadata"].model_copy(update={"labels": body.labels})
    result = build_supervisor_graph().invoke(state)
    approval_required = result["approval_required"]
    lifecycle = result["status"].state
    task = request.app.state.store.create_task(
        {
            "task_id": result["metadata"].task_id,
            "title": body.title,
            "description": body.description,
            "lineage": result["lineage"].model_dump(mode="json"),
            "provenance": result["metadata"].provenance.model_dump(mode="json"),
            "callback_url": body.callback_url,
        },
        lifecycle.value,
        approval_required,
    )
    event = request.app.state.store.add_event(result["metadata"].task_id, "task.created", {"state": lifecycle.value})
    await request.app.state.telemetry.publish(event)
    if approval_required:
        approval_id = uuid4()
        request.app.state.store.add_approval(result["metadata"].task_id, approval_id)
        approval_event = request.app.state.store.add_event(result["metadata"].task_id, "approval.required", {"approval_id": str(approval_id)})
        await request.app.state.telemetry.publish(approval_event)
    await _deliver_callback(
        request,
        body.callback_url,
        {
            "task_id": str(result["metadata"].task_id),
            "state": lifecycle.value,
            "answer": result.get("plan") or "Task execution completed.",
            "provenance": result["metadata"].provenance.model_dump(mode="json"),
        },
    )
    return TaskResponse.model_validate(
        task
        | {
            "lineage": result["lineage"].model_dump(mode="json"),
            "provenance": result["metadata"].provenance.model_dump(mode="json"),
        }
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: Request, body: TaskRequest, _: dict = Depends(require_scopes("hapa:write"))) -> TaskResponse:
    return await _create(request, body)


async def submit_chat(request: Request, body: TaskRequest) -> tuple[dict, str]:
    state = create_initial_state(
        title=body.title,
        description=body.description,
        requested_by=body.requested_by,
        source="api",
    )
    task = _persist_state(request, state, body)
    accepted = request.app.state.store.add_event(
        state["metadata"].task_id,
        "chat.accepted",
        {
            "chat_id": str(state["metadata"].task_id),
            "task_id": str(state["metadata"].task_id),
            "answer": f"Tier 1 accepted '{body.title}'. Execution will continue asynchronously.",
        },
    )
    await request.app.state.telemetry.publish(accepted)
    asyncio.create_task(
        _execute_state(request, state, callback_url=body.callback_url, event_prefix="chat")
    )
    return task, f"Tier 1 accepted '{body.title}'. Execution will continue asynchronously."


@router.get("", response_model=list[TaskResponse])
def list_tasks(request: Request, _: dict = Depends(require_scopes("hapa:read"))) -> list[TaskResponse]:
    return [
        TaskResponse.model_validate(task)
        for task in request.app.state.store.list_tasks(active_only=True)
    ]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, request: Request, _: dict = Depends(require_scopes("hapa:read"))) -> TaskResponse:
    try:
        return TaskResponse.model_validate(request.app.state.store.get_task(task_id))
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found") from exc


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: UUID, request: Request, _: dict = Depends(require_scopes("hapa:write"))) -> TaskResponse:
    try:
        task = request.app.state.store.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found") from exc
    if task["state"] in {TaskLifecycle.SUCCESS.value, TaskLifecycle.FAILED.value, TaskLifecycle.CANCELLED.value}:
        raise HTTPException(status.HTTP_409_CONFLICT, "Task is already terminal")
    return TaskResponse.model_validate(
        request.app.state.store.update_task(task_id, state=TaskLifecycle.CANCELLED.value)
    )
