"""Telegram webhook normalization without coupling the API to python-telegram-bot."""

from fastapi import APIRouter, Header, HTTPException, Request

from src.api.models import ChatMessageRequest, TaskResponse
from src.api.routes.tasks import _create
from .discord_bot import _check_secret

router = APIRouter(prefix="/webhooks/telegram", tags=["integrations"])


@router.post("", response_model=TaskResponse, status_code=201)
async def receive(request: Request, payload: dict, x_hapa_webhook_secret: str | None = Header(default=None)) -> TaskResponse:
    settings = request.app.state.settings.integrations
    if not settings.telegram_enabled:
        raise HTTPException(404, "Telegram integration is disabled")
    _check_secret(settings.telegram_webhook_secret, x_hapa_webhook_secret)
    message = payload.get("message", {})
    text = message.get("text")
    sender = message.get("from", {}).get("username", "telegram")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(422, "Telegram payload must contain message.text")
    return await _create(request, ChatMessageRequest(message=text, requested_by=f"telegram:{sender}", title="Telegram message"))
