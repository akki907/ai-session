# Day 4 — Agent Frameworks & MCP · Notes

> The major abstractions used to build modern AI-agent systems.
> Frameworks are tools. Pick the right one for the job.

---

## 1. Why Frameworks Exist

Raw OpenAI + manual loops work for prototypes. They don't scale because:

- You reinvent state management, retries, observability, HITL every time.
- Switching LLM providers means rewriting the call layer.
- Adding a new tool means rewriting the dispatcher.
- Testing is hard because everything is one big script.

Frameworks give you reusable building blocks. The spec does NOT mandate
any framework. Pick the one that matches the problem.

---

## 2. LangChain

LangChain is the **kit-of-parts** for LLM applications. Its mental model:

| Primitive | What it is |
|-----------|-----------|
| **Model** | Wraps an LLM (OpenAI, Anthropic, Azure, ...) |
| **Prompt** | A versioned template with variables |
| **Tool** | A typed function the LLM can call |
| **Retriever** | Wraps a vector DB with a unified interface |
| **Agent** | The loop: prompt → model → tool → repeat |
| **Output parser** | Validates and parses model output |
| **Memory** | Persists state across calls |

### Architecture

```text
Application
 ↓
LangChain
 ├── Model
 ├── Prompt
 ├── Tools
 └── Retriever
```

### When to use LangChain

- You want to swap models / providers / vector DBs without rewriting code.
- You want a clean composition of prompts + models + tools.
- You're building a single-agent application.
- You want lots of pre-built integrations (loaders, retrievers, tools).

### When NOT to use it

- You need explicit control over the agent loop (use LangGraph).
- You need conditional branching, cycles, or HITL pauses (use LangGraph).
- You're building a multi-agent system with non-trivial topology (LangGraph).

---

## 3. LangGraph

LangGraph models agents as **stateful graphs**. Every node is a function
that reads the state, does work, and returns an updated state. Edges define
what runs next.

### Core concepts

| Concept | What it is |
|---------|-----------|
| **State** | A TypedDict passed between nodes |
| **Node** | A function: `state → state` |
| **Edge** | A connection: `node A → node B` |
| **Conditional edge** | A function decides the next node |
| **Loop** | Edge that points back (e.g. Reviewer → Summarize on NEEDS_WORK) |
| **Checkpoint** | Persisted state for resume / time-travel debugging |
| **Interrupt** | Pause the graph (for HITL approval) |
| **Send** | Fan-out: one node triggers N parallel nodes |

### Example topology

```text
START
 ↓
Planner
 ↓
Research
 ↓
Review
 ↓
Conditional
 ├── Retry → Research
 └── Final Answer → END
```

### State definition

```python
class AgentState(TypedDict):
    question: str
    research: list[str]
    review: str
    final_answer: str
```

### When to use LangGraph

- ✅ You need parallel fan-out (Planner → 3 workers in parallel).
- ✅ You need conditional routing (reviewer passes or fails).
- ✅ You need HITL pauses that survive restarts.
- ✅ You want to visualize the workflow as a graph.
- ✅ You want time-travel debugging (checkpoint + replay).

### When NOT to use it

- Single-shot LLM calls (overkill).
- Linear pipelines without branching (a plain function is enough).
- Pure role-based multi-agent (CrewAI might be cleaner).

---

## 4. CrewAI

CrewAI's mental model: **roles + tasks + a crew**.

| Concept | What it is |
|---------|-----------|
| **Agent** | A role with a goal, backstory, and tools |
| **Task** | A unit of work assigned to an agent with expected output |
| **Crew** | A group of agents that execute a list of tasks |
| **Process** | How tasks are scheduled (`sequential`, `hierarchical`) |
| **Delegation** | An agent can hand work to another agent |

### Example

```text
Researcher (role: Research Analyst, tools: [search])
  → research_task (description, expected_output)

Writer (role: Technical Writer, tools: [])
  → write_task (description, expected_output)

Reviewer (role: Fact-checker, tools: [])
  → review_task (description, expected_output)

Crew([Researcher, Writer, Reviewer], process=sequential)
```

### When to use CrewAI

- ✅ Role-based collaboration reads naturally (researcher, writer, reviewer).
- ✅ You want task delegation built-in.
- ✅ You prefer declarative agent definitions (Python classes).

### When NOT to use it

- You need complex conditional branching or parallel fan-out beyond delegation.
- You need durable execution, HITL pauses, or checkpointing (use LangGraph).
- You need fine-grained control over the state shape (LangGraph's TypedDict is cleaner).

---

## 5. MCP — Model Context Protocol

MCP is a **standardized protocol** between AI applications and tool/data
servers. It solves the "every framework reinvents tool calling" problem.

### Why MCP matters

Before MCP: every agent framework (LangChain, LangGraph, CrewAI, custom)
defines its own tool calling convention. Each tool server has to be
re-implemented for each framework.

After MCP: one tool server (e.g. `jira-mcp`) works with any MCP-compatible
client (Claude Desktop, Cursor, your LangGraph agent, ...).

### Architecture

```text
AI Application
      ↓
   MCP Client
      ↓
   MCP Server
      ↓
 ┌────┼──────────┐
 ↓    ↓          ↓
Tools Resources Prompts
```

### Components

- **MCP Client** — lives inside your AI app. Manages connections to servers.
- **MCP Server** — wraps a backend (Jira, GitHub, DB, files). Exposes
  capabilities.
- **Tools** — actions the agent can execute. Declared with JSON schema.
- **Resources** — read-only context the client can fetch.
- **Prompts** — reusable prompt templates the server can return.

### Two transports

| Transport | Use case |
|-----------|----------|
| **stdio** | Local development. Server runs as a child process. |
| **Streamable HTTP** | Production. Server runs as a long-lived HTTP endpoint. |

### JSON-RPC methods

| Method | Purpose |
|--------|---------|
| `initialize` | Handshake, exchange capabilities |
| `tools/list` | List available tools on a server |
| `tools/call` | Invoke a tool by name with arguments |
| `resources/list` | List resources |
| `resources/read` | Read a resource |
| `prompts/list` | List prompt templates |
| `prompts/get` | Fetch a prompt template by name |

### Conceptual flow

```text
list tools → server returns [search_docs, create_ticket, ...]
call tools/call name=search_docs args={q:"VPN"} → server returns result
```

---

## 6. When to Combine

Frameworks are not mutually exclusive. A common production pattern:

```text
LangGraph
    ↓
Agent Orchestration (state, nodes, edges, HITL)
    ↓
MCP
    ↓
Enterprise Tools (Jira, Slack, Salesforce, ...)
    ↓
LangChain primitives
    ↓
LLM + Prompts + Retrievers
```

### Decision guide

| Need | Pick |
|------|------|
| Quick prototype, single agent | LangChain |
| Complex workflow with branches and loops | LangGraph |
| Role-based collaboration | CrewAI |
| Standardized tool integration across apps | MCP |
| RAG with retrieval | LangChain retrievers (works in any framework) |

---

## 7. Framework Comparison (No Ranking)

| Framework | Primary abstraction |
|-----------|---------------------|
| **LangChain** | LLM application building blocks |
| **LangGraph** | Stateful agent/workflow orchestration |
| **CrewAI** | Role-based multi-agent collaboration |
| **MCP** | Standardized tool/context integration |

Each solves a different problem. The spec deliberately does not rank them.

---

## 8. Common Failure Modes

- **Framework lock-in.** Pick a framework, get stuck rewriting when you
  need a feature it doesn't have. Keep tool integrations behind MCP when
  possible so you can swap frameworks.
- **Over-abstraction.** Some teams use LangGraph for a one-shot LLM call.
  Match the framework to the problem complexity.
- **CrewAI for everything.** CrewAI's `Process.sequential` doesn't support
  parallel fan-out cleanly. If you need it, use LangGraph.
- **Custom tool protocols.** Re-implementing JSON-RPC tool calling instead
  of using MCP. You will regret it when you need a second client.
- **Ignoring state.** Framework state must be bounded. Cap message history,
  cap token usage, summarize aggressively.

---

## Bridge to Day 5

Tomorrow we put multiple specialized agents together: Planner/Worker,
Supervisor, Reviewer. We use LangGraph because we need parallel fan-out
and conditional loops — exactly its strengths.
