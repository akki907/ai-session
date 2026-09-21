# Day 7 — Knowledge Assessment

**Duration:** 30 minutes
**Format:** Open-book, but no copy-paste from your project code.
**Pass mark:** 11 / 15
**Resit:** Allowed after 1 week.

---

## Section A — Fundamentals (Day 1–2, 6 questions)

### A1. Tokens & Context (2 pts)
a) Define a "token" in the context of an LLM. (1 pt)
b) A model has a 128K-token context window. Your system prompt is 800 tokens, retrieved docs are 12K tokens, and conversation history is 4K tokens. Roughly how many tokens are left for the model's response? (1 pt)

### A2. Agent Loop (2 pts)
In 3–5 sentences, describe the ReAct loop. What happens at each step?

### A3. Structured Output (1 pt)
Why do we use `response_format={"type":"json_object"}` instead of just asking the model to "return JSON"?

### A4. RAG (1 pt)
Explain in one sentence what retrieval-augmented generation does, and give one reason it is preferred over fine-tuning for company-specific knowledge.

---

## Section B — Frameworks & Multi-Agent (Day 3, 4 questions)

### B1. Framework Choice (2 pts)
For each scenario below, pick the most appropriate framework (LangChain / LangGraph / CrewAI / raw loop) and justify in one sentence:
- (a) A 3-step sequential pipeline: classify → summarize → email.
- (b) A research system that runs 4 sub-questions in parallel, then merges.
- (c) A 6-agent research crew where each agent has a clear role.

### B2. Multi-Agent Topology (1 pt)
Name and describe two multi-agent topologies (e.g. planner/worker, supervisor, reviewer).

### B3. MCP (1 pt)
In one sentence, what problem does the Model Context Protocol (MCP) solve?

---

## Section C — Production (Day 4, 3 questions)

### C1. Async vs Streaming (2 pts)
For each scenario, recommend async + webhook, SSE streaming, or sync request-response, and explain why:
- (a) A 3-second question-answering flow.
- (b) A 10-minute document-summary job.
- (c) A long chat session where the user watches tokens appear.

### C2. Observability (1 pt)
List three things you would put in a Langfuse trace for a production agent run.

---

## Section D — Real-World (Day 5–6, 2 questions)

### D1. Agent Spec (1 pt)
Open `Day-06-Mini-Project/architecture/specs/it-support-agent.yaml`. Identify which fields correspond to:
- HITL gate
- Per-user budget
- Output guardrail

### D2. Eval (1 pt)
You ship a new prompt for the Day-6 agent. What would your regression test suite check before merging the PR?

---

## Answer Key (for instructor)

| Q | Answer (key points) |
|---|---|
| A1.a | A unit of text the model processes (≈ 4 chars English). Not necessarily a word. |
| A1.b | ~111,200 tokens left. |
| A2 | Reason → Act (call tool) → Observe (get result) → loop until done. |
| A3 | Guarantees valid JSON output; cheaper retries; downstream schema validation. |
| A4 | Retrieves relevant docs and adds them to context before generating. RAG preferred because: cheaper, instant updates, verifiable, citations possible. |
| B1.a | LangChain or raw loop. Sequential, no parallel, simple. |
| B1.b | LangGraph (parallel START edges + merge). |
| B1.c | CrewAI (role-based agents + sequential or hierarchical process). |
| B2 | Planner/worker (one planner dispatches), Supervisor (routes + approves), Reviewer (loops back if NEEDS_WORK). |
| B3 | Standardizes how tools are exposed to any LLM client — one protocol for any tool. |
| C1.a | Sync request-response. |
| C1.b | Async + webhook (10 min is too long for HTTP). |
| C1.c | SSE streaming. |
| C2 | Run ID, user ID, all LLM prompts + responses, tool call args + results, latency, cost, error type. |
| D1 | HITL → `hitl.approve_before[]`; budget → `limits.budget_usd_per_user_per_day`; output guardrail → `guardrails.output[]`. |
| D2 | RAG accuracy, tool routing correctness, HITL gate fires, cost under threshold, JSON schema valid, no PII leakage, streaming first-token &lt; 1 s. |
