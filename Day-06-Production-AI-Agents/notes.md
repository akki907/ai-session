# Day 6 — Production AI Agents · Notes

> From prototype to production. Every concern that doesn't exist in a notebook.

---

## 1. Prototype vs Production

### Prototype

```text
User → Python Script → LLM → Answer
```

One file. No auth. No tracing. No retries. Works for the demo.

### Production

```text
Client
  ↓
API Gateway (auth, rate limit, TLS)
  ↓
Agent Service
  ↓
Orchestrator (LangGraph, durable)
  ↓
LLM + Tools + RAG + Memory
  ↓
External Systems (Jira, Slack, DB, ...)

+
Logs (structured, with request_id)
+
Metrics (latency, tokens, cost, success rate)
+
Traces (Langfuse, OpenTelemetry)
+
Evaluation (offline + online)
+
Security (auth, authz, PII, secrets)
```

Every box in the production diagram is a feature. Each one has its own
failure modes. This day covers the major ones.

---

## 2. API Deployment

### FastAPI is the de-facto standard

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RunReq(BaseModel):
    user_id: str
    message: str

class RunResp(BaseModel):
    answer: str
    tokens: int
    cost_usd: float

@app.post("/agent/run", response_model=RunResp)
def run(req: RunReq) -> RunResp:
    ...
```

### Endpoints a production agent API needs

| Endpoint | Purpose |
|----------|---------|
| `POST /agent/run` | Sync execution, returns when finished |
| `POST /agent/run-stream` | SSE streaming, returns events as they happen |
| `POST /agent/run-async` | Returns 202 + job_id, run in background |
| `GET /agent/runs/{id}` | Check status of async run |
| `GET /approvals/pending` | Human approver dashboard |
| `POST /approvals/{id}/approve` | Approver action |
| `GET /budget/{user_id}` | Per-user spend |
| `GET /healthz` | Liveness probe |

### Auth

- API key for service-to-service.
- OAuth2 + JWT for end-user requests.
- mTLS for internal service mesh.

Every endpoint must validate the caller. Unauthenticated agent endpoints
are how you become a $50,000 overnight news story.

---

## 3. Async Execution

Long-running agent tasks (research, document processing, multi-step
approval) should not block the HTTP request thread.

```text
Client → POST /execute → 202 Accepted (with run_id)
                            ↓
                       Background worker
                            ↓
                       Agent run
                            ↓
                       Store result
                            ↓
Client → GET /runs/{id} → status, result
```

Use Celery, RQ, Temporal, or your platform's job runner. The agent
service writes progress to a shared store; the client polls or subscribes.

---

## 4. SSE Streaming

Server-Sent Events give the client a continuous stream of updates without
WebSocket complexity.

```text
HTTP → SSE → Agent Events

event: planning
data: {"step": "decomposing query"}

event: tool_call
data: {"tool": "search_docs", "args": {"q": "VPN"}}

event: tool_result
data: {"tool": "search_docs", "result": "..."}

event: final
data: {"answer": "...", "citations": [...]}
```

### Why SSE

- **Perceived latency** — users see progress instead of a spinner.
- **Long-running support** — doesn't time out at 30s like a sync HTTP call.
- **Easy to implement** — one endpoint, one stream.
- **Works through HTTP proxies** — unlike WebSockets sometimes.

### Implementation

Use FastAPI's `StreamingResponse` with `media_type="text/event-stream"`.
Yield `data: {json}

` chunks.

---

## 5. Long-Running Workflows

A research-and-approval workflow might look like:

```text
Start Research → Search → Wait for Approval → Continue → Generate Report
```

Some steps take seconds. Some take hours (human approval). The naive
implementation keeps a Python process alive the whole time — fragile.

### Temporal

Temporal is the standard solution. It provides:

- **Durable execution** — workflow state persists across restarts.
- **Workflow state** — every step's result is checkpointed.
- **Retries** — automatic with exponential backoff.
- **Timeouts** — per-activity deadlines.
- **Recovery** — restart from the last checkpoint, not from scratch.
- **Long-running workflows** — workflows can pause for days.
- **Human approval pauses** — built-in `update_with_timeout` for signals.

### Conceptual architecture

```text
API
 ↓
Temporal Workflow (durable)
 ↓
Agent Orchestration
 ├── Search Activity
 ├── Tool Activity
 ├── Approval Activity (signals from humans)
 └── Finalization Activity
```

### LangGraph + Temporal

They are complementary, not competing:

- **LangGraph** → agent state and routing (in-memory graph).
- **Temporal** → durable workflow execution (survives restarts).

Wrap each LangGraph node in a Temporal activity. The graph becomes a
Temporal workflow. HITL pauses become Temporal signals.

---

## 6. Retry Strategy

### Retry appropriate transient failures

- Network timeout
- 5xx responses
- 429 rate-limit responses
- Brief service unavailability

### Don't retry

- 4xx (client error — the request is wrong, not the network)
- Authentication failures
- Permission denied
- Invalid request shape
- Destructive operations (idempotency unknown)

### Patterns

```python
@retry(
    wait=wait_exponential(min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
def call_with_retry():
    ...
```

Add **jitter** so retries don't synchronize. Add a **circuit breaker** so
a failing tool doesn't take down the whole run.

---

## 7. Observability

You can't operate what you can't see. Every production agent must emit:

### Logs

Structured logs with `request_id`, `user_id`, `agent`, `tool`, `latency`,
`tokens`, `cost`. Use JSON. Send to a central log aggregator.

### Metrics

| Metric | Why |
|--------|-----|
| `agent_run_total` | Request volume |
| `agent_run_duration_seconds` | Latency (p50, p95, p99) |
| `agent_run_errors_total` | Failure rate |
| `llm_tokens_total` | Token usage (input + output) |
| `llm_cost_usd_total` | Spend |
| `tool_calls_total` | Tool usage breakdown |
| `hitl_pending_count` | Pending approvals |

### Traces

Distributed traces (OpenTelemetry) propagate `request_id` through:

```text
Request → Agent → LLM Call → Tool Call → Tool Result → LLM Call → Response
```

Each span has: latency, attributes (model, tokens, cost), events
(retries, errors). Langfuse is the standard for LLM traces specifically.

---

## 8. Evaluation

### Offline eval

Run a fixed test set through the agent. Compare answers to a reference
set (human-labeled or LLM-as-judge).

### Online eval

On a sample of real traffic (say 1%), score the response with LLM-as-judge.
Track the score over time. Alert on regression.

### Regression suite

A CI test that runs on every PR. Same queries, same expected behavior.
Catches "we changed a prompt and now all answers are wrong."

### Human eval

Sample 0.1% of production traffic and have a human rate it. Most
accurate, most expensive, slowest feedback loop.

### What to evaluate

- **Correctness** — was the answer right?
- **Groundedness** — was it supported by retrieved evidence?
- **Tool selection** — did the agent choose the right tool?
- **Tool arguments** — were they correct?
- **Safety** — did it avoid unauthorized actions?
- **Cost** — how much did it spend?
- **Latency** — how long did it take?

---

## 9. Security

### Threats

| Threat | Mitigation |
|--------|-----------|
| Prompt injection | Input validation, output validation, isolation |
| PII leakage | Input redaction, output redaction, audit logs |
| Tool abuse | Per-agent tool allowlists, per-user permissions |
| Secret leakage | Env vars / secrets manager, never log tokens |
| Excessive permissions | Principle of least privilege |
| Untrusted tool output | Treat tool output as untrusted; never inject raw into system prompt |
| Denial of wallet | Per-user budget cap, per-run cap, circuit breakers |

### Principle

```text
Agent → Minimum Required Permissions → Allowed Tools
```

Every agent declares exactly what tools it can use and what permissions
those tools need. The orchestrator enforces this; the agent cannot
escalate.

---

## 10. Guardrails

Three layers:

```text
Input Guardrail
       ↓
Agent
       ↓
Tool Guardrail
       ↓
Output Guardrail
```

### Input guardrails

- PII detection + redaction.
- Prompt-injection detection.
- Topic blocklist ("salary", "SSN", ...).
- Length / format constraints.

### Tool guardrails

- Allowlist per agent.
- Per-user authorization.
- Schema validation on arguments.
- Rate limits per tool.

### Output guardrails

- JSON schema validation.
- PII redaction.
- Toxicity filter.
- Citation presence / accuracy check.

---

## 11. Cost Optimization

### Sources of cost

```text
LLM Calls (input + output tokens)
+
Embedding Calls (per chunk, per query)
+
Tool Calls (API costs, compute)
+
Infrastructure (compute, storage, network)
```

### Levers

- **Reduce unnecessary context.** Trim conversation history; don't send
  full docs.
- **Cache results.** Cache identical embeddings; cache frequent queries.
- **Parallelize.** Independent sub-tasks run at the same time.
- **Smaller models.** Use a smaller model for triage, a bigger one for
  synthesis.
- **Limit agent loops.** Cap `max_iterations`.
- **Reduce unnecessary tool calls.** Better tool descriptions; better
  planning.

---

## 12. Latency Optimization

### Sources

```text
LLM inference
+
RAG retrieval
+
Tool calls
+
Network
+
Sequential agents (if not parallelized)
```

### Levers

- Parallelize independent agents.
- Stream early (SSE — users see progress immediately).
- Cache retrievals (semantic cache).
- Use a smaller model for the first pass.
- Cap retries.

---

## Bridge to Day 7

Everything in these notes comes together in the capstone project: a
multi-agent IT Support system behind a FastAPI service, with SSE
streaming, Langfuse traces, retries, HITL, RAG, and eval.
