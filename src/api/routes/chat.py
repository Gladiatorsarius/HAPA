from fastapi import APIRouter, Depends, Request, status
from uuid import UUID

from ..auth import require_scopes
from ..models import ChatAcknowledgement, ChatMessageRequest, TaskRequest
from .tasks import submit_chat

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/messages", response_model=ChatAcknowledgement, status_code=status.HTTP_202_ACCEPTED)
async def message(
    request: Request,
    body: ChatMessageRequest,
    _: dict = Depends(require_scopes("hapa:write")),
) -> ChatAcknowledgement:
    task, answer = await submit_chat(
        request,
        TaskRequest(
            title=body.title,
            description=body.message,
            requested_by=body.requested_by,
            labels=body.labels,
            callback_url=body.callback_url,
        ),
    )
    return ChatAcknowledgement(
        chat_id=UUID(task["task_id"]),
        answer=answer,
        state=task["state"],
        follow_up_url=f"/api/v1/tasks/{task['task_id']}/events/stream",
        events_url=f"/api/v1/tasks/{task['task_id']}/events",
        callback_configured=body.callback_url is not None,
    )
