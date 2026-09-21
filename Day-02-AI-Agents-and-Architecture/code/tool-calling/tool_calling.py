"""
Day 2 — Minimal tool calling (single tool).

Demonstrates:
- Defining one tool for the LLM (search_docs)
- Letting the LLM decide whether to call it
- Feeding the tool result back to get a final answer

Setup:
    uv sync
    cp .env.example .env    # then edit .env (bifrost vars are pre-filled)
Run:
    uv run tool_calling.py
"""
import json
import sys
from pathlib import Path

# Allow `from llm_config import ...` regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_client, get_model

client = get_client()
MODEL = get_model()

SYSTEM = "You are an IT support agent. Use search_docs when you need policy information."

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search the IT knowledge base for relevant articles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        },
    }
]


def search_docs(query: str) -> str:
    """Mock implementation. Replace with real search in production."""
    return json.dumps({
        "results": [
            {"title": "VPN Troubleshooting Guide",
             "snippet": "Restart the VPN client. If the issue persists, reconnect."},
            {"title": "Password Reset Policy",
             "snippet": "Use the self-service portal at password.company.com."},
        ]
    })


def run(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_message},
    ]
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, tools=TOOLS
    )
    msg = resp.choices[0].message

    # Did the LLM want to call a tool?
    if msg.tool_calls:
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            print(f"[tool call] search_docs({args})")
            result = search_docs(**args)
            messages.append(msg)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        # Second pass: LLM now has the tool result
        final = client.chat.completions.create(
            model=MODEL, messages=messages
        )
        return final.choices[0].message.content or ""
    return msg.content or ""


if __name__ == "__main__":
    print(">> What does the VPN troubleshooting guide say?")
    print(f"<< {run('What does the VPN troubleshooting guide say?')}")
    print("\n>> Hello")
    print(f"<< {run('Hello')}")
