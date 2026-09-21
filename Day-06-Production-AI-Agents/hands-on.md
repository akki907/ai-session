# Day 4 — Hands-on (15 min)

## Goal
Take the Day-1 agent and wrap it in a production-ready FastAPI service: SSE streaming, Langfuse tracing, retry logic, and a per-user budget cap.

## Setup
```bash
pip install fastapi uvicorn langfuse tenacity
export LANGFUSE_PUBLIC_KEY="pk-..."
export LANGFUSE_SECRET_KEY="sk-..."
```

## Steps

### Part A — Wrap agent in FastAPI (5 min)
1. Open `code/day4_fastapi_agent.py`.
2. Note the `/agent/run` POST endpoint that wraps the Day-1 agent.
3. Run: `uvicorn day4_fastapi_agent:app --reload`
4. Test: `curl -X POST localhost:8000/agent/run -H "Content-Type: application/json" -d '{"user_id":"u-1","query":"VPN issue"}'`

### Part B — Add streaming (3 min)
1. Open `code/day4_streaming.py`.
2. Test the SSE endpoint: `curl -N localhost:8000/agent/stream?q=hello`
3. Confirm tokens arrive one-by-one.

### Part C — Tracing + retry (4 min)
1. Add Langfuse tracing to your `/agent/run` endpoint (already in the code).
2. Add a retry decorator on the LLM call (already in the code).
3. Open the Langfuse UI and confirm your test run shows up.

### Part D — Budget cap (3 min)
1. Add a per-user budget: read budget from a Redis hash on every request.
2. If `spent + estimated_cost > 0.50`, reject with 429.
3. Increment the budget after every successful call.

## Expected Output
```json
{
  "answer": "Based on IT-Security.pdf#5.1...",
  "tool_calls": [...],
  "tokens": {"input": 1840, "output": 220, "cost_usd": 0.012}
}
```

## Common Mistakes
- ❌ Streaming without backpressure handling. Disconnected clients leak memory.
- ❌ No timeout. Hanging LLM holds a worker forever.
- ❌ No retry — transient failures become customer-visible outages.
- ❌ Secrets in env vars baked into the container image.
