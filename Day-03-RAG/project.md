# Day 2 Project — Policy-Aware Helpdesk Agent

## Business Problem
The Day-1 agent had hard-coded knowledge. Real employees ask about company policies that change quarterly. We need an agent that answers from the *current* HR/IT/Security docs.

## Goal
Build an agent that:
- Looks up policies via **RAG** (retrieval-augmented generation).
- Looks up employee data (leave balance, manager, role).
- Creates tickets only after **human approval** (HITL).
- Rejects dangerous queries via **input guardrails**.

## Architecture
```
User Query
   ↓
[Guardrail: input filter (PII redaction, topic block)]
   ↓
Agent Loop
   ├── search_hr_policy(query) → RAG over HR/IT/Security docs
   ├── get_employee(user_id)   → DB lookup
   └── create_ticket(...)      → [HITL APPROVAL REQUIRED]
   ↓
[Guardrail: output validation (JSON schema)]
   ↓
Final Answer
```

## 9 Building Blocks in this Project
| # | Block | Where in code |
|---|-------|---------------|
| 1 | LLM | `client` (Azure OpenAI gpt-4o) |
| 2 | Tools | `search_hr_policy`, `get_employee`, `create_ticket` |
| 3 | State | `messages` list per session |
| 4 | Memory | Long-term: vector store + employee DB |
| 5 | Planning | ReAct loop in `agent.py` |
| 6 | Reasoning | LLM picks tool + args |
| 7 | Context | system + last 5 messages + retrieved policy |
| 8 | Guardrails | Pre/post hooks |
| 9 | HITL | `require_approval=True` on write tools |

## What Day 2 Does NOT Yet Do
- ✗ No multi-agent routing (Day 3)
- ✗ No streaming (Day 4)
- ✗ No production API (Day 4)
- ✗ No observability (Day 4)
