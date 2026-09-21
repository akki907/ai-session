"""
Day 3 — Minimal RAG: ingest policies into Chroma, then query them.

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run rag_pipeline.py
"""
import sys
from pathlib import Path

import chromadb

# Allow `from llm_config import ...` regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_client, get_model

client = get_client()
LLM_MODEL = get_model()
EMBED_MODEL = "text-embedding-3-small"

chroma = chromadb.PersistentClient(path="./db")
col = chroma.get_or_create_collection("policies")

DATA = Path(__file__).parent / "data" / "sample_policies.txt"

SAMPLE = """
Section 4.1 - Leave Policy
Full-time employees receive 25 vacation days per year, accrued at 2.08 days per month.
Unused days roll over up to a maximum of 5 days.

Section 4.2 - Sick Leave
Employees may take up to 10 sick days per year with no doctor's note required.

Section 4.3 - Parental Leave
New parents are entitled to 16 weeks of paid parental leave.

Section 5.1 - VPN Policy
Personal VPN access requires MFA. Approved from personal devices only with prior IT approval.
"""


def chunk(text: str, size: int = 400, overlap: int = 60) -> list[str]:
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += size - overlap
    return chunks


def ingest():
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(SAMPLE)
    pieces = chunk(SAMPLE)
    for idx, piece in enumerate(pieces):
        emb = client.embeddings.create(
            model=EMBED_MODEL, input=piece
        ).data[0].embedding
        col.add(
            documents=[piece],
            embeddings=[emb],
            ids=[f"policy-{idx}"],
            metadatas=[{"source": "hr-handbook.pdf", "chunk": idx}],
        )
    print(f"Ingested {len(pieces)} chunks.")


def ask(q: str, k: int = 3) -> str:
    qe = client.embeddings.create(
        model=EMBED_MODEL, input=q
    ).data[0].embedding
    res = col.query(query_embeddings=[qe], n_results=k)
    docs = res["documents"][0]
    ctx = "\n\n".join(docs)
    prompt = f"Answer using ONLY the context below.\n\nContext:\n{ctx}\n\nQuestion: {q}"
    return client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
    ).choices[0].message.content


if __name__ == "__main__":
    ingest()
    print("\n>> Q: How many vacation days do I have?")
    print(f"<< A: {ask('How many vacation days do I have?')}")
    print("\n>> Q: Can I use VPN from my personal laptop?")
    print(f"<< A: {ask('Can I use VPN from my personal laptop?')}")
