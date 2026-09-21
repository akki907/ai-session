# Day 2 — AI Agents & Agent Architecture · Notes

> The transition from "LLM answers questions" to "LLM takes actions in the world."

---

## 1. What is an AI Agent?

An **agent** is an LLM application that can call **tools** to affect the
outside world, then decide what to do next based on the results.

```text
Observe → Reason → Decide → Act → Observe Result → Repeat
```

The "Repeat" is the crucial part. A single-shot LLM call is not an agent.
The agent decides when it has enough information to stop.

---

## 2. LLM Application vs Agent

### Simple LLM application

```text
Question → LLM → Answer
```

One call. No tools. No iteration. Stateless.

### Agent

```text
Question
  ↓
Agent
  ↓
LLM
  ↓
Decision (call tool X or finish)
  ↓
If tool: execute → feed result back to LLM → loop
If finish: return answer
```

Multiple LLM calls. Tools. State. Iteration.

---

## 3. Agent Components

```text
                  Agent
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
       LLM        State       Tools
                    │
                  Memory
```

| Component | Role |
|-----------|------|
| **LLM** | The reasoning engine |
| **Instructions** | System prompt defining role + rules |
| **Tools** | Functions the LLM can call |
| **State** | The current request context (messages, scratchpad) |
| **Memory** | Cross-request context (session, user, long-term) |
| **Planning** | Strategy for breaking down the task |
| **Guardrails** | Limits on what the agent can do |
| **HITL** | Human approval for sensitive actions |

---

## 4. Tools

A tool is a typed function the LLM can request. In OpenAI's API:

```json
{
  "type": "function",
  "function": {
    "name": "search_docs",
    "description": "Search the IT knowledge base for relevant articles.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string"}
      },
      "required": ["query"]
    }
  }
}
```

The LLM receives tool definitions in the prompt. When it decides a tool
is needed, it returns a `tool_call` instead of (or in addition to) text.
Your code executes the function, feeds the result back.

### Common tool categories

- REST APIs (Jira, ServiceNow, GitHub, Salesforce)
- Databases (read + write)
- Search (Elasticsearch, OpenSearch)
- Internal services
- File systems, calendars, email
- Cloud platforms (AWS, GCP, Azure)
- Kubernetes, observability systems

### Tool design principles

1. **One job per tool.** `search_docs` ≠ `search_docs_and_summarize`.
2. **Typed parameters.** Use JSON schema. Validate at the boundary.
3. **Idempotent when possible.** Easier to retry safely.
4. **Return structured data.** JSON with fields the LLM can reason over.
5. **Add descriptions.** The LLM uses your description to decide when to
   call the tool. A bad description = bad tool selection.

---

## 5. Agent Execution Flow

```text
User
 ↓
LLM
 ↓
Tool Call
 ↓
Application
 ↓
External API
 ↓
Tool Result
 ↓
LLM
 ↓
... loop or finish ...
 ↓
Final Response
```

**Key invariants:**

- The LLM never executes tools directly. Your code does.
- Tool results are appended to the message history.
- The agent runs until the LLM returns without `tool_calls` OR a max iteration cap.

### Failure modes in the loop

| Failure | What happens | Fix |
|---------|--------------|-----|
| Tool returns invalid JSON | LLM hallucinates an answer | Validate tool output before feeding back |
| Tool times out | Agent hangs | Add per-tool timeout |
| LLM keeps calling tools | Infinite loop, runaway cost | `max_iterations` cap |
| LLM can't parse tool args | Wrong tool called | Better JSON schema + descriptions |
| Tool returns sensitive data | PII leaks into LLM context | Redact in tool wrapper |

---

## 6. State

The **state** is the data the agent maintains across iterations of its
loop. Minimum useful state:

```python
{
  "messages": [...],   # full conversation history
  "user_id": "u-42",
  "request_id": "req-123",
  "tool_calls": [...], # audit log
  "iteration": 0,      # loop counter
}
```

The state is what makes the loop survive across LLM calls.

---

## 7. Memory

| Type | Lifetime | Example |
|------|----------|---------|
| **Request state** | One agent run | Current messages, tool results |
| **Conversation memory** | One user session | "User prefers email notifications" |
| **Long-term memory** | Across sessions | User profile, past tickets |

**Common patterns:**
- Conversation: append messages to a list, optionally summarize when too long.
- Long-term: store in a vector DB keyed by user_id; retrieve top-k relevant facts.

---

## 8. Planning

Before acting, an agent often needs to break a goal into steps. Patterns:

- **ReAct** — reason → act → observe (most common, default for tool-calling).
- **Plan-and-Execute** — generate the full plan first, then execute step by step.
- **Reflexion** — after each step, critique and revise the plan.

```text
User: Investigate my VPN issue.

Plan:
1. Search documentation.
2. Check existing tickets.
3. Determine whether troubleshooting is sufficient.
4. Create a ticket if necessary.
5. Respond to user.
```

---

## 9. Human-in-the-Loop (HITL)

```text
Agent → Sensitive Action → Approval Required → Human → Approve/Reject → Tool Execution
```

**When you need HITL:**
- Writes to external systems (Jira, Slack, production DBs).
- Destructive actions (delete, revoke access).
- High-cost actions (refunds, escalations).
- Compliance-mandated approvals.

**Implementation pattern:**
- Mark the tool with `requires_approval: true` (in the spec).
- On tool call, append to a pending queue and return `status: pending_approval`.
- Pause the agent loop until the human approves.
- On approval, re-invoke the tool for real.

---

## 10. Guardrails

| Layer | Example |
|-------|---------|
| **Input** | Block PII, detect prompt injection, topic blocklist |
| **Tool** | Allowlist of tools per agent, per-user permissions |
| **Output** | Schema validation, PII redaction, toxicity filter |
| **Iteration** | `max_iterations=8`, `max_tokens=50000` |
| **Cost** | `$0.10 per run`, `$5 per user per day` |
| **Time** | `timeout_seconds=120` |

**Rule:** the agent can never exceed its declared limits. Hard-code them.

---

## Project: IT Support Agent

```text
User
 ↓
IT Support Agent
 ↓
LLM
 ├── Documentation Tool (search_docs)
 ├── Ticket Lookup Tool (get_ticket_status)
 └── Ticket Creation Tool (create_ticket, requires_approval)
```

Hands-on builds all three tools + the loop.

---

## Bridge to Day 3

Today the agent's only knowledge was what was in the LLM's training data.
Tomorrow we add **RAG** — the agent decides when to look up enterprise
documents, retrieves the right chunks, and grounds its answer on them.
