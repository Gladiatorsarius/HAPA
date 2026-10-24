from fastapi import APIRouter, Depends, Request, status

from ..auth import require_scopes
from ..models import ChatMessageRequest, TaskResponse
from .tasks import _create
from .tasks import TaskRequest

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/messages", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def message(request: Request, body: ChatMessageRequest, _: dict = Depends(require_scopes("hapa:write"))) -> TaskResponse:
    return await _create(request, TaskRequest(title=body.title, description=body.message, requested_by=body.requested_by, labels=body.labels))
