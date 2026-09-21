# Day 2 — Hands-on · Build a Tool-Calling Agent

> 15-minute build session. Work in pairs.

## Goal

Build a minimal tool-calling agent from scratch. No frameworks. Just
the OpenAI SDK and a loop.

## Steps

### 1. Configure the LLM

```bash
pip install openai
export OPENAI_API_KEY="sk-..."
```

### 2. Pick a tool

Start with **one** tool. `search_docs(query: str) → str`. Mock it:

```python
def search_docs(query: str) -> str:
    return json.dumps({
        "results": [
            {"title": "VPN Troubleshooting",
             "text": "Restart the VPN client. Reconnect."},
            {"title": "Password Reset",
             "text": "Use password.company.com."}
        ]
    })
```

### 3. Declare the tool to the LLM

```python
TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_docs",
        "description": "Search the IT knowledge base.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
}]
```

### 4. Write the loop

```python
def run(user_message: str):
    messages = [
        {"role": "system", "content": "You are an IT support agent."},
        {"role": "user", "content": user_message},
    ]
    while True:
        resp = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=TOOLS
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content
        messages.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            result = search_docs(**args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
```

### 5. Test it

```bash
python tool_calling.py
```

You should see:

```
>> What does the VPN troubleshooting guide say?
[tool call] search_docs({'query': 'VPN troubleshooting'})
<< Restart the VPN client. Reconnect.
```

## Stretch Goals

- Add a second tool (`get_ticket_status`).
- Add a HITL gate: when the agent tries to call `create_ticket`, return
  `{"status": "pending_approval"}` instead of executing.
- Add a max-iteration cap (e.g. 5).
- Log every tool call.

## What You Now Have

- A working tool-calling loop, 30 lines.
- The foundation for everything else this week: RAG, MCP, multi-agent.
