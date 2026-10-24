from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from src.core.schemas import TaskLifecycle

from ..auth import require_scopes
from ..models import ApprovalDecision, TaskResponse

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


@router.get("")
def list_approvals(request: Request, _: dict = Depends(require_scopes("hapa:approve"))) -> list[dict]:
    return request.app.state.store.list_approvals()


async def _decide(
    approval_id: UUID,
    request: Request,
    state: str,
    body: ApprovalDecision,
    __: dict,
) -> TaskResponse:
    try:
        approval = request.app.state.store.decide_approval(approval_id, state, body.comment)
        task_state = (
            TaskLifecycle.RUNNING.value
            if state == "APPROVED"
            else TaskLifecycle.CANCELLED.value
        )
        task = request.app.state.store.update_task(
            UUID(approval["task_id"]),
            state=task_state,
            approval_required=False,
        )
        event = request.app.state.store.add_event(
            UUID(approval["task_id"]),
            f"approval.{state.lower()}",
            {"approval_id": str(approval_id), "comment": approval["comment"]},
        )
        await request.app.state.telemetry.publish(event)
        return TaskResponse.model_validate(task)
    except KeyError as exc:
        raise HTTPException(404, "Approval not found or already decided") from exc


@router.post("/{approval_id}/approve", response_model=TaskResponse)
async def approve(approval_id: UUID, request: Request, body: ApprovalDecision, claims: dict = Depends(require_scopes("hapa:approve"))) -> TaskResponse:
    return await _decide(approval_id, request, "APPROVED", body, claims)


@router.post("/{approval_id}/reject", response_model=TaskResponse)
async def reject(approval_id: UUID, request: Request, body: ApprovalDecision, claims: dict = Depends(require_scopes("hapa:approve"))) -> TaskResponse:
    return await _decide(approval_id, request, "REJECTED", body, claims)
