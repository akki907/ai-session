# Day 7 — End-to-End Enterprise Agent · Requirements

The capstone project is an **Enterprise IT Support Multi-Agent System** that
exhibits every concept from Days 1–6.

## Functional Requirements

The system must:

1. Accept a natural-language request from an authenticated employee.
2. Determine intent (policy question · ticket lookup · ticket creation · access request · escalation).
3. Search the enterprise knowledge base (RAG) when the answer is not in the model's training.
4. Look up or create Jira tickets via MCP tools.
5. Pause and request human approval before any write to an external system (HITL).
6. Validate the final response through a Reviewer agent (groundedness + completeness).
7. Stream progress events to the client (SSE).
8. Return a structured response with citations and tool-call history.

## Non-Functional Requirements

| Concern | Requirement |
|---------|-------------|
| Latency | First event < 2 s. Total < 30 s for typical requests. |
| Cost | < $0.10 per request. $5.00 per user per day budget cap. |
| Reliability | Retries (3x exp backoff). Fallbacks. Never claim success on a failed tool call. |
| Observability | Every LLM and tool call traced to Langfuse. Every error logged with request_id. |
| Security | Per-tenant auth. Tool authorization. PII redaction. Prompt-injection detection. |
| Audit | All write operations require human approval + produce an audit record. |

## Test Scenarios

The `starter-code/tests/test_eval.py` suite covers:

- VPN policy question returns grounded answer with citation.
- Ticket lookup returns structured result.
- `create_ticket` always goes through HITL.
- Urgent query triggers escalation.
- Budget cap blocks over-spending users.

## Out of Scope (for the workshop)

- Production auth (OAuth2, mTLS, etc.) — use a stub.
- Real Jira / Slack / PagerDuty connections — use the mocked tools in `tools.py`.
- Multi-tenant isolation — assume single tenant.
- Disaster recovery / cross-region failover.
