# Day 7 — End-to-End Enterprise Agent · Architecture

## High-Level View

```
                         User
                          │
                          ▼
                    API Gateway
                          │
                          ▼
                   Planner Agent
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        Knowledge      Ticket      Approval
          Agent         Agent        Agent
              │           │           │
              ▼           ▼           ▼
             RAG       Ticket API   Human
                                      │
                                      ▼
                            Reviewer Agent
                          ▼
                    Final Response
```

## Component Map

| Component | File | Responsibility |
|-----------|------|----------------|
| API | `starter-code/api/app.py` | FastAPI service, SSE streaming, approvals dashboard |
| Orchestration | `starter-code/agents/graph.py` | LangGraph workflow, 5-agent fan-out |
| Tools | `starter-code/tools/tools.py` | RAG retrieval, Jira stubs, escalation |
| RAG ingestion | `starter-code/rag/ingest.py` | Read docs → chunk → embed (offline) |
| RAG data | `starter-code/rag/data/*.txt` | Sample IT/HR policies |
| Eval | `starter-code/tests/test_eval.py` | Tool tests + end-to-end graph tests |
| Spec | `architecture/specs/it-support-multi-agent.yaml` | Versioned agent config |

## Agent Topology

```
              Planner
              /  |  \
             ▼   ▼   ▼
        Knowledge Ticket Escalation
             \  |  /
              ▼ ▼ ▼
            Summarize
                │
                ▼
             Reviewer
                │
        ┌───────┴───────┐
        ▼               ▼
    APPROVED       NEEDS_WORK
        │               │
        ▼               ▼ (loop back)
      HitlGate
        │
        ▼
   Final Response
```

## Data Flow

1. **Request received** — `app.py` POSTs to `/support`.
2. **Planner runs** — emits a plan: `[knowledge]` / `[ticket]` / `[escalation]` (any combination).
3. **Worker agents run in parallel** — each calls its tool.
4. **Summarize merges** — combines knowledge + ticket info + escalation into a draft.
5. **Reviewer validates** — emits `APPROVED` or `NEEDS_WORK` (loops back).
6. **HITL gate** — if the draft requested `create_ticket`, the API layer pauses until a human approves.
7. **Response streamed** — final answer + citations + tool history sent via SSE.

## Why These Design Decisions

### Why LangGraph, not CrewAI?

We need parallel fan-out from the Planner and a conditional loop
(Reviewer → Summarize if NEEDS_WORK). CrewAI's `Process.sequential`
doesn't support these directly.

### Why a Reviewer agent?

The first draft often has unsupported claims. The Reviewer catches them
and routes back to Summarize with feedback. In production this can be
an LLM-as-judge with a strict rubric.

### Why HITL on `create_ticket`?

Writes to external systems must be auditable. A single wrong ticket can
break dashboards. HITL = a 1-hour delay vs a 4-hour cleanup.

### Why a per-user budget cap?

LLM costs can run away. One user can burn the entire daily budget in
minutes. Budget cap = circuit breaker.

## Production-Readiness Checklist

- [ ] Replace mock tools with real MCP servers
- [ ] Replace in-memory state with Postgres + Redis
- [ ] Add OAuth2 + per-tenant auth
- [ ] Wire Langfuse + OpenTelemetry into every LLM and tool call
- [ ] Wrap in Temporal for durable execution
- [ ] Add CI: run `tests/test_eval.py` on every PR
- [ ] Add dashboards: cost, latency, success rate, eval scores
