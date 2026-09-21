"""
Day 6 — Eval suite for the IT Support Multi-Agent System.

Run:
    pytest tests/test_eval.py -v
"""
import pytest
from tools import search_docs, get_ticket_status, create_ticket, PENDING_WRITES
from graph import build_graph


# --- Tool-level tests ---

def test_search_docs_finds_vpn_policy():
    res = search_docs("VPN keeps dropping")
    assert "VPN" in res["text"]
    assert len(res["citations"]) >= 1


def test_search_docs_finds_password_reset():
    res = search_docs("forgot my password")
    assert "self-service" in res["text"].lower() or "password.company.com" in res["text"].lower()


def test_get_ticket_status_existing():
    res = get_ticket_status("T-1042")
    assert res["id"] == "T-1042"
    assert res["status"] in ("OPEN", "RESOLVED", "CLOSED")


def test_get_ticket_status_unknown():
    res = get_ticket_status("T-9999")
    assert res["status"] == "UNKNOWN"


def test_create_ticket_requires_approval():
    before = len(PENDING_WRITES)
    result = create_ticket(title="VPN drops", description="Every 5 min")
    assert result["status"] == "pending_approval"
    assert len(PENDING_WRITES) == before + 1


# --- End-to-end agent tests ---

@pytest.fixture
def graph():
    return build_graph()


def test_vpn_query_returns_grounded_answer(graph):
    result = graph.invoke({
        "user_id": "u-42", "query": "My VPN keeps dropping every 5 minutes",
        "plan": [], "knowledge": "", "ticket_info": {},
        "escalation": "", "draft": "", "review": "",
        "citations": [], "tool_calls": [],
    })
    assert result["draft"]  # non-empty
    assert "VPN" in result["draft"] or "vpn" in result["draft"].lower()


def test_escalation_triggers_for_urgent_query(graph):
    result = graph.invoke({
        "user_id": "u-42", "query": "This is critical, get a human on it NOW",
        "plan": [], "knowledge": "", "ticket_info": {},
        "escalation": "", "draft": "", "review": "",
        "citations": [], "tool_calls": [],
    })
    # planner should detect "critical" / "urgent"
    assert "escalation" in result["plan"]


def test_create_ticket_always_goes_through_hitl():
    """Even when planner picks ticket, create_ticket appends to PENDING_WRITES."""
    before = len(PENDING_WRITES)
    create_ticket(title="Laptop broken", description="won't boot")
    assert len(PENDING_WRITES) == before + 1
    assert PENDING_WRITES[-1]["status"] == "pending_approval"
