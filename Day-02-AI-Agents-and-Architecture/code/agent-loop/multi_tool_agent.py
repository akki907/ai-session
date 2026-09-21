"""
Day 2 — Multi-tool helpdesk agent with HITL gate on writes.

Demonstrates:
- 3 tools (policy search, employee lookup, ticket create)
- Input guardrail (PII + topic block)
- Output guardrail (JSON validation)
- Human-in-the-loop on create_ticket
"""
import json
import sys
from pathlib import Path

# Allow `from llm_config import ...` regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_client, get_model

client = get_client()
MODEL = get_model()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_hr_policy",
            "description": "Search HR, IT, and Security policies.",
            "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee",
            "description": "Look up employee data: name, role, leave balance.",
            "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a new IT support ticket. Requires human approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["title", "description"],
            },
        },
    },
]

# --- Mock implementations ---
def search_hr_policy(q: str) -> str:
    return json.dumps({
        "results": [
            {"source": "hr-handbook.pdf#v3.2",
             "section": "Leave Policy",
             "text": "Full-time employees receive 25 vacation days/year."}
        ]
    })


def get_employee(user_id: str) -> str:
    return json.dumps({"name": "Jane Doe", "role": "Engineer", "leave_balance": 12})


PENDING_WRITES = []  # in real life → approval queue


def create_ticket(title: str, description: str) -> str:
    """In demo mode: auto-reject and require explicit human approval."""
    ticket_id = f"T-{3000 + len(PENDING_WRITES)}"
    PENDING_WRITES.append({"id": ticket_id, "title": title})
    return json.dumps({
        "status": "pending_approval",
        "ticket_id": ticket_id,
        "message": "Awaiting human approval. Review in the approval UI.",
    })


DISPATCH = {
    "search_hr_policy": search_hr_policy,
    "get_employee": get_employee,
    "create_ticket": create_ticket,
}

# --- Guardrails ---
BLOCKED_TOPICS = ["salary", "ssn", "credit card"]


def input_guardrail(text: str) -> str | None:
    low = text.lower()
    for t in BLOCKED_TOPICS:
        if t in low:
            return f"Sorry, I can't help with questions about {t}."
    return None


def output_guardrail(text: str) -> str:
    if not text.strip().startswith("{"):
        return json.dumps({"status": "ok", "reason": text})
    try:
        obj = json.loads(text)
        return json.dumps(obj)
    except Exception:
        return json.dumps({"status": "error", "reason": "invalid JSON output"})


def run_agent(user_msg: str, max_iter: int = 6) -> str:
    blocked = input_guardrail(user_msg)
    if blocked:
        return blocked
    messages = [
        {"role": "system", "content": "You are a policy-aware helpdesk agent. Always cite your sources."},
        {"role": "user", "content": user_msg},
    ]
    for _ in range(max_iter):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return output_guardrail(msg.content or "")
        messages.append(msg)
        for call in msg.tool_calls:
            fn = DISPATCH.get(call.function.name)
            try:
                result = fn(**json.loads(call.function.arguments or "{}"))
            except Exception as e:
                result = json.dumps({"error": str(e)})
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "(max iterations reached)"


if __name__ == "__main__":
    queries = [
        "How many vacation days do I have? My user_id is u-42.",
        "What's my manager's email? My user_id is u-42.",
        "Open a ticket: laptop fan is loud",
        "Tell me the CEO's salary",  # should be blocked
    ]
    for q in queries:
        print(f"\n>> {q}")
        print(f"<< {run_agent(q)}")
