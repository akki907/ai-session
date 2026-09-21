"""
Day 6 — Ingest sample policies into Chroma (or any vector DB).

In production:
    - Use pgvector, Weaviate, or Qdrant
    - Add metadata filters per chunk (section, version, dept)
    - Re-ingest on every policy update

Run:
    python ingest.py --dir data
"""
import argparse
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def chunk(text: str, size: int = 500, overlap: int = 80) -> list[str]:
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += size - overlap
    return chunks


def ingest(directory: Path) -> int:
    total = 0
    for fp in directory.glob("*.txt"):
        text = fp.read_text()
        for idx, piece in enumerate(chunk(text)):
            print(f"  ingested: {fp.name}#{idx} ({len(piece)} chars)")
            total += 1
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=str(DATA_DIR))
    args = parser.parse_args()

    directory = Path(args.dir)
    if not directory.exists():
        directory.mkdir(parents=True)
        # write sample data
        (directory / "it-security.txt").write_text(
            "VPN Policy: Personal devices require MFA. Approved for use only "
            "with prior IT approval. Connection drops every 5 minutes often "
            "indicate a stale session token — reconnect via the IT VPN client.\n\n"
            "Password Policy: Passwords must be at least 14 characters and "
            "rotated every 90 days. MFA is mandatory for all production systems."
        )
        (directory / "it-handbook.txt").write_text(
            "Password Reset: Use the self-service portal at password.company.com. "
            "If MFA is locked, contact IT helpdesk.\n\n"
            "Hardware Request: Submit a ticket via the IT portal. Approval "
            "typically takes 2 business days."
        )
        (directory / "hr-handbook.txt").write_text(
            "Leave Policy: Full-time employees receive 25 vacation days per year, "
            "accrued at 2.08 days/month. Unused days roll over up to a maximum of 5.\n\n"
            "Sick Leave: Employees may take up to 10 sick days per year with no "
            "doctor's note required."
        )

    total = ingest(directory)
    print(f"\nIngested {total} chunks across {len(list(directory.glob('*.txt')))} collections.")


if __name__ == "__main__":
    main()
