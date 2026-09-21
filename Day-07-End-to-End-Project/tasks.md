# Day 7 — Build Session Tasks

You have 15 minutes. Work in pairs. Each task has an explicit acceptance
criterion. Mark them off as you go.

## Task 1 — Agent Foundation (Planner)

**File:** `starter-code/agents/graph.py`

Add a Planner node that takes the user query and returns a plan
(list of agent names to invoke: `knowledge`, `ticket`, `escalation`).

**Acceptance:** A query like "Tell me about VPN and check my ticket"
returns `["knowledge", "ticket"]`.

## Task 2 — Knowledge Agent

**File:** `starter-code/tools/tools.py`

Wire `search_docs` so it returns text + citations from `rag/data/*.txt`.

**Acceptance:** Calling `search_docs("VPN drops")` returns text mentioning
VPN with at least one citation.

## Task 3 — Ticket Agent

**File:** `starter-code/tools/tools.py`

Implement `get_ticket_status` and `create_ticket`. `create_ticket` must
append to `PENDING_WRITES` (HITL gate).

**Acceptance:** `create_ticket(...)` returns `status: "pending_approval"`
and the ticket appears in `PENDING_WRITES`.

## Task 4 — Orchestration

**File:** `starter-code/agents/graph.py`

Build the LangGraph workflow:

```
START → Planner → (Knowledge || Ticket || Escalation) → Summarize → Reviewer → END
```

The Reviewer should route back to Summarize on `NEEDS_WORK`.

**Acceptance:** Running `python graph.py` produces a final `draft` field
that mentions at least one of the worker agents' results.

## Task 5 — Human Approval

**File:** `starter-code/api/app.py`

Add a `/approvals/pending` endpoint that returns `PENDING_WRITES` and a
`/approvals/{ticket_id}/approve` endpoint that removes the entry.

**Acceptance:** After calling `/support` with a "create ticket" query,
the pending ticket appears in `/approvals/pending`.

## Task 6 — Error Handling

**File:** `starter-code/api/app.py` and `starter-code/agents/graph.py`

- Wrap every tool call in a try/except. On failure, append an error to
  the state and continue (don't crash the run).
- Add a `max_iterations` cap on the review loop (default: 3).

**Acceptance:** A query that triggers a tool failure still produces a
final response with an explanation.

## Task 7 — API + Observability

**File:** `starter-code/api/app.py`

- POST `/support` returning `{trace_id, answer, citations, tool_calls,
  tokens, cost_usd}`.
- Log every LLM call and tool call with `request_id`.
- Enforce a per-user budget cap (`BUDGET_USD = 0.50`).

**Acceptance:** Two consecutive requests from the same user exceed the
budget → the second returns `429`.

## Stretch Goals

- Replace the mock `search_docs` with a real Chroma retrieval.
- Add SSE streaming so the client sees events as they happen.
- Wire Langfuse traces for every LLM call.
- Add a `/support/stream` SSE endpoint.

## Submission Checklist

- [ ] All 7 tasks done
- [ ] `pytest starter-code/tests/` passes
- [ ] `curl -X POST /support` returns a structured response
- [ ] A "create ticket" query lands in `/approvals/pending`
- [ ] The Reviewer loops back at least once during a NEEDS_WORK run
