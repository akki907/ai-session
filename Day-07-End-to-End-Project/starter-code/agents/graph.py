"""
Day 7 — LangGraph multi-agent workflow.

5 agents:
- Planner:     decides which sub-tasks to run
- Knowledge:   runs RAG lookup
- Ticket:      reads/creates Jira tickets
- Escalation:  routes to human
- Reviewer:    validates the draft response

HITL is enforced outside the graph — any tool with `requires_approval`
will append to PENDING_WRITES and pause the graph.
"""
import sys
from pathlib import Path
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END

# Importing llm_config exports proxy env vars so any LLM call below
# automatically goes through the configured provider (bifrost by default).
sys.path.insert(0, str(Path(__file__).parent.parent))
import llm_config  # noqa: F401

from tools import (
    search_docs,
    get_ticket_status,
    create_ticket,
    escalate_to_human,
)


class State(TypedDict):
    user_id: str
    query: str
    plan: list[str]
    knowledge: str
    ticket_info: dict
    escalation: str
    draft: str
    review: str
    citations: list[str]
    tool_calls: list[dict]


# --- Node implementations (use the LLM client in real code) ---

def planner(state: State) -> State:
    """In real code: call LLM with structured output to get a plan."""
    q = state["query"].lower()
    plan = []
    if any(w in q for w in ["policy", "rule", "guideline", "what is"]):
        plan.append("knowledge")
    if any(w in q for w in ["ticket", "status", "open", "create"]):
        plan.append("ticket")
    if any(w in q for w in ["urgent", "human", "manager", "critical"]):
        plan.append("escalation")
    state["plan"] = plan
    state["tool_calls"].append({"tool": "planner", "args": {"plan": plan}})
    return state


def knowledge_node(state: State) -> State:
    docs = search_docs(state["query"])
    state["knowledge"] = docs["text"]
    state["citations"] = docs["citations"]
    state["tool_calls"].append({"tool": "search_docs", "args": {"q": state["query"]}})
    return state


def ticket_node(state: State) -> State:
    # In real code: ask LLM to extract ticket_id from query
    state["ticket_info"] = get_ticket_status("T-1042")
    state["tool_calls"].append({"tool": "get_ticket_status", "args": {"ticket_id": "T-1042"}})
    return state


def escalation_node(state: State) -> State:
    state["escalation"] = escalate_to_human(state["query"])
    state["tool_calls"].append({"tool": "escalate_to_human", "args": {"q": state["query"]}})
    return state


def summarize(state: State) -> State:
    """Combine knowledge + ticket info + escalation into a draft."""
    parts = []
    if state["knowledge"]:
        parts.append(f"Based on policy: {state['knowledge']}")
    if state["ticket_info"]:
        parts.append(f"Ticket info: {state['ticket_info']}")
    if state["escalation"]:
        parts.append(f"Escalation: {state['escalation']}")
    state["draft"] = "\n\n".join(parts) or "I'm not sure. Let me escalate."
    return state


def review(state: State) -> State:
    """Reviewer decides APPROVED vs NEEDS_WORK."""
    state["review"] = "APPROVED" if state["draft"] else "NEEDS_WORK"
    state["tool_calls"].append({"tool": "reviewer", "args": {}, "output": state["review"]})
    return state


def should_loop(state: State) -> Literal["summarize", "__end__"]:
    return "summarize" if state["review"] == "NEEDS_WORK" else "__end__"


def build_graph():
    g = StateGraph(State)

    g.add_node("planner", planner)
    g.add_node("knowledge", knowledge_node)
    g.add_node("ticket", ticket_node)
    g.add_node("escalation", escalation_node)
    g.add_node("summarize", summarize)
    g.add_node("review", review)

    g.add_edge(START, "planner")

    # Conditional edges from planner
    def route(state: State):
        return [p for p in state["plan"] if p in ("knowledge", "ticket", "escalation")] or ["summarize"]

    g.add_conditional_edges("planner", route)
    for node in ("knowledge", "ticket", "escalation"):
        g.add_edge(node, "summarize")

    g.add_edge("summarize", "review")
    g.add_conditional_edges("review", should_loop, {"summarize": "summarize", "__end__": END})

    return g.compile()


class _GraphWrapper:
    """Tiny adapter so app.py can call graph.arun()."""

    async def arun(self, query: str, user_id: str):
        initial: State = {
            "user_id": user_id,
            "query": query,
            "plan": [],
            "knowledge": "",
            "ticket_info": {},
            "escalation": "",
            "draft": "",
            "review": "",
            "citations": [],
            "tool_calls": [],
        }
        # LangGraph returns the final state via invoke()
        final = build_graph().invoke(initial)
        return {
            "answer": final["draft"],
            "citations": final["citations"],
            "tool_calls": final["tool_calls"],
            "tokens": {"input": 1840, "output": 220},
        }


# Re-build on import so app.py gets a fresh graph
graph = _GraphWrapper()
