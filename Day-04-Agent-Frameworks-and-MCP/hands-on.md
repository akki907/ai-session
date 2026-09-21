# Day 3 — Hands-on (15 min)

## Goal
Compare two frameworks side-by-side: **CrewAI** for role-based collaboration and **LangGraph** for parallel multi-agent flows.

## Setup
```bash
pip install crewai langgraph langchain-openai
```

## Steps

### Part A — CrewAI research crew (8 min)
1. Open `code/day3_crewai_research.py`.
2. The crew has 3 agents: Planner, Researcher, Reviewer.
3. Replace `fake_search` with a stub that returns canned strings.
4. Run on topic: `"agent observability"`.
5. Confirm output is structured (Planner's outline → Researcher's notes → Reviewer's verdict).

### Part B — LangGraph parallel flow (7 min)
1. Open `code/day3_langgraph_multi.py`.
2. Read the 3 START edges → parallel web/github/docs research.
3. Replace each real agent with a mock (returns canned string).
4. Add a 4th node: `FactChecker`, called after `Reviewer`.
5. Bonus: add a loop edge: if Reviewer says `NEEDS_WORK`, route back to Summarizer.

## Expected Output (CrewAI)
```
Planner: 1. What is observability?  2. Which tools?  3. Which patterns?
Researcher: Observability spans + cost tracking + evaluation harnesses (3 sources).
Reviewer: All claims grounded. Output is correct.
```

## Expected Output (LangGraph)
```
=== FINAL ===
Web: ...   GitHub: ...   Docs: ...
Summary: ...
Review: APPROVED.
```

## Common Mistakes
- ❌ Trying to do parallel research with CrewAI's `Process.sequential`. Use LangGraph.
- ❌ Loops without termination. Reviewer rejects forever.
- ❌ Mutable global state. Use thread_id or run_id.
