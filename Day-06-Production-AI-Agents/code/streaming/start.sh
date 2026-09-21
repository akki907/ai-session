#!/usr/bin/env bash
# Start the sse_endpoint:app FastAPI service using the project's local virtualenv.
# Loads .env (via llm_config.py -> python-dotenv), then runs uvicorn with auto-reload.
# The service is reachable at http://localhost:8001

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV_PY="$HERE/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "error: $VENV_PY not found. Create the venv with: uv sync" >&2
  exit 1
fi

if [[ ! -f "$HERE/.env" ]]; then
  echo "warning: $HERE/.env missing. Copy .env.example to .env and fill in BIFROST_API_KEY." >&2
fi

exec "$VENV_PY" -m uvicorn sse_endpoint:app --reload --port 8001 "$@"
