# Day 4 Project — Production Enterprise Agent

## Business Problem
The Day-2 helpdesk agent works on a laptop but not for 5,000 employees. We need it as a service.

## Goal
Deploy the agent as:
- A **REST API** behind authentication.
- With **streaming** for long answers.
- With **tracing** for every run.
- With **per-user budget** enforcement.
- With **retry** + **timeout** on every external call.

## Architecture
```
Client (web/mobile)
   ↓
API Gateway (OAuth2, rate limit)
   ↓
Agent Service (FastAPI)
   ├── Sync endpoint: /agent/run
   ├── SSE endpoint:   /agent/stream
   └── Async endpoint: /agent/submit → webhook
   ↓
LLM + Tools + RAG
   ↓
Observability → Langfuse + OpenTelemetry → Grafana
```

## SLOs (Service-Level Objectives)
| Metric | Target |
|--------|--------|
| Latency p50 | < 2 s |
| Latency p99 | < 10 s |
| Availability | 99.5% |
| Cost per request | < $0.10 |
| Streaming first-token | < 1 s |

## What Day 4 Adds vs Day 1–3
| Concern | Day 1–3 | Day 4 |
|---------|---------|-------|
| Deployment | Script | REST API + SSE |
| Errors | Crashes | Retry + fallback |
| Cost | Unknown | Per-user budget |
| Observability | print() | Langfuse + traces |
| Security | None | Auth + guardrails |
| Throughput | 1 user | N users |
