#!/bin/sh

set -eu

: "${HAPA_WORKSPACE_ROOT:=.}"
: "${HAPA_SNAPSHOT_DIR:=${HAPA_WORKSPACE_ROOT}/artifacts/checkpoints}"
: "${HAPA_SCREENSHOT_DIR:=${HAPA_WORKSPACE_ROOT}/artifacts/screenshots}"
: "${HAPA_API_HOST:=0.0.0.0}"
: "${HAPA_API_PORT:=8000}"
: "${HAPA_API_LOG_LEVEL:=info}"

case "$HAPA_API_PORT" in
    ''|*[!0-9]*)
        printf '%s\n' "HAPA_API_PORT must be a positive integer" >&2
        exit 2
        ;;
    0)
        printf '%s\n' "HAPA_API_PORT must be greater than zero" >&2
        exit 2
        ;;
esac

mkdir -p "$HAPA_WORKSPACE_ROOT" "$HAPA_SNAPSHOT_DIR" "$HAPA_SCREENSHOT_DIR"

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

exec uvicorn src.main:app \
    --host "$HAPA_API_HOST" \
    --port "$HAPA_API_PORT" \
    --log-level "$HAPA_API_LOG_LEVEL"
