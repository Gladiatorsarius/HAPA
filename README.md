# HAPA

HAPA exposes a FastAPI gateway for task orchestration, approvals, and realtime
telemetry.

## Configuration

The default configuration is in [`config/settings.yaml`](config/settings.yaml).
Set `storage.database_url` to a durable SQLite URL such as
`sqlite:///artifacts/hapa.db`. Configure `auth.issuer_url`, `auth.audience`,
and `auth.jwt_secret` for the JWT issuer used by your deployment. The
development secret in the checked-in example must be replaced in production.
The API listens on `api.host` and `api.port`.

Run locally with:

```sh
./scripts/entrypoint.sh
```

Or run the container:

```sh
docker compose up --build
```

## API usage

For the complete HTTP, SSE, WebSocket, chat, callback, and recurring schedule
reference, see [`api.md`](api.md).

Task, chat, approval, and event routes under `/api/v1` require an OAuth/OIDC
bearer token. The aggregate telemetry endpoint is public, and the telemetry
WebSocket currently does not validate bearer tokens. Tokens
must contain the configured issuer and audience claims plus one of:
`hapa:read`, `hapa:write`, or `hapa:approve`.

Create a task:

```sh
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $HAPA_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Add login","description":"Implement and test login","requested_by":"web"}'
```

Applications can poll `GET /api/v1/tasks/{task_id}` or consume
`GET /api/v1/tasks/{task_id}/events/stream` (SSE). Interactive clients can
subscribe to `WS /api/v1/ws/telemetry?task_id={task_id}`. Approval-gated tasks
appear at `GET /api/v1/approvals` and require an explicit approve or reject
request with the `hapa:approve` scope. Every task response includes its
lineage and provenance (`source`, `actor`, and `received_at`) so requests can
be traced across tiers. Rejected approvals cancel the task and preserve the
reviewer's comment.

Quality gates validate all cross-tier hand-offs with strict Pydantic models.
Workspace diffs and test reports are JSON-round-trippable structured
artifacts; incomplete test counts or malformed artifacts block progression.

`GET /health/live` is a public liveness check; `GET /health/ready` checks the
configured durable store. Discord clients use the normal authenticated `/api/v1/chat/messages` contract
like the website. Completion follow-ups can be read from durable events/SSE or
delivered to an optional `callback_url`; there are no provider-specific
Discord or Telegram webhook routes.