"""Small dependency-free HS256 JWT validator for API boundaries."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.settings import AuthSettings

_bearer = HTTPBearer(auto_error=False)


def _decode_part(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def decode_jwt(token: str, settings: AuthSettings) -> dict[str, Any]:
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}".encode()
        expected = hmac.new(settings.jwt_secret.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _decode_part(signature)):
            raise ValueError("invalid signature")
        claims = json.loads(_decode_part(payload))
    except (ValueError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid bearer token") from exc
    if claims.get("iss") != settings.issuer_url or claims.get("aud") != settings.audience:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token issuer or audience")
    if claims.get("exp", 0) < time.time():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired")
    return claims


def require_scopes(settings: AuthSettings, *required: str):
    def dependency(credentials: HTTPAuthorizationCredentials | None = Security(_bearer)) -> dict[str, Any]:
        if credentials is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
        claims = decode_jwt(credentials.credentials, settings)
        scopes = set(claims.get("scope", "").split())
        if not set(required).issubset(scopes):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Required scope is missing")
        return claims
    return dependency
