"""
Day 4 — LangChain building blocks.

LangChain provides composable pieces: models, prompts, tools, retrievers,
output parsers. This file shows how they fit together.

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run basic_components.py
"""
import sys
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Allow `from llm_config import ...` regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_model  # noqa: F401  (also exports proxy env vars)

llm = ChatOpenAI(model=get_model(), temperature=0.2)


# --- Output parser: enforce JSON schema ---
class TicketTriage(BaseModel):
    intent: str = Field(description="One of: vpn_issue, password_reset, billing, hardware, software, other")
    priority: int = Field(description="1 (urgent) to 3 (low)")
    draft_reply: str = Field(description="A short, friendly response (1-3 sentences)")


parser = JsonOutputParser(pydantic_object=TicketTriage)


# --- Prompt template ---
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an IT support triage analyst.\n{format_instructions}"),
    ("user", "{query}"),
]).partial(format_instructions=parser.get_format_instructions())


# --- Compose ---
chain = prompt | llm | parser


def triage(query: str) -> dict:
    return chain.invoke({"query": query})


if __name__ == "__main__":
    for q in ["VPN keeps dropping every 5 minutes",
              "I forgot my Windows password"]:
        print(f">> {q}")
        print(f"   {triage(q)}")
