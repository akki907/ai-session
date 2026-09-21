# ingestion — chunk and load documents

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
uv run ingest.py
```


## Notes

Reads .txt files from `../data/`, splits into fixed-size chunks with overlap, and prints chunk counts. The output feeds the embeddings step.

## Why uv

- **Fast** — installs in seconds, not minutes.
- **Reproducible** — `uv.lock` pins every transitive dep.
- **Per-demo isolation** — each code dir has its own `.venv/`, no conflicts.
- **Drop-in replacement** — `uv run` works like `python` but with the
  venv activated automatically.
