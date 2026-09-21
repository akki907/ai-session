"""
Day 3 — Embedding generation.

Takes chunks from the ingestion step, calls the embedding model
(default: ``text-embedding-3-small``), and prints the resulting vectors
(first 5 dims) plus a similarity demo.

Setup:
    uv sync
    cp .env.example .env    # bifrost vars are pre-filled
Run:
    uv run embed.py
"""
import sys
from pathlib import Path

import numpy as np

# Allow `from llm_config import ...` regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_client

client = get_client()
EMBED_MODEL = "text-embedding-3-small"


def embed(texts):
    """Embed a list of texts -> (n, d) matrix."""
    vecs = []
    for t in texts:
        v = client.embeddings.create(model=EMBED_MODEL, input=t).data[0].embedding
        vecs.append(v)
    return np.array(vecs)


def cosine_sim(a, b):
    """Pairwise cosine similarity."""
    a_n = a / np.linalg.norm(a, axis=1, keepdims=True)
    b_n = b / np.linalg.norm(b, axis=1, keepdims=True)
    return a_n @ b_n.T


def main():
    # Lazy-import the ingestion helpers (sibling module).
    sys.path.insert(0, str(Path(__file__).parent))
    from ingest import read_docs, chunk

    docs = read_docs(Path(__file__).parent.parent / "data")
    chunks = []
    for d in docs:
        chunks.extend(chunk(d["text"]))

    print(f"Embedding {len(chunks)} chunks...")
    matrix = embed(chunks[:5])  # demo on first 5 to keep cost low
    print(f"Vector shape: {matrix.shape}")

    q = "How many vacation days do I get per year?"
    qv = embed([q])
    sims = cosine_sim(qv, matrix)[0]
    print(f"\nSimilarity for query: {q!r}")
    for i, s in sorted(enumerate(sims), key=lambda x: -x[1]):
        print(f"  chunk {i}: {s:.3f}  -> {chunks[i][:60]!r}...")


if __name__ == "__main__":
    main()
