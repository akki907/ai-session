# Day 5 — Hands-on · Build a Planner / Worker / Reviewer

> 15-minute build session. Work in pairs.

## Goal

Build a 3-agent research system with parallel fan-out, aggregation, and
review.

## Steps

### 1. Define the shared state

```python
from typing import TypedDict

class State(TypedDict):
    question: str
    web: str
    github: str
    docs: str
    draft: str
    review: str
```

### 2. Implement 3 worker nodes

Each worker simulates a search. In production, each one calls a different
retrieval backend.

```python
def web_node(s):    s["web"]    = f"[WEB] findings on: {s['question']}"
def github_node(s): s["github"] = f"[GH]  findings on: {s['question']}"
def docs_node(s):   s["docs"]   = f"[DOCS] findings on: {s['question']}"
```

### 3. Implement the Aggregator

```python
def summarize(s):
    s["draft"] = (
        f"Summary based on:\n"
        f"  - {s['web']}\n  - {s['github']}\n  - {s['docs']}"
    )
    return s
```

### 4. Implement the Reviewer

```python
def review(s):
    # In real code: LLM-as-judge with rubric
    s["review"] = "APPROVED"   # try "NEEDS_WORK" to test the loop
    return s
```

### 5. Wire it in LangGraph

```python
from langgraph.graph import StateGraph, START, END

g = StateGraph(State)
g.add_node("web", web_node)
g.add_node("github", github_node)
g.add_node("docs", docs_node)
g.add_node("summarize", summarize)
g.add_node("review", review)

# Parallel fan-out
g.add_edge(START, "web")
g.add_edge(START, "github")
g.add_edge(START, "docs")

# Fan-in to aggregator
g.add_edge(["web", "github", "docs"], "summarize")

# Conditional loop: APPROVED → END, NEEDS_WORK → summarize (loop back)
g.add_edge("summarize", "review")
g.add_conditional_edges("review",
    lambda s: "summarize" if s["review"] == "NEEDS_WORK" else END,
    {"summarize": "summarize", END: END})

app = g.compile()
result = app.invoke({"question": "What is agent observability?"})
```

### 6. Test it

```bash
python multi_agent.py
```

You should see the final state with `draft`, `review: APPROVED`, and the
three worker outputs merged.

## Stretch Goals

- Replace the simulated workers with real `search_web`, `search_github`,
  `search_docs` tools.
- Add a Planner node that decomposes the question into 3 sub-questions,
  one per worker.
- Add a `max_iterations=3` cap so the Reviewer can't loop forever.
- Log every node entry/exit with timestamps.

## What You Now Have

A graph with **parallel fan-out, fan-in aggregation, conditional
looping**. The same shape scales to production multi-agent systems.
