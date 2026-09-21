# mcp — minimal MCP-style server (educational)

This demo uses [uv](https://docs.astral.sh/uv/) for dependency management.

## Setup

```bash
# 1. Install uv (skip if already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Sync dependencies (creates .venv/ automatically)
uv sync

# 3. Set environment variables
cp .env.example .env
$EDITOR .env   # fill in OPENAI_API_KEY etc.
```

## Run the demo

```bash
uv run mcp_server.py
```


## Notes

Educational re-implementation of the MCP shape: a server that exposes a list of tools and dispatches calls. Real MCP uses JSON-RPC over stdio/HTTP — see `pip install mcp` and `mcp run` for production.

## Why uv

- **Fast** — installs in seconds, not minutes.
- **Reproducible** — `uv.lock` pins every transitive dep.
- **Per-demo isolation** — each code dir has its own `.venv/`, no conflicts.
- **Drop-in replacement** — `uv run` works like `python` but with the
  venv activated automatically.
