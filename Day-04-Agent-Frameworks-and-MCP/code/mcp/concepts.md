# MCP — Model Context Protocol

MCP is a standardized protocol that lets AI applications discover and call
tools, fetch resources, and load prompts from external servers.

## Why MCP?

Without MCP, every framework (LangChain, LangGraph, CrewAI) builds its
own tool-calling convention. MCP gives you ONE protocol so any agent can
talk to any tool server.

## Architecture

```
AI Application
     |
   MCP Client  (e.g. Claude Desktop, an IDE plugin, your agent)
     |
   MCP Server  (wraps one backend: Jira, GitHub, a database, ...)
     |
  Tools / Resources / Prompts
```

## Components

### MCP Client
Lives inside your AI app. Connects to one or more MCP servers.

### MCP Server
Exposes a set of capabilities. Each server wraps one backend (e.g. `jira-mcp`).

### Tools
Actions the agent can execute. Declared with name + JSON-schema parameters.

### Resources
Read-only context the client can fetch (files, database rows, ...).

### Prompts
Reusable prompt templates the server can return to the client.

## Two Transports

| Transport | Use case |
|-----------|----------|
| **stdio** | Local development; server runs as a child process |
| **Streamable HTTP** | Production; server runs as a long-lived HTTP endpoint |

## JSON-RPC Methods

| Method | Direction | Purpose |
|--------|-----------|---------|
| `initialize` | client → server | Handshake |
| `tools/list` | client → server | List available tools |
| `tools/call` | client → server | Invoke a tool |
| `resources/list` | client → server | List resources |
| `resources/read` | client → server | Read a resource |
| `prompts/list` | client → server | List prompt templates |

## MCP in the bigger picture

```text
LangGraph (agent orchestration)
        ↓
    MCP client
        ↓
    MCP server  ─── tools you don't need to re-implement per framework
```

## Quick start with the official SDK

```bash
pip install mcp
# Run an example server:
mcp run examples/snippets/resources.py
```

Reference: https://modelcontextprotocol.io
