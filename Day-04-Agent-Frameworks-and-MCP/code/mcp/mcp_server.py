"""
Day 4 — Minimal MCP-style server (educational).

Real MCP uses JSON-RPC over stdio or Streamable HTTP. This script shows
the *shape* of an MCP server: tools are declared, tools are called by name,
results are returned.

For a real implementation, see the `mcp` Python SDK and `mcp run`.

Conceptual flow:
    client  --list tools-->  server
    client  --call tool X-->  server  -->  returns result
"""
import json
from typing import Callable


class MCPServer:
    def __init__(self, name: str):
        self.name = name
        self.tools: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable, description: str = ""):
        self.tools[name] = {"fn": fn, "description": description}

    def list_tools(self) -> list[dict]:
        return [{"name": n, "description": meta["description"]}
                for n, meta in self.tools.items()]

    def call(self, name: str, args: dict) -> dict:
        meta = self.tools.get(name)
        if not meta:
            return {"error": f"unknown tool: {name}"}
        try:
            return {"result": meta["fn"](**args)}
        except Exception as e:
            return {"error": str(e)}


# --- Build a toy docs server ---
docs_server = MCPServer("docs-mcp")
docs_server.register(
    "search_docs",
    lambda query: {
        "results": [
            {"title": "VPN Troubleshooting Guide",
             "text": "Restart the VPN client and reconnect."},
            {"title": "Password Reset Policy",
             "text": "Use the self-service portal."},
        ]
    },
    description="Search the IT knowledge base."
)


if __name__ == "__main__":
    print(f"Server: {docs_server.name}")
    print("Tools:", json.dumps(docs_server.list_tools(), indent=2))

    # Simulate a client call (in real MCP, this is JSON-RPC over stdio/HTTP)
    request = {"method": "tools/call", "name": "search_docs", "args": {"query": "VPN"}}
    print(f"\nRequest: {request}")
    response = docs_server.call(request["name"], request["args"])
    print(f"Response: {json.dumps(response, indent=2)}")
