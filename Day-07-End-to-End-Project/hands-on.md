# Day 7 — Hands-on · End-to-End Enterprise Agent

> 15-minute build session. Work in pairs. Each task has an explicit
> acceptance criterion.

## Goal

By the end of this session, you will have a working multi-agent system
that you can hit with `curl` and watch return a structured response with
citations, tool calls, and a HITL gate.

## Prerequisites

```bash
cd Day-07-End-to-End-Project/starter-code
pip install -r requirements.txt
pytest tests/ -v   # should pass before you start
```

## Tasks

### Task 1 — Run the starter

```bash
uvicorn api.app:app --reload
```

In another terminal:

```bash
curl -X POST localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u-42","query":"My VPN keeps dropping"}'
```

**Acceptance:** you get back `{trace_id, answer, citations, tool_calls,
tokens, cost_usd}`.

### Task 2 — Trigger the HITL gate

```bash
curl -X POST localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u-42","query":"Open a ticket: laptop fan is loud"}'
curl localhost:8000/approvals/pending
```

**Acceptance:** the new ticket appears in `/approvals/pending` with
`status: "pending_approval"`.

### Task 3 — Approve a pending ticket

```bash
curl -X POST localhost:8000/approvals/T-1100/approve?approve=true
```

**Acceptance:** the ticket disappears from `/approvals/pending`.

### Task 4 — Trigger the escalation path

```bash
curl -X POST localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u-42","query":"This is critical, get a human on it NOW"}'
```

**Acceptance:** the response mentions "Incident INC-..." and the
`tool_calls` list contains `escalate_to_human`.

### Task 5 — Add a new tool

Add a `send_slack_notification` tool to `tools/tools.py`:

```python
def send_slack_notification(channel: str, message: str) -> dict:
    """Mock Slack notification."""
    return {"channel": channel, "ts": "1234567890.123456", "message": message}
```

Wire it into the `escalation_node` in `agents/graph.py` so that an
escalation also posts to `#it-help`.

**Acceptance:** a critical query results in BOTH an Incident ID AND a
Slack notification in the response.

### Task 6 — Add a tool guardrail

Add a check that **only** the `ticket` agent can call `create_ticket`.
If any other agent tries, raise an error and stop the run.

```python
ALLOWED_TOOLS = {
    "planner": [],
    "knowledge": ["search_docs"],
    "ticket": ["get_ticket_status", "create_ticket"],
    "escalation": ["escalate_to_human", "send_slack_notification"],
    "reviewer": [],
}
```

**Acceptance:** manually calling `create_ticket` from the `knowledge`
agent raises `PermissionError`.

### Task 7 — Run the eval suite

```bash
pytest tests/ -v
```

**Acceptance:** all tests pass.

## Stretch Goals

- Replace the mock `search_docs` with a real Chroma retrieval.
- Add SSE streaming so the client sees events as they happen.
- Wire Langfuse traces for every LLM call.
- Add a `/support/stream` SSE endpoint that emits `planning`,
  `tool_call`, `tool_result`, `final` events.

## Submission Checklist

- [ ] All 7 tasks done
- [ ] `pytest starter-code/tests/` passes
- [ ] `curl -X POST /support` returns a structured response
- [ ] A "create ticket" query lands in `/approvals/pending`
- [ ] The Reviewer loops back at least once during a NEEDS_WORK run
- [ ] The tool guardrail blocks unauthorized tool calls

## What You Now Have

A working multi-agent IT support system that demonstrates every concept
from Days 1–6:

- **Day 1** — LLM API calls, structured output, generation parameters.
- **Day 2** — Tool calling, agent loop, guardrails, HITL gate.
- **Day 3** — RAG retrieval with citations.
- **Day 4** — LangGraph orchestration, MCP-ready tool abstraction.
- **Day 5** — Multi-agent topology: Planner → Workers → Reviewer.
- **Day 6** — FastAPI service, SSE, traces, retries, budget caps.

**You are production-ready.** Take this code, swap the mock tools for
real MCP servers, wire Langfuse, and deploy.
