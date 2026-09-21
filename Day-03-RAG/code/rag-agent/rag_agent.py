"""
Day 3 — RAG exposed as an agent tool.

The agent (an LLM with tool-calling) decides when to call search_docs,
the tool retrieves from a vector store, and the result is fed back.

This file is the bridge between RAG (Day 3) and Agents (Day 2).

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run rag_agent.py
"""
import json
import sys
from pathlib import Path

# Allow `from llm_config import ...` regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_client, get_model

client = get_client()
MODEL = get_model()

SYSTEM = """You are an IT support agent with access to a policy knowledge base.
Always cite the source of any policy claim."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search the IT/HR policy knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        }
    }
]


def search_docs(query: str) -> str:
    """Mock RAG retriever — returns canned chunks + citations."""
    return json.dumps({
        "results": [
            {
                "text": "Full-time employees receive 25 vacation days per year.",
                "source": "hr-handbook.pdf#v3.2#section-4.1"
            },
            {
                "text": "Unused days roll over up to a maximum of 5 days.",
                "source": "hr-handbook.pdf#v3.2#section-4.1"
            }
        ]
    })


def run(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_message},
    ]
    while True:
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

        messages.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            result = search_docs(**args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})


if __name__ == "__main__":
    print(">> How many vacation days do I get?")
    print(f"<< {run('How many vacation days do I get?')}")
