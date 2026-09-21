#!/usr/bin/env bash
# Multi-step runner for the IT-support-multi-agent starter-code (Day 7 capstone).
# Sub-commands: setup | ingest | serve | test | help
# Each subcommand runs in the project's local virtualenv and loads .env.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV_PY="$HERE/.venv/bin/python"

usage() {
  cat <<EOF
Usage: $0 <subcommand> [args]

Sub-commands:
  setup    uv sync (create .venv/ + install deps) and copy .env.example to .env
  ingest   Run the RAG ingestion step:  python rag/ingest.py --dir data
  serve    Start the FastAPI service:   python -m uvicorn api.app:app --reload --port 8000
  test     Run the pytest suite:        python -m pytest -v tests/
  help     Show this message

Any extra args are forwarded to the underlying tool.
EOF
}

require_venv() {
  if [[ ! -x "$VENV_PY" ]]; then
    echo "error: $VENV_PY not found. Run '$0 setup' first." >&2
    exit 1
  fi
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  setup)
    echo "[setup] uv sync (creates .venv/ if missing)"
    uv sync
    if [[ ! -f "$HERE/.env" ]]; then
      if [[ -f "$HERE/.env.example" ]]; then
        cp "$HERE/.env.example" "$HERE/.env"
        echo "[setup] copied .env.example -> .env (edit it to add BIFROST_API_KEY)"
      else
        echo "warning: no .env.example found; create .env manually" >&2
      fi
    else
      echo "[setup] .env already exists, leaving it alone"
    fi
    ;;

  ingest)
    require_venv
    exec "$VENV_PY" "$HERE/rag/ingest.py" "$@"
    ;;

  serve)
    require_venv
    exec "$VENV_PY" -m uvicorn api.app:app --reload --port 8000 "$@"
    ;;

  test)
    require_venv
    exec "$VENV_PY" -m pytest -v tests/ "$@"
    ;;

  help|-h|--help)
    usage
    ;;

  *)
    echo "error: unknown subcommand '$cmd'" >&2
    usage >&2
    exit 1
    ;;
esac
