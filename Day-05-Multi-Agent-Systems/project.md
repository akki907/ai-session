# Day 5 — Project · Autonomous Research Agent

## Objective

Build an autonomous research agent with three independent workers running
in parallel, a summarizer that aggregates their findings, and a reviewer
that validates the result.

## Architecture

```text
                 Planner
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Web Agent   GitHub Agent  Docs Agent
       │            │            │
       └────────────┼────────────┘
                    ▼
                Summarizer
                    ▼
                 Reviewer
                    ▼
              Final Answer
```

## Agents

| Agent | Responsibility | Tools |
|-------|----------------|-------|
| **Planner** | Decompose the question into 3 sub-questions | none |
| **Web Agent** | Search the web | `search_web` |
| **GitHub Agent** | Search GitHub repos/issues | `search_github` |
| **Docs Agent** | Search internal docs | `search_docs` |
| **Summarizer** | Merge the three findings into a draft | none |
| **Reviewer** | Validate groundedness, completeness, format | none |

## Acceptance Criteria

1. The three workers run in parallel (not sequentially).
2. The Summarizer waits for all three before producing a draft.
3. The Reviewer's verdict is deterministic and auditable.
4. On `NEEDS_WORK`, the loop returns to Summarize with feedback (max 3 times).
5. Wall-clock latency < 30 seconds for the full run.

## Project Mapping

| Concept | Implementation |
|---------|---------------|
| Planner | Question decomposition |
| Worker | Specialized research (web, github, docs) |
| Supervisor | (Implicit — LangGraph orchestrator) |
| Reviewer | Quality validation |
| Parallel agents | Three workers running concurrently |
| Shared state | LangGraph State object |
| Retry | Loop back to Summarize on NEEDS_WORK |
| Delegation | Planner → Workers (via Send or list edges) |

## Stretch Goals

- Replace the simulated searches with real MCP tool calls.
- Add a Planner LLM call that emits the 3 sub-questions via structured output.
- Add per-worker timeout + fallback.
- Add a cost cap: abort if total LLM cost > $0.10.
