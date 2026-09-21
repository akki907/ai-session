"""
Day 6 — Tool implementations (mocked for the workshop).

In production these would call:
- ChromaDB / pgvector for `search_docs`
- Jira REST API for `get_ticket_status` / `create_ticket`
- PagerDuty / Slack for `escalate_to_human`

For the workshop we use canned responses so the demo works offline.
"""
import json
import uuid

# --- Mock data store ---
MOCK_POLICIES = {
    "it-security.pdf#v3.2#section-5.1": (
        "VPN Policy: Personal devices require MFA. Approved for use only "
        "with prior IT approval. Connection drops every 5 minutes often "
        "indicate a stale session token — reconnect via the IT VPN client."
    ),
    "it-handbook.pdf#v2.1#section-3.4": (
        "Password Reset: Use the self-service portal at password.company.com. "
        "If MFA is locked, contact IT helpdesk."
    ),
    "hr-handbook.pdf#v3.2#section-4.1": (
        "Leave Policy: Full-time employees receive 25 vacation days per year, "
        "accrued at 2.08 days/month."
    ),
}

MOCK_TICKETS = {
    "T-1042": {"id": "T-1042", "status": "OPEN", "priority": 2, "title": "VPN connection drops"},
    "T-1043": {"id": "T-1043", "status": "RESOLVED", "priority": 3, "title": "Slow Wi-Fi"},
}

PENDING_WRITES: list[dict] = []


def search_docs(query: str) -> dict:
    """Mock RAG retrieval."""
    q = query.lower()
    for citation, text in MOCK_POLICIES.items():
        if any(w in text.lower() for w in q.split()):
            return {"text": text, "citations": [citation]}
    return {
        "text": "No matching policy found.",
        "citations": [],
    }


def get_ticket_status(ticket_id: str) -> dict:
    """Mock Jira ticket lookup."""
    return MOCK_TICKETS.get(ticket_id, {"id": ticket_id, "status": "UNKNOWN"})


def create_ticket(title: str, description: str) -> dict:
    """Create a ticket — but require human approval first.

    In demo mode: append to PENDING_WRITES and return pending status.
    Approver UI must call /approvals/{id}/approve to actually create it.
    """
    new_id = f"T-{1100 + len(PENDING_WRITES)}"
    PENDING_WRITES.append({
        "id": new_id,
        "title": title,
        "description": description,
        "status": "pending_approval",
    })
    return {"id": new_id, "status": "pending_approval", "title": title}


def escalate_to_human(query: str) -> str:
    """Mock PagerDuty / Slack escalation."""
    incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    return f"Incident {incident_id} created and routed to on-call IT manager."
