# IT Support Multi-Agent — starter code (Day 7)

This is the end-of-week capstone. It uses [uv](https://docs.astral.sh/uv/)
for dependency management.

## Setup

```bash
# 1. Install uv (skip if already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. From this directory, sync everything (creates .venv/)
uv sync

# 3. Set environment variables
cp .env.example .env
$EDITOR .env
```

## Run the demo

```bash
# Ingest sample policies into Chroma
uv run python rag/ingest.py --dir data

# Start the API
uv run --with uvicorn uvicorn api.app:app --reload --port 8000

# In another terminal, talk to it
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "My VPN keeps disconnecting", "user_id": "u-42"}'
```

## Run tests

```bash
uv run pytest -v tests/
```

## Structure

| Path | Purpose |
|------|---------|
| `api/` | FastAPI service: `/invoke`, `/invoke/stream`, `/approvals` |
| `agents/` | LangGraph state machine for the planner / worker / reviewer |
| `tools/` | `search_docs`, `get_ticket_status`, `create_ticket`, `escalate_to_human` |
| `rag/` | Ingest + retrieval over ChromaDB |
| `tests/` | Pytest suite for the agent and tools |

## Day 7 architecture

```text
User → FastAPI → LangGraph
              ├─ Planner   (decompose)
              ├─ Retriever (search_docs)
              ├─ Ticket    (get_ticket_status)
              └─ Reviewer  (validate)
                  ↓
             Final Answer (with citations + ticket ids)
```

## Why uv

- **Fast** — installs in seconds, not minutes.
- **Reproducible** — `uv.lock` pins every transitive dep.
- **Workspace-friendly** — `uv sync` reads every `pyproject.toml`
  in sub-dirs.
- **Drop-in replacement** — `uv run` works like `python` but with
  the venv activated automatically.

See `../tasks.md`, `../requirements.md`, and `../architecture.md` for
the full Day 7 spec.
