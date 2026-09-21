# Day 2 — Project · IT Support Agent

## Objective

Build a multi-tool agent that can:

- Search documentation.
- Check ticket status.
- Create tickets (with human approval).
- Update tickets (with human approval).

The agent reasons, decides, calls tools, observes results, and
reasons again — until it has enough information to answer.

## Agent Architecture

```text
User
  ↓
IT Support Agent
  ↓
LLM
 ├── Documentation Tool  (search_docs)
 ├── Ticket Lookup Tool  (get_ticket_status)
 └── Ticket Creation Tool  (create_ticket, requires_approval)
```

## Tools

### `search_docs(query: str) → dict`

Search the IT knowledge base. Returns text snippets + sources.

### `get_ticket_status(ticket_id: str) → dict`

Look up an existing Jira ticket. Returns status, priority, assignee.

### `create_ticket(title: str, description: str) → dict`

Create a new ticket. **Requires human approval.** The tool appends to
`PENDING_WRITES` and returns `{"status": "pending_approval"}`.

## Acceptance Criteria

1. Agent correctly identifies when to use `search_docs` vs `get_ticket_status`.
2. Agent **never** calls `create_ticket` without explicit user request.
3. All `create_ticket` calls land in `PENDING_WRITES`.
4. Tool results are correctly appended to the message history.
5. The agent reaches a final answer within 5 iterations.
6. Edge cases handled: empty tool result, malformed JSON, tool timeout.

## Project Mapping

| Concept | Implementation |
|---------|---------------|
| Agent | IT Support Agent |
| LLM | Decision-making |
| Tool | Ticket API |
| State | Current request |
| Memory | User/session context |
| Planning | Troubleshooting flow |
| Guardrails | Allowed actions |
| HITL | Sensitive operations |
