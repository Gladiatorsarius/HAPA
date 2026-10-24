"""Discord webhook normalization without coupling the API to discord.py."""

from __future__ import annotations

import hmac

from fastapi import APIRouter, Header, HTTPException, Request

from src.api.models import ChatMessageRequest, TaskResponse
from src.api.routes.tasks import _create

router = APIRouter(prefix="/webhooks/discord", tags=["integrations"])


def _check_secret(expected: str, received: str | None) -> None:
    if expected and not received or expected and not hmac.compare_digest(expected, received or ""):
        raise HTTPException(401, "Invalid webhook secret")


@router.post("", response_model=TaskResponse, status_code=201)
async def receive(request: Request, payload: dict, x_hapa_webhook_secret: str | None = Header(default=None)) -> TaskResponse:
    settings = request.app.state.settings.integrations
    if not settings.discord_enabled:
        raise HTTPException(404, "Discord integration is disabled")
    _check_secret(settings.discord_webhook_secret, x_hapa_webhook_secret)
    content = payload.get("content")
    author = payload.get("author", {}).get("username", "discord")
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(422, "Discord payload must contain content")
    return await _create(request, ChatMessageRequest(message=content, requested_by=f"discord:{author}", title="Discord message"))
