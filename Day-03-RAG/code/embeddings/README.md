# embeddings — vectorize chunks

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
uv run embed.py
```


## Notes

Embeds each chunk via OpenAI's `text-embedding-3-small` and stores the vectors in a local numpy cache. The retrieval step consumes this cache.

## Why uv

- **Fast** — installs in seconds, not minutes.
- **Reproducible** — `uv.lock` pins every transitive dep.
- **Per-demo isolation** — each code dir has its own `.venv/`, no conflicts.
- **Drop-in replacement** — `uv run` works like `python` but with the
  venv activated automatically.
