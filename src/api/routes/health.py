from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(request: Request) -> dict[str, str]:
    request.app.state.store.list_tasks()
    return {"status": "ready"}


@router.get("/api/v1/telemetry")
def telemetry(request: Request) -> dict[str, int]:
    return {"tasks": len(request.app.state.store.list_tasks()), "events": sum(len(request.app.state.store.list_events(__import__("uuid").UUID(task["task_id"]))) for task in request.app.state.store.list_tasks())}
