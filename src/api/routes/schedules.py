from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import require_scopes
from ..models import ScheduleRequest, ScheduleResponse
from ..scheduling import next_run_at

router = APIRouter(prefix="/api/v1/schedules", tags=["schedules"])


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    request: Request,
    body: ScheduleRequest,
    _: dict = Depends(require_scopes("hapa:write")),
) -> ScheduleResponse:
    next_run = next_run_at(
        body.schedule_type,
        interval_seconds=body.interval_seconds,
        cron_expression=body.cron_expression,
        timezone_name=body.timezone,
    )
    schedule = request.app.state.store.create_schedule(
        {
            "schedule_id": str(uuid4()),
            "title": body.title,
            "description": body.description,
            "requested_by": body.requested_by,
            "schedule_type": body.schedule_type,
            "interval_seconds": body.interval_seconds,
            "cron_expression": body.cron_expression,
            "timezone": body.timezone,
            "callback_url": body.callback_url,
        },
        next_run,
    )
    return ScheduleResponse.model_validate(schedule)


@router.get("", response_model=list[ScheduleResponse])
def list_schedules(
    request: Request,
    _: dict = Depends(require_scopes("hapa:read")),
) -> list[ScheduleResponse]:
    return [ScheduleResponse.model_validate(item) for item in request.app.state.store.list_schedules()]


@router.post("/{schedule_id}/pause", response_model=ScheduleResponse)
def pause_schedule(
    schedule_id: UUID,
    request: Request,
    _: dict = Depends(require_scopes("hapa:write")),
) -> ScheduleResponse:
    return _set_state(request, schedule_id, "PAUSED")


@router.post("/{schedule_id}/resume", response_model=ScheduleResponse)
def resume_schedule(
    schedule_id: UUID,
    request: Request,
    _: dict = Depends(require_scopes("hapa:write")),
) -> ScheduleResponse:
    try:
        current = request.app.state.store.get_schedule(schedule_id)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Schedule not found") from exc
    next_run = next_run_at(
        current["schedule_type"],
        interval_seconds=current["interval_seconds"],
        cron_expression=current["cron_expression"],
        timezone_name=current["timezone"],
    )
    return ScheduleResponse.model_validate(
        request.app.state.store.update_schedule(schedule_id, state="ACTIVE", next_run_at=next_run)
    )


@router.post("/{schedule_id}/cancel", response_model=ScheduleResponse)
def cancel_schedule(
    schedule_id: UUID,
    request: Request,
    _: dict = Depends(require_scopes("hapa:write")),
) -> ScheduleResponse:
    return _set_state(request, schedule_id, "CANCELLED")


def _set_state(request: Request, schedule_id: UUID, state: str) -> ScheduleResponse:
    try:
        schedule = request.app.state.store.update_schedule(schedule_id, state=state)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Schedule not found") from exc
    return ScheduleResponse.model_validate(schedule)
