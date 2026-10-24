# HAPA API reference

HAPA is a FastAPI gateway for task orchestration, human approvals, and
realtime task telemetry. It exposes:

- a JSON-over-HTTP API under `/api/v1`;
- an HTTP Server-Sent Events (SSE) stream for task events;
- a WebSocket telemetry feed;
- inbound Discord and Telegram webhook adapters.

The Discord and Telegram adapters are intentionally thin. They do not call the
Discord or Telegram APIs themselves; they accept provider webhook payloads,
extract a message, and submit it through the same task creation pipeline as
the website API.

## Running the API

The default development configuration listens on `http://localhost:8000`.
The host, port, and public URL are configured in
[`config/settings.yaml`](config/settings.yaml).

```sh
./scripts/entrypoint.sh
```

FastAPI also publishes an interactive OpenAPI UI at `/docs` and a ReDoc view
at `/redoc` when the application is running. The OpenAPI schema is available
at `/openapi.json`.

## Common conventions

### Base URLs

For a local deployment:

```text
HTTP base URL: http://localhost:8000
API base URL:  http://localhost:8000/api/v1
WebSocket URL: ws://localhost:8000/api/v1/ws/telemetry
```

Use `https://` and `wss://` behind TLS in production.

### Authentication and authorization

All `/api/v1` task, chat, approval, and event routes require an OAuth/OIDC
bearer token. HAPA validates an HS256 JWT locally using the configured
`auth.jwt_secret`. The token must contain:

- `iss` equal to `auth.issuer_url`;
- `aud` equal to `auth.audience`;
- an `exp` timestamp in the future;
- the scope required by the route.

Send the token as:

```http
Authorization: Bearer <jwt>
```

The scopes are:

| Scope | Allows |
|---|---|
| `hapa:read` | List and read tasks, read event history, and consume SSE |
| `hapa:write` | Create, chat-submit, and cancel tasks |
| `hapa:approve` | List and decide human approvals |

Missing credentials result in `401 Unauthorized`. A valid token without the
required scope results in `403 Forbidden`. Invalid issuer, audience, expiry, or
signature also results in `401 Unauthorized`.

The health endpoints and the aggregate telemetry endpoint are public. The
WebSocket currently accepts a connection without bearer-token validation; put
it behind an authenticated reverse proxy if it is exposed outside a trusted
network.

### JSON validation

Request bodies use strict Pydantic models and reject unknown fields. Text
fields marked as required must not be empty. Invalid JSON or validation errors
normally return `422 Unprocessable Entity`.

### Task lifecycle

Task responses use these states:

| State | Meaning |
|---|---|
| `PENDING` | Task has been accepted but has not started running |
| `RUNNING` | Task is being processed |
| `BLOCKED_AT_HUMAN_GATE` | Human approval is required |
| `SUCCESS` | Task completed successfully |
| `FAILED` | Task failed |
| `CANCELLED` | Task was cancelled |

Every task includes a UUID `task_id`, execution lineage, and provenance. The
provenance identifies the input source (`api`, `discord`, or `telegram`),
requesting actor, and receipt time.

## HTTP API

### `GET /health/live`

Public liveness probe. It does not access the database.

Response `200`:

```json
{
  "status": "ok"
}
```

### `GET /health/ready`

Public readiness probe. It checks that the configured store can be queried.

Response `200`:

```json
{
  "status": "ready"
}
```

If the store cannot be queried, the request fails rather than returning a
false-ready response.

### `GET /api/v1/telemetry`

Public aggregate telemetry. It returns the number of stored tasks and the
total number of events across those tasks.

Response `200`:

```json
{
  "tasks": 4,
  "events": 12
}
```

### `POST /api/v1/tasks`

Creates a task and immediately runs it through the supervisor routing
pipeline. Requires `hapa:write`.

Request:

```json
{
  "title": "Add login",
  "description": "Implement and test login",
  "requested_by": "web-user-123",
  "labels": ["web", "authentication"]
}
```

Fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `title` | non-empty string | yes | Human-readable task title |
| `description` | string | no | Task instructions; defaults to `""` |
| `requested_by` | non-empty string | yes | Actor or client identity |
| `labels` | array of non-empty strings | no | Client-defined labels; defaults to `[]` |

Response `201` is a `TaskResponse`:

```json
{
  "task_id": "2d7f5f50-f8a8-4c18-93f4-8e8c9df6c3a8",
  "title": "Add login",
  "description": "Implement and test login",
  "state": "RUNNING",
  "approval_required": false,
  "lineage": {
    "correlation_id": "8d6ab4cc-5fd5-4f03-8a75-b0bd7ca25092",
    "parent_task_id": null,
    "root_task_id": "2d7f5f50-f8a8-4c18-93f4-8e8c9df6c3a8",
    "hop_number": 1,
    "requested_by": "web-user-123",
    "preceding_handoff_id": null
  },
  "provenance": {
    "source": "api",
    "actor": "web-user-123",
    "received_at": "2026-10-24T14:15:00Z"
  },
  "created_at": "2026-10-24T14:15:00Z",
  "updated_at": "2026-10-24T14:15:00Z"
}
```

The exact state depends on supervisor routing. Tasks that need a human gate
are returned as `BLOCKED_AT_HUMAN_GATE` with `approval_required: true`.

Example:

```sh
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <jwt-with-hapa:write>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add login",
    "description": "Implement and test login",
    "requested_by": "web-user-123",
    "labels": ["web"]
  }'
```

### `GET /api/v1/tasks`

Lists active tasks and requires `hapa:read`. The response is an array of
`TaskResponse` objects. “Active” means the task state is `PENDING`, `RUNNING`,
or `BLOCKED_AT_HUMAN_GATE`; terminal tasks are not returned by this endpoint.

### `GET /api/v1/tasks/{task_id}`

Returns one task by UUID and requires `hapa:read`.

- `200`: `TaskResponse`
- `404`: `{"detail": "Task not found"}`
- `422`: malformed UUID

### `POST /api/v1/tasks/{task_id}/cancel`

Cancels a non-terminal task and requires `hapa:write`. The response is the
updated `TaskResponse`.

- `404`: task does not exist
- `409`: task is already `SUCCESS`, `FAILED`, or `CANCELLED`
- `422`: malformed UUID

### `POST /api/v1/chat/messages`

Creates a task from a chat-style request and requires `hapa:write`. This is
the website-friendly alternative to supplying `description` directly.

Request:

```json
{
  "message": "Investigate the failing checkout tests",
  "requested_by": "web-chat-user-123",
  "title": "Checkout investigation",
  "labels": ["support"]
}
```

`message` and `requested_by` are required non-empty strings. `title` defaults
to `Chat task`, and `labels` defaults to an empty array. The response is the
same `TaskResponse` returned by task creation, with provenance source `api`.

### `GET /api/v1/approvals`

Lists pending approvals and requires `hapa:approve`.

Response:

```json
[
  {
    "approval_id": "97bd0bca-4f3d-4daf-a3ef-e9be4ff6a5dd",
    "task_id": "2d7f5f50-f8a8-4c18-93f4-8e8c9df6c3a8",
    "state": "PENDING",
    "comment": "",
    "created_at": "2026-10-24T14:15:00Z",
    "decided_at": null
  }
]
```

Only pending approvals are listed.

### `POST /api/v1/approvals/{approval_id}/approve`

Approves a pending approval and requires `hapa:approve`. The task is moved to
`RUNNING`, `approval_required` becomes `false`, and an
`approval.approved` event is emitted.

Request body:

```json
{
  "comment": "Reviewed and approved for execution"
}
```

`comment` is optional and defaults to `""`. The response is the updated
`TaskResponse`.

### `POST /api/v1/approvals/{approval_id}/reject`

Rejects a pending approval and requires `hapa:approve`. The task is moved to
`CANCELLED`, `approval_required` becomes `false`, and an
`approval.rejected` event is emitted. The reviewer comment is preserved.

Both decision endpoints return `404` when the approval does not exist or has
already been decided.

### `GET /api/v1/tasks/{task_id}/events`

Returns the durable event history for a task and requires `hapa:read`.

Response:

```json
[
  {
    "event_id": 1,
    "task_id": "2d7f5f50-f8a8-4c18-93f4-8e8c9df6c3a8",
    "event_type": "task.created",
    "payload": {
      "state": "BLOCKED_AT_HUMAN_GATE"
    },
    "created_at": "2026-10-24T14:15:00Z"
  },
  {
    "event_id": 2,
    "task_id": "2d7f5f50-f8a8-4c18-93f4-8e8c9df6c3a8",
    "event_type": "approval.required",
    "payload": {
      "approval_id": "97bd0bca-4f3d-4daf-a3ef-e9be4ff6a5dd"
    },
    "created_at": "2026-10-24T14:15:00Z"
  }
]
```

The current API records `task.created`, `approval.required`,
`approval.approved`, and `approval.rejected` events. The event payload is
event-specific and should be treated as an extensible object.

## Realtime API

### SSE: `GET /api/v1/tasks/{task_id}/events/stream`

Opens an authenticated, task-specific Server-Sent Events stream. It requires
`hapa:read`.

```sh
curl -N http://localhost:8000/api/v1/tasks/<task-id>/events/stream \
  -H "Authorization: Bearer <jwt-with-hapa:read>"
```

Each event is sent as a JSON object in an SSE `data` field:

```text
data: {"event_id":2,"task_id":"...","event_type":"approval.required","payload":{"approval_id":"..."},"created_at":"..."}

```

The stream sends `: keepalive` comments after the configured
`telemetry.sse_keepalive_seconds` interval (15 seconds by default). Clients
should ignore comment lines and reconnect after a dropped connection. The
stream subscribes to newly published events; it does not replay events already
stored before the connection was opened. Use the events HTTP endpoint first if
a complete history is required.

### WebSocket: `GET /api/v1/ws/telemetry`

Opens a JSON WebSocket telemetry stream:

```text
ws://localhost:8000/api/v1/ws/telemetry
```

To receive events for one task only, add its UUID as a query parameter:

```text
ws://localhost:8000/api/v1/ws/telemetry?task_id=<task-id>
```

Without `task_id`, the connection receives events for all tasks published by
this API process. With `task_id`, it receives only matching events. Messages
use the same event shape as the events HTTP endpoint:

```json
{
  "event_id": 2,
  "task_id": "2d7f5f50-f8a8-4c18-93f4-8e8c9df6c3a8",
  "event_type": "approval.required",
  "payload": {
    "approval_id": "97bd0bca-4f3d-4daf-a3ef-e9be4ff6a5dd"
  },
  "created_at": "2026-10-24T14:15:00Z"
}
```

The bus is in-process and has a bounded queue of 100 messages per subscriber.
When a subscriber falls behind, the oldest queued message is discarded.
Therefore, use durable event history to recover from gaps. The current
endpoint does not authenticate the WebSocket handshake and does not replay
historical events.

## Discord webhook API

### `POST /webhooks/discord`

This endpoint accepts a Discord message-shaped JSON payload and creates a
HAPA task. It is disabled by default and is not under `/api/v1`.

Enable it in `config/settings.yaml`:

```yaml
integrations:
  discord_enabled: true
  discord_webhook_secret: replace-with-a-long-random-secret
```

If `discord_webhook_secret` is non-empty, callers must send:

```http
X-HAPA-Webhook-Secret: replace-with-a-long-random-secret
```

Supported input:

```json
{
  "content": "Investigate the checkout failure",
  "author": {
    "username": "alice"
  }
}
```

`content` must be a non-empty string. `author.username` is optional and
defaults to `discord`. The adapter submits:

- title: `Discord message`;
- description: `content`;
- requested-by: `discord:<username>`;
- provenance source: `discord`.

It returns `201` with the normal `TaskResponse`. Disabled integrations return
`404`; a wrong configured secret returns `401`; missing or invalid `content`
returns `422`.

Example:

```sh
curl -X POST http://localhost:8000/webhooks/discord \
  -H "X-HAPA-Webhook-Secret: replace-with-a-long-random-secret" \
  -H "Content-Type: application/json" \
  -d '{"content":"Investigate checkout","author":{"username":"alice"}}'
```

This adapter does not verify Discord signatures or implement Discord
interaction acknowledgement semantics. Put it behind a gateway that
validates the provider request when those guarantees are required.

## Telegram webhook API

### `POST /webhooks/telegram`

This endpoint accepts a Telegram Update-shaped JSON payload and creates a
HAPA task. It is disabled by default.

Enable it in `config/settings.yaml`:

```yaml
integrations:
  telegram_enabled: true
  telegram_webhook_secret: replace-with-a-long-random-secret
```

If `telegram_webhook_secret` is non-empty, send it in
`X-HAPA-Webhook-Secret`.

Supported input:

```json
{
  "message": {
    "text": "Investigate the checkout failure",
    "from": {
      "username": "alice"
    }
  }
}
```

`message.text` must be a non-empty string. `message.from.username` is
optional and defaults to `telegram`. The adapter submits:

- title: `Telegram message`;
- description: `message.text`;
- requested-by: `telegram:<username>`;
- provenance source: `telegram`.

It returns `201` with the normal `TaskResponse`. Disabled integrations return
`404`; a wrong configured secret returns `401`; missing or invalid
`message.text` returns `422`.

Example:

```sh
curl -X POST http://localhost:8000/webhooks/telegram \
  -H "X-HAPA-Webhook-Secret: replace-with-a-long-random-secret" \
  -H "Content-Type: application/json" \
  -d '{"message":{"text":"Investigate checkout","from":{"username":"alice"}}}'
```

The endpoint is a payload normalizer, not a full Telegram Bot API client. Bot
registration, Telegram's webhook configuration, and outbound replies are
outside the current adapter.

## Integration and deployment notes

1. Replace the development JWT secret before deploying.
2. Use TLS for browser, SSE, WebSocket, and webhook traffic.
3. Keep webhook secrets separate from the JWT secret and rotate them
   independently.
4. Restrict `/api/v1/ws/telemetry` at the network or reverse-proxy layer until
   application-level WebSocket authentication is added.
5. Persist and reconcile event history with
   `GET /api/v1/tasks/{task_id}/events` because realtime delivery is
   in-process, non-replaying, and can drop messages for slow consumers.
