"""
Day 5 — Load an agent YAML spec and build a LangGraph workflow from it.

Setup:
    pip install pyyaml langgraph langchain-openai
Run:
    python day5_modify_agent.py
"""
import yaml
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from typing import TypedDict


class S(TypedDict):
    input: str
    output: str
    trace: list[str]


def load_spec(name: str) -> dict:
    path = Path(__file__).parent.parent / "architecture" / "specs" / f"{name}.yaml"
    return yaml.safe_load(path.read_text())


def make_node(tool_name: str):
    """Build a LangGraph node that simulates a tool call."""
    def node(s: S) -> S:
        s["trace"].append(f"called: {tool_name}({s['input']!r})")
        s["output"] = f"[{tool_name}] processed: {s['input']}"
        return s
    return node


def build_graph(spec: dict) -> StateGraph:
    g = StateGraph(S)
    tools = [t["name"] for t in spec["tools"]]
    print(f"Loaded agent v{spec['version']} with tools: {tools}")

    g.add_node("__start__", lambda s: s)
    for t in tools:
        g.add_node(t, make_node(t))
    g.add_node("__final__", lambda s: s)

    g.add_edge(START, "__start__")
    for t in tools:
        g.add_edge("__start__", t)
    for t in tools:
        g.add_edge(t, "__final__")
    g.add_edge("__final__", END)

    return g


if __name__ == "__main__":
    spec = load_spec("it-support-agent")
    graph = build_graph(spec).compile()

    result = graph.invoke({
        "input": "Notify #it-help that T-1042 is OPEN",
        "output": "",
        "trace": [],
    })

    print("\n=== TRACE ===")
    for step in result["trace"]:
        print(f"  {step}")
    print(f"\n=== OUTPUT ===\n{result['output']}")
