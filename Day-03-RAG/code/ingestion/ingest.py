"""
Day 3 — Document ingestion.

Reads .txt and .md files from data/, splits them into chunks, and prints
the chunks with their metadata. The output of this step is fed into the
embeddings stage.

Setup:
    pip install tiktoken
Run:
    python ingest.py
"""
from pathlib import Path
import re

DATA_DIR = Path(__file__).parent.parent / "data"


def read_docs(directory: Path) -> list[dict]:
    docs = []
    for fp in sorted(directory.glob("*.txt")):
        docs.append({"path": str(fp), "text": fp.read_text()})
    return docs


def chunk(text: str, size: int = 500, overlap: int = 80) -> list[str]:
    """Fixed-size chunker with overlap."""
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += size - overlap
    return chunks


def chunk_by_heading(text: str) -> list[dict]:
    """Heading-aware chunker — splits on section markers."""
    sections = re.split(r'\n(?=Section \d)', text)
    return [{"heading": s.splitlines()[0] if s else "", "text": s.strip()}
            for s in sections if s.strip()]


def main():
    docs = read_docs(DATA_DIR)
    print(f"Found {len(docs)} documents in {DATA_DIR}")
    total_chunks = 0
    for doc in docs:
        chunks = chunk(doc["text"])
        print(f"  {doc['path']}: {len(chunks)} fixed-size chunks")
        total_chunks += len(chunks)
    print(f"\nTotal chunks ready for embedding: {total_chunks}")


if __name__ == "__main__":
    main()
