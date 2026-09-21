# Day 5 — Multi-Agent Systems · Notes

> Multiple specialized agents collaborating on complex tasks.

---

## 1. Single Agent vs Multi-Agent

### Single agent

```text
User → Agent (Search + Code + DB + API)
```

One LLM, many tools, one big context. Pros: simple. Cons: prompt bloat,
permission creep, hard to debug, context grows linearly with task complexity.

### Multi-agent

```text
User → Supervisor → [Research Agent, Coding Agent, Doc Agent]
```

Many specialized agents, each with its own instructions, tools, context.
Pros: separation of concerns, permission boundaries, parallel execution.
Cons: more LLM calls, more state, harder to debug.

---

## 2. Why Multi-Agent?

**Reasons to split:**

- **Responsibility separation** — research vs writing vs review.
- **Specialized tools** — one agent owns the Jira tools; another owns the
  RAG tools.
- **Specialized instructions** — a code-review agent has a different system
  prompt than a research agent.
- **Permission boundaries** — the ticket agent can create tickets; the
  research agent cannot.
- **Independent context** — each agent's context stays small and focused.
- **Parallel execution** — independent sub-tasks run at the same time.

**Reasons NOT to split:**

- More complexity to design, build, debug, and operate.
- More LLM calls → higher cost.
- More latency unless parallelized (and orchestration has its own cost).
- More state to manage (shared state, message passing, results).
- More failure modes (one agent can sabotage others).

### Rule of thumb

Start with a **single agent**. Split when:
- The system prompt exceeds ~3k tokens of instructions.
- Two distinct permission domains appear (read-only vs read-write).
- You need parallel execution of independent sub-tasks.
- Failure isolation would help (one agent failing shouldn't kill the run).

---

## 3. Planner / Worker Pattern

```text
Planner
  ↓
Task 1 → Worker A
Task 2 → Worker B
Task 3 → Worker C
  ↓
Aggregator
```

**Planner** decomposes a goal into independent tasks. **Workers** execute
each task. **Aggregator** combines results.

**Best for:** research tasks where each subtopic is independent.
("Tell me about authentication, authorization, and audit logging.")

---

## 4. Supervisor Pattern

```text
             Supervisor
          /      |       \
         ▼       ▼        ▼
    Research   Coding   Database
      Agent     Agent      Agent
```

The **supervisor** routes incoming requests to the right specialist, owns
the shared state, and decides when to finish.

**LangGraph implementation:** conditional edges from the supervisor node.

**Best for:** request-routing systems (helpdesk, triage, ops dashboards).

---

## 5. Reviewer Pattern

```text
Worker → Output → Reviewer → Pass → End
                         → Fail → Retry (with feedback)
```

The **reviewer** validates the worker's output against a rubric:
groundedness, completeness, format compliance, safety.

**Pro tip:** the reviewer should be a *different* LLM (or the same LLM
with a different prompt + strict schema). Never trust the producer to
self-grade reliably.

**Best for:** content generation, code generation, any output that needs
quality control before being shown to a user.

---

## 6. Sequential vs Parallel Execution

### Sequential

```text
Agent A → Agent B → Agent C
```

Use when each stage depends on the previous. Latency = sum of all stages.

### Parallel (fan-out / fan-in)

```text
Planner ──┬── Agent B ──┐
          └── Agent C ──┴── Aggregator
```

Use when tasks are independent. Latency ≈ slowest single agent.

**In LangGraph:** use `Send` or a list of conditional edges from the
Planner node. All parallel branches must converge before the next stage.

---

## 7. Shared State + Communication

Agents share state through one of:

| Mechanism | Pros | Cons |
|-----------|------|------|
| **Shared state object** (TypedDict) | Simple, single source of truth | Grows unbounded |
| **Messages on a queue** | Async-friendly, decouples agents | Needs broker (Redis, RabbitMQ) |
| **Task results JSON** | Explicit, debuggable | Schema maintenance |
| **External store** (DB) | Survives restarts, scales | Latency, consistency |

### Example message format

```json
{
  "task_id": "research-123",
  "agent": "web-researcher",
  "status": "completed",
  "result": "..."
}
```

### State bloat

Shared state grows. **Cap it.** Summarize messages when they exceed N
tokens. Persist only what's needed for downstream agents. Use a vector
store for "memory" instead of stuffing everything into the state.

---

## 8. Failure Handling + Retry

```text
Agent → Tool → Failure?
                ├── No → Continue
                └── Yes → Retry (max 3, exp backoff) → Fallback (cached/default) → Human
```

### What to retry

- Transient: network timeouts, 5xx, rate limits (429).
- Tool-specific: API says "please retry" in the error.

### What NOT to retry

- Validation errors (4xx except 429).
- Permission denied (will fail every time).
- Destructive actions (be careful).
- Hallucinated tool calls (don't compound the error).

### Patterns

- **Retry with exponential backoff** — start at 1s, double, cap at 10s.
- **Jitter** — randomize the delay so retries don't synchronize.
- **Circuit breaker** — after N failures in a window, stop calling the tool
  entirely for K seconds.
- **Fallback value** — return a stale cached value, or a clear "I don't know."
- **Human escalation** — last resort. Pause the run; notify a human.

---

## 9. Common Failure Modes

- **Infinite loops** — Reviewer always says NEEDS_WORK. Cap the loop
  iteration count.
- **Conflicting agent results** — Agent A says X, Agent B says ¬X. Add an
  arbiter node (or a Reviewer) that picks a winner.
- **Runaway cost** — one user triggers 1000 parallel research agents.
  Per-user budget cap. Per-run cap. Circuit breaker.
- **Lost context** — shared state grows but agents forget what was decided.
  Explicit `summary` field; periodic summarization.
- **Permission leakage** — the Researcher agent accidentally calls
  `create_ticket`. Per-agent tool allowlists.
- **Latency cliffs** — sequential agents + retries = minutes per request.
  Parallelize where possible; cap retries; cache.

---

## 10. Autonomous Research Agent — Reference Architecture

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

Three independent research agents run in parallel. The Summarizer
combines their findings. The Reviewer validates groundedness and
format. The whole thing should finish in 15–30s.

---

## Bridge to Day 6

Tomorrow we wrap this in production concerns: FastAPI, SSE streaming,
retries, observability, security, evaluation. The multi-agent graph is
the engine; the API is the chassis.
