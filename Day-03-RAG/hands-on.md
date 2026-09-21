# Day 2 — Hands-on (15 min)

## Goal
Extend the Day-1 agent with: HITL gate on writes, RAG-backed policy lookup, and a simple input/output guardrail.

## Setup
```bash
pip install openai chromadb pydantic
```

## Steps

### Part A — Architecture (5 min)
1. Open `code/day2_architecture.py`.
2. Read the multi-tool helpdesk agent. Confirm you see 3 tools: HR Policy, Employee Data, Ticket.
3. Note how `create_ticket` is wrapped in a HITL approval.

### Part B — Add guardrails (5 min)
1. Add an input guardrail: any message containing `"salary"` is rejected before reaching the LLM.
2. Add an output guardrail: the final response must be valid JSON with `{"status": "...", "reason": "..."}`.
3. Test that an invalid request is rejected with a friendly error.

### Part C — RAG (5 min)
1. Open `code/day2_rag.py`.
2. Run the ingest step on `code/data/sample_policies.txt`.
3. Query: `"What is the leave policy for full-time employees?"`
4. Confirm you see a real policy snippet, not a hallucinated one.

## Expected Output
```
>> query: "How many vacation days do I have?"
<< answer: "According to the HR Handbook (v3.2, section 4.1),
            full-time employees receive 25 vacation days per year,
            accrued at 2.08 days/month."
<< citations: ["hr-handbook.pdf#v3.2#section-4.1"]
```

## Common Mistakes
- ❌ Guardrail rejects *after* the LLM call (costs tokens). Reject *before*.
- ❌ No overlap between chunks. Sentences get split mid-thought.
- ❌ Forgetting to include `user_id` in the trace.
