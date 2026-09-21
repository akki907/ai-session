"""
Day 4 — LangGraph: parallel research → summary → review (with optional loop).

This demo shows the *graph shape* (parallel fan-out, fan-in, conditional
looping) without touching the LLM. To plug in real LLM calls, replace
each node body with a ``get_client().chat.completions.create(...)`` call
and import the model name from ``llm_config``.

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run multi_agent.py
"""
import sys
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

# Importing llm_config exports proxy env vars so any later LLM call
# inherits the bifrost / OpenAI configuration automatically.
sys.path.insert(0, str(Path(__file__).parent))
import llm_config  # noqa: F401


class S(TypedDict):
    question: str
    web: str
    github: str
    docs: str
    draft: str
    review: str


def web_node(s):    s["web"]    = f"[WEB] findings on: {s['question']}"
def github_node(s): s["github"] = f"[GH]  findings on: {s['question']}"
def docs_node(s):   s["docs"]   = f"[DOCS] findings on: {s['question']}"


def summarize(s):
    s["draft"] = (
        f"Summary based on:\n  - {s['web']}\n  - {s['github']}\n  - {s['docs']}"
    )
    return s


def review(s):
    s["review"] = "APPROVED"  # try setting to "NEEDS_WORK" to test the loop
    return s


def should_continue(s):
    return "summarize" if s["review"] == "NEEDS_WORK" else END


g = StateGraph(S)
g.add_node("web", web_node)
g.add_node("github", github_node)
g.add_node("docs", docs_node)
g.add_node("summarize", summarize)
g.add_node("review", review)

g.add_edge(START, "web")
g.add_edge(START, "github")
g.add_edge(START, "docs")
g.add_edge(["web", "github", "docs"], "summarize")
g.add_edge("summarize", "review")
g.add_conditional_edges("review", should_continue, {"summarize": "summarize", END: END})

app = g.compile()
result = app.invoke({"question": "What is agent observability?"})

print("=== FINAL ===")
for k, v in result.items():
    print(f"{k}: {v}")
