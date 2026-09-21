# Day 7 — End-to-End Enterprise Agent · Notes

> The capstone. Every concept from Days 1–6 appears in this one system.

---

## 1. Business Problem

Employees need help with:

- VPN issues
- Laptop issues
- Password problems
- Software installation
- Access requests
- Ticket status
- IT policies

The organization wants an AI-powered IT support platform that:

1. Understands the employee request.
2. Searches enterprise documentation.
3. Checks existing tickets.
4. Creates tickets when required.
5. Updates tickets when authorized.
6. Asks for human approval for sensitive operations.
7. Validates the final response.

---

## 2. Agents

### Planner Agent

Decomposes the user query into a list of sub-tasks. Decides which
specialist agents need to run.

```python
def planner(state):
    q = state["query"].lower()
    plan = []
    if any(w in q for w in ["policy", "rule", "guideline"]):
        plan.append("knowledge")
    if any(w in q for w in ["ticket", "status", "open", "create"]):
        plan.append("ticket")
    if any(w in q for w in ["urgent", "human", "manager", "critical"]):
        plan.append("escalation")
    state["plan"] = plan
    return state
```

In production: the Planner is an LLM call with structured output. The
planner prompt enumerates the available agents and asks the LLM to
produce a JSON list of which ones to run.

### Knowledge Agent

Searches documentation. Retrieves relevant policies. Returns sources.

```python
def knowledge_node(state):
    docs = search_docs(state["query"])  # RAG retrieval
    state["knowledge"] = docs["text"]
    state["citations"] = docs["citations"]
    return state
```

### Ticket Agent

Reads or creates Jira tickets.

```python
def ticket_node(state):
    if "create" in state["query"].lower():
        # HITL gate — append to PENDING_WRITES
        state["ticket_info"] = create_ticket(title=..., description=...)
    else:
        state["ticket_info"] = get_ticket_status(...)
    return state
```

### Approval Agent

Detects sensitive actions. Requests human approval. Pauses execution.

```python
# In app.py — outside the graph
def approval_gate(state):
    if state.get("requires_approval"):
        PENDING_WRITES.append(state["pending_ticket"])
        return {"status": "pending_approval"}
    return {"status": "approved"}
```

The agent graph **does not** call the approval directly. The API layer
intercepts `create_ticket` and pauses until a human approves via
`POST /approvals/{id}/approve`.

### Reviewer Agent

Validates the final response. Checks groundedness, completeness, format.
Routes back to Summarize on `NEEDS_WORK`.

```python
def review(state):
    has_citations = len(state["citations"]) > 0
    has_answer = bool(state["draft"])
    state["review"] = "APPROVED" if (has_citations and has_answer) else "NEEDS_WORK"
    return state
```

---

## 3. Tools

```python
def search_docs(query: str) -> dict:
    """Mock RAG — returns text + citations."""
    ...

def get_ticket_status(ticket_id: str) -> dict:
    """Mock Jira ticket lookup."""
    ...

def create_ticket(title: str, description: str) -> dict:
    """Mock Jira ticket creation — with HITL gate."""
    ...

def escalate_to_human(query: str) -> str:
    """Mock PagerDuty / Slack escalation."""
    ...
```

In production: each tool wraps an MCP server. The mock implementations
return canned data so the demo works offline.

---

## 4. Architecture

```text
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

### Why these design choices

**Why LangGraph, not CrewAI?** We need parallel fan-out from the Planner
and a conditional loop (Reviewer → Summarize if NEEDS_WORK). CrewAI's
`Process.sequential` doesn't support these directly.

**Why a Reviewer agent?** The first draft often has unsupported claims.
The Reviewer catches them and routes back to Summarize with feedback.
In production this can be an LLM-as-judge with a strict rubric.

**Why HITL on create_ticket?** Writes to external systems must be
auditable. A single wrong ticket can break dashboards. HITL = 1-hour
delay vs 4-hour cleanup.

**Why a per-user budget cap?** LLM costs can run away. One user can burn
the entire daily budget in minutes. Budget cap = circuit breaker.

---

## 5. Technology Architecture

```text
Frontend
   ↓
FastAPI
   ↓
LangGraph
   ↓
Agent State
   ↓
LLM
   ↓
MCP / Tools
   ↓
External Systems

RAG
 ↓
Vector Database

Long-running execution
 ↓
Temporal

Observability
 ↓
Logs / Metrics / Traces
```

---

## 6. Example User Journey

User: *"My VPN has stopped working. Can you check whether I already have
a ticket and tell me what I should do?"*

Planner:
1. Search VPN documentation.
2. Check existing tickets.
3. Generate recommendation.

Knowledge Agent:
- Retrieved: VPN Troubleshooting Guide (it-security.pdf#v3.2#section-5.1).

Ticket Agent:
- INC-12345 status: In Progress.

Reviewer:
- Evidence found. Existing ticket confirmed.

Final response:
> Your existing VPN ticket INC-12345 is currently in progress. The
> troubleshooting guide recommends restarting the VPN client and
> reconnecting. No new ticket was created because an existing ticket
> was found.

---

## 7. Human Approval Scenario

User: *"Create a production access request for me."*

Agent:
> Production access requires approval. Approval is required before
> creating the request.

Human: *"Approve"*

Agent:
- Creates the access request via the Ticket API.
- Returns the new ticket ID.

The flow:
```text
Sensitive Action → Approval Required → Human → Approve → Continue
```

---

## 8. Error Scenario

The Ticket API fails (timeout, 5xx, network).

```text
Ticket API → Timeout → Retry (3x) → Failure → Fallback → User Notification
```

**Critical rule:** the agent must NOT claim success unless the external
system confirms the operation. Never invent success.

```text
# WRONG:
"Ticket created successfully."  # but it wasn't

# RIGHT:
"I was unable to create the ticket. The system is currently
unavailable. Please try again in a few minutes, or open a ticket
manually at helpdesk.company.com."
```

---

## 9. Final Project Requirements

### Functional Requirements

- User query processing
- Intent understanding
- RAG retrieval
- Tool calling
- Ticket lookup
- Ticket creation
- Ticket update
- Human approval
- Final response validation

### Technical Requirements

- LLM
- LangGraph
- RAG
- Vector database
- MCP or tool abstraction
- FastAPI
- State management
- Error handling
- Logging
- Evaluation

---

## 10. Production-Readiness Checklist

- [ ] Replace mock tools with real MCP servers
- [ ] Replace in-memory state with Postgres + Redis
- [ ] Add OAuth2 + per-tenant auth
- [ ] Wire Langfuse + OpenTelemetry
- [ ] Wrap in Temporal for durable execution
- [ ] Add CI: run `tests/test_eval.py` on every PR
- [ ] Add dashboards: cost, latency, success rate, eval scores
- [ ] Set per-user budget caps
- [ ] Set per-run budget caps
- [ ] Set `max_iterations` cap on review loop
- [ ] Add HITL on all write operations
- [ ] Add input/output guardrails
- [ ] Add per-agent tool allowlists

---

## 11. Engineering Role Mapping

| Engineering Role | AI-Agent Contribution |
|------------------|-----------------------|
| Software Engineer | Agent logic, tools, APIs |
| Backend Engineer | Agent services, orchestration |
| Full Stack Engineer | Agent UI, APIs, streaming |
| QA Engineer | Agent evaluation, test scenarios, tool validation |
| DevOps Engineer | CI/CD, deployment, monitoring |
| Cloud Engineer | Infrastructure, IAM, networking |
| .NET Engineer | Enterprise APIs and integrations |
| Python Engineer | Agent logic, RAG, ML pipelines |
| Data Engineer | Data pipelines and retrieval |
| Security Engineer | IAM, authorization, guardrails |

The big takeaway: **every existing engineering role maps to a piece of
the agent system.** You don't need to become an ML researcher to
contribute. You contribute by applying what you already know.

---

## 12. Where to Go Next

After this training, you should be able to:

- Build a tool-calling agent from scratch.
- Add RAG, guardrails, HITL, memory, multi-agent routing.
- Deploy as a production API with streaming, tracing, and budgets.
- Read and modify an agent YAML spec.
- Evaluate an agent (offline + online).
- Identify and fix common mistakes (injection, runaway cost, no HITL).

### Deep dives

- **Temporal for agent durability** — wrap LangGraph in Temporal activities.
- **Agent evaluation** — beyond LLM-as-judge: behavioral tests, regression
  suites, A/B frameworks.
- **MCP server development** — build your own MCP server for internal tools.
- **Multi-tenant RAG** — metadata filtering, per-tenant embeddings,
  access control lists.
- **Agent security** — sandboxing, prompt-injection defenses, secrets
  management.

### Build

- Ship a production agent in your team. Start with a single-agent,
  one-tool pilot.
- Pick a real Jira / Slack / GitHub workflow and automate it.

### Read

- LangGraph docs (langchain-ai.github.io/langgraph)
- MCP spec (modelcontextprotocol.io)
- Temporal docs (temporal.io)
- "Building LLMs for Production" by Louie Peters

---

## Closing

The seven days took you from "what is a token?" to "I shipped a
production-grade multi-agent system." The capstone here is small — but
the patterns are exactly what you'd use at scale.

**The biggest risk** is treating agents as magic. They are software
with new failure modes. Apply the same engineering rigor you'd apply
to any other distributed system.

**The biggest opportunity** is that every existing skill you have —
backend, frontend, QA, DevOps, security, data — maps directly onto a
piece of an agent system. You're already qualified. Go build.
